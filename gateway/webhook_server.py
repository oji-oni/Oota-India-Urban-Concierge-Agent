# ─────────────────────────────────────────────────────────────────────────────
# gateway/webhook_server.py
# Oota India Urban Concierge — FastAPI Webhook & REST Server
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from telegram import Update

load_dotenv()

logger = logging.getLogger("oota.webhook")

SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./data/oota.db")
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Oota India Urban Concierge",
    description=(
        "Privacy-first India Urban Concierge AI Agent — "
        "REST & Telegram Webhook API"
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (permissive for local dev — tighten in production) ───────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Lazy-loaded Telegram Application singleton (webhook mode) ─────────────────
_tg_app = None


def _get_tg_app():
    """Return the cached Telegram Application, building it if needed."""
    global _tg_app
    if _tg_app is None and TELEGRAM_BOT_TOKEN:
        from gateway.telegram_bot import get_application

        _tg_app = get_application()
    return _tg_app


# ── DB helpers ────────────────────────────────────────────────────────────────
def _db_connected() -> bool:
    """Return True if the SQLite database file is accessible."""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False


def _list_supported_cities() -> list[str]:
    """Query the DB for all city slugs; fall back to hardcoded defaults."""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.execute("SELECT slug FROM cities ORDER BY name")
        rows = [row[0] for row in cursor.fetchall()]
        conn.close()
        if rows:
            return rows
    except Exception as exc:
        logger.debug("cities table query failed: %s", exc)

    # Hardcoded fallback
    return [
        "ahmedabad",
        "bengaluru",
        "chennai",
        "delhi",
        "hyderabad",
        "jaipur",
        "kolkata",
        "mumbai",
        "pune",
    ]


# ── Pydantic models ───────────────────────────────────────────────────────────
class AgentRequest(BaseModel):
    message: str = Field(..., description="User message to send to the agent")
    city: Optional[str] = Field(
        None, description="Active city slug (e.g. 'bengaluru')"
    )
    user_id: Optional[int] = Field(
        None, description="Caller user ID for session tracking"
    )


class AgentResponse(BaseModel):
    response: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    db_connected: bool


# ── Lifecycle events ──────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize the Telegram Application in webhook mode on startup."""
    tg_app = _get_tg_app()
    if tg_app is not None:
        await tg_app.initialize()
        await tg_app.start()
        logger.info("Telegram Application initialised in webhook mode.")
    else:
        logger.info("No TELEGRAM_BOT_TOKEN — running without Telegram integration.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Gracefully shut down the Telegram Application."""
    global _tg_app
    if _tg_app is not None:
        try:
            await _tg_app.stop()
            await _tg_app.shutdown()
            logger.info("Telegram Application shut down cleanly.")
        except Exception as exc:
            logger.warning("Error during Telegram shutdown: %s", exc)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.post("/webhook/{bot_token}", include_in_schema=False)
async def telegram_webhook(bot_token: str, request: Request) -> Response:
    """
    Telegram webhook endpoint.
    Telegram POSTs Update objects here when webhook mode is active.
    The {bot_token} path segment acts as a shared secret to reject spoofed calls.
    """
    if bot_token != TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid bot token")

    tg_app = _get_tg_app()
    if tg_app is None:
        raise HTTPException(status_code=503, detail="Telegram bot not configured")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    update = Update.de_json(body, tg_app.bot)
    await tg_app.process_update(update)
    return Response(status_code=200)


@app.post("/agent", response_model=AgentResponse, summary="Run a single agent turn")
async def agent_endpoint(req: AgentRequest) -> AgentResponse:
    """
    Run one agent turn synchronously.

    **Request body:**
    - `message` *(required)*: The user's natural-language message.
    - `city` *(optional)*: Active city slug (defaults to `DEFAULT_CITY` env var).
    - `user_id` *(optional)*: Numeric user ID for session isolation.

    **Returns:** `{response: str}` — the agent's text reply.
    """
    city = req.city or os.getenv("DEFAULT_CITY", "bengaluru")
    user_id = req.user_id or 0

    try:
        from oota_agent.runner import run_agent_turn

        response = await run_agent_turn(
            message=req.message, city=city, user_id=user_id
        )
        return AgentResponse(response=response)
    except ImportError:
        logger.warning(
            "oota_agent.runner not available — returning stub response"
        )
        return AgentResponse(
            response=f"[Stub] Echo: {req.message!r} (city={city})"
        )
    except Exception as exc:
        logger.exception("Agent runner failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health", response_model=HealthResponse, summary="Health check")
async def health() -> HealthResponse:
    """Returns service health status and database connectivity."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        db_connected=_db_connected(),
    )


@app.get(
    "/cities",
    response_model=list[str],
    summary="List supported cities",
)
async def cities() -> list[str]:
    """Returns all supported city slugs from the local SQLite database."""
    return _list_supported_cities()
