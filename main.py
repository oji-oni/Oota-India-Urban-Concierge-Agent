# ─────────────────────────────────────────────────────────────────────────────
# main.py
# Oota India Urban Concierge — Application Entry Point
# Handles DB seeding, MCP server launch, and mode selection
# (webhook / Telegram polling / terminal interactive)
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import asyncio
import logging
import os
import signal
import subprocess
import sys
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("oota.main")

# ── Global state for graceful shutdown ────────────────────────────────────────
_shutdown_event: asyncio.Event
_mcp_proc: Optional[subprocess.Popen] = None  # type: ignore[type-arg]


def _signal_handler(sig: int, frame: object) -> None:
    name = signal.Signals(sig).name if hasattr(signal, "Signals") else str(sig)
    logger.info("Received signal %s — initiating graceful shutdown...", name)
    try:
        _shutdown_event.set()
    except RuntimeError:
        # Event loop already closed; ignore
        pass


def _register_signal_handlers() -> None:
    """Register SIGINT / SIGTERM handlers (SIGTERM skipped on Windows)."""
    try:
        signal.signal(signal.SIGINT, _signal_handler)
    except (OSError, ValueError):
        pass
    try:
        signal.signal(signal.SIGTERM, _signal_handler)
    except (OSError, ValueError):
        pass  # SIGTERM not available on Windows


# ── DB seed ───────────────────────────────────────────────────────────────────
def _seed_db_if_needed(db_path: str) -> None:
    """Run data/seed_database.py if the SQLite DB does not exist yet."""
    if os.path.exists(db_path):
        logger.info("Database exists at %s — skipping seed.", db_path)
        return

    seed_script = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "seed_database.py"
    )
    if not os.path.exists(seed_script):
        logger.warning(
            "Seed script not found at %s — skipping DB seed. "
            "Run 'python data/seed_database.py' manually.",
            seed_script,
        )
        return

    logger.info("Database not found — running seed script: %s", seed_script)
    try:
        subprocess.run([sys.executable, seed_script], check=True)
        logger.info("Database seeded successfully.")
    except subprocess.CalledProcessError as exc:
        logger.error("Seed script failed (exit code %s). Continuing...", exc.returncode)


# ── MCP server ────────────────────────────────────────────────────────────────
def _start_mcp_server() -> Optional[subprocess.Popen]:  # type: ignore[type-arg]
    """Launch the FastMCP city data server as a background subprocess."""
    mcp_script = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "mcp_servers",
        "city_data_server.py",
    )
    if not os.path.exists(mcp_script):
        logger.warning(
            "MCP server script not found at %s — skipping.", mcp_script
        )
        return None

    logger.info("Starting FastMCP city data server: %s", mcp_script)
    proc = subprocess.Popen(
        [sys.executable, mcp_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    logger.info("FastMCP server started (PID=%s).", proc.pid)
    return proc


def _stop_mcp_server(proc: Optional[subprocess.Popen]) -> None:  # type: ignore[type-arg]
    """Terminate the MCP server subprocess gracefully."""
    if proc is None or proc.poll() is not None:
        return
    logger.info("Terminating FastMCP server (PID=%s)...", proc.pid)
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        logger.warning("FastMCP server did not stop; sending SIGKILL.")
        proc.kill()


# ── Run modes ─────────────────────────────────────────────────────────────────
async def _run_webhook_mode(telegram_token: str) -> None:
    """
    Start the FastAPI webhook server on $PORT (default 8000).
    Optionally also starts the Telegram long-poll bot if a token is set.
    Both tasks race against the shutdown event.
    """
    import uvicorn
    from gateway.webhook_server import app as fastapi_app

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    config = uvicorn.Config(
        fastapi_app,
        host=host,
        port=port,
        log_level="info",
        loop="asyncio",
    )
    server = uvicorn.Server(config)

    tasks: list[asyncio.Task] = [
        asyncio.create_task(server.serve(), name="uvicorn"),
    ]

    if telegram_token:
        from gateway.telegram_bot import run_telegram_bot

        tasks.append(
            asyncio.create_task(run_telegram_bot(), name="telegram-polling")
        )

    shutdown_task = asyncio.create_task(
        _shutdown_event.wait(), name="shutdown-watcher"
    )

    done, pending = await asyncio.wait(
        [*tasks, shutdown_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    if shutdown_task in done:
        logger.info("Shutdown event — stopping running tasks...")
        server.should_exit = True

    for task in pending:
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass


async def _run_polling_mode() -> None:
    """Run the Telegram bot in long-polling mode."""
    from gateway.telegram_bot import run_telegram_bot

    bot_task = asyncio.create_task(run_telegram_bot(), name="telegram-polling")
    shutdown_task = asyncio.create_task(
        _shutdown_event.wait(), name="shutdown-watcher"
    )

    done, pending = await asyncio.wait(
        [bot_task, shutdown_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass


async def _run_terminal_mode() -> None:
    """
    Fall back to ADK interactive terminal when no Telegram token is configured.
    """
    try:
        from google.adk.cli import run_interactive  # type: ignore[import]
        from oota_agent.agent import root_agent  # type: ignore[import]

        logger.info("Starting ADK interactive terminal mode...")
        await run_interactive(root_agent)
    except ImportError as exc:
        logger.error(
            "Cannot start terminal mode — missing modules: %s\n"
            "Tip: Set TELEGRAM_BOT_TOKEN in .env to use the Telegram bot instead.",
            exc,
        )
        print(
            "\n[Oota] Terminal mode requires oota_agent and google-adk.\n"
            "Set TELEGRAM_BOT_TOKEN in .env to use the Telegram bot instead.\n",
            file=sys.stderr,
        )
        sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────
async def main() -> None:
    global _shutdown_event, _mcp_proc

    _shutdown_event = asyncio.Event()
    _register_signal_handlers()

    # ── 1. Ensure database is seeded ─────────────────────────────────────────
    db_path = os.getenv("SQLITE_DB_PATH", "./data/oota.db")
    _seed_db_if_needed(db_path)

    # ── 2. Start FastMCP server subprocess ────────────────────────────────────
    _mcp_proc = _start_mcp_server()

    # ── 3. Select run mode ────────────────────────────────────────────────────
    webhook_mode = os.getenv("WEBHOOK_MODE", "false").lower() == "true"
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    try:
        if webhook_mode:
            logger.info("Mode: WEBHOOK  (FastAPI on port %s)", os.getenv("PORT", "8000"))
            await _run_webhook_mode(telegram_token)
        elif telegram_token:
            logger.info("Mode: TELEGRAM POLLING")
            await _run_polling_mode()
        else:
            logger.info("Mode: TERMINAL INTERACTIVE")
            await _run_terminal_mode()
    finally:
        _stop_mcp_server(_mcp_proc)
        logger.info("Oota shut down cleanly. Goodbye! 🍛")


if __name__ == "__main__":
    asyncio.run(main())
