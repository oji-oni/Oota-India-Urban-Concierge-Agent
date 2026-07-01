# ─────────────────────────────────────────────────────────────────────────────
# gateway/telegram_bot.py
# Oota India Urban Concierge — Telegram Bot Gateway
# Full async bot using python-telegram-bot v20+
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    JobQueue,
    MessageHandler,
    filters,
)

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("oota.telegram")

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
_raw_ids = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS: set[int] = (
    {int(uid.strip()) for uid in _raw_ids.split(",") if uid.strip()}
    if _raw_ids.strip()
    else set()  # empty set = allow all (dev mode)
)
SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./data/oota.db")
DEFAULT_CITY: str = os.getenv("DEFAULT_CITY", "bengaluru")

# ConversationHandler states
AWAITING_CITY = 1

# ── Welcome / Help text ───────────────────────────────────────────────────────
WELCOME_TEXT = """
🍛 *Welcome to Oota India Urban Concierge!*

Your privacy-first AI assistant for navigating Indian cities.

*What I can do:*
• 🗺️ Recommend restaurants, cafes & street food
• 🚇 Plan metro / BMTC / auto routes
• 💸 Split bills & track shared expenses
• 📅 Manage your itinerary & send reminders
• 🛒 Build shopping lists with local market tips
• 🌦️ Weather-aware outing suggestions
• 🔍 Neighbourhood deep-dives
• 🗣️ Kannada / Hindi / Tamil phrasebook
• 📦 Export your data anytime

*Quick commands:* /help
*Current city:* Use /switch\\_city to change

Just type anything — I'm listening! 🙂
"""

HELP_TEXT = """
*Oota Bot — Command Reference*

/start — Welcome message & feature overview
/help — This command reference
/switch\\_city \\[city\\] — Change active city \\(e\\.g\\. /switch\\_city mumbai\\)
/split \\[amount\\] at \\[venue\\] for \\[names\\] — Split a bill
/balances — Show outstanding expense balances
/export — Export all local data as ZIP backup
/status — System & itinerary status summary

*Supported cities:* bengaluru · mumbai · delhi · chennai
  hyderabad · kolkata · pune · ahmedabad · jaipur

*Tip:* Just type naturally — e\\.g\\. "Find a quiet café near Indiranagar with good WiFi"
"""

# ── Auth middleware helper ────────────────────────────────────────────────────
def _is_authorised(user_id: int) -> bool:
    """Return True if user is in the allow-list, or if list is empty (dev mode)."""
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS


async def _auth_gate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check auth and reply with rejection if not allowed. Returns True if OK."""
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_authorised(uid):
        await update.effective_message.reply_text(
            "🚫 Unauthorized. Contact the bot administrator to get access."
        )
        logger.warning("Unauthorized access attempt by user_id=%s", uid)
        return False
    return True


# ── ADK runner helper ─────────────────────────────────────────────────────────
async def _run_agent(message: str, city: str, user_id: int) -> str:
    """
    Forward a message to the Oota ADK agent and return its text response.
    Falls back to an error string on failure.
    """
    try:
        from oota_agent.runner import run_agent_turn  # lazy import

        response = await run_agent_turn(message=message, city=city, user_id=user_id)
        return response
    except ImportError:
        logger.error("oota_agent.runner not available — running in stub mode")
        return f"[Agent stub] Received: {message!r} for city={city}"
    except Exception as exc:
        logger.exception("Agent runner error: %s", exc)
        return f"⚠️ Agent encountered an error: {exc}"


def _get_user_city(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Read city from user_data, fallback to DEFAULT_CITY."""
    return context.user_data.get("city", DEFAULT_CITY)  # type: ignore[return-value]


# ── Command handlers ──────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _auth_gate(update, context):
        return
    await update.message.reply_text(WELCOME_TEXT, parse_mode=ParseMode.MARKDOWN)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _auth_gate(update, context):
        return
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _auth_gate(update, context):
        return
    city = _get_user_city(context)
    uid = update.effective_user.id
    response = await _run_agent("Show system status and today's itinerary summary", city, uid)
    await update.message.reply_text(response)


async def cmd_balances(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _auth_gate(update, context):
        return
    city = _get_user_city(context)
    uid = update.effective_user.id
    response = await _run_agent("Show current expense balances for all group members", city, uid)
    await update.message.reply_text(response)


async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _auth_gate(update, context):
        return
    uid = update.effective_user.id
    await update.message.reply_text("📦 Preparing your data export...")
    response = await _run_agent("export_local_backup", _get_user_city(context), uid)
    await update.message.reply_text(response)


async def cmd_split(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/split [amount] at [venue] for [names]"""
    if not await _auth_gate(update, context):
        return
    city = _get_user_city(context)
    uid = update.effective_user.id
    raw = " ".join(context.args or [])
    if not raw:
        await update.message.reply_text(
            "Usage: /split 1200 at MTR for Alice, Bob, Charlie"
        )
        return
    instruction = f"Split bill: {raw}"
    response = await _run_agent(instruction, city, uid)
    await update.message.reply_text(response)


# ── City switch ConversationHandler ──────────────────────────────────────────
async def cmd_switch_city_entry(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """/switch_city entry point. Inline switch if arg provided; else ask."""
    if not await _auth_gate(update, context):
        return ConversationHandler.END

    args = context.args or []
    if args:
        city_slug = args[0].lower().strip()
        return await _apply_city_switch(update, context, city_slug)

    await update.message.reply_text(
        "🏙️ Which city would you like to switch to?\n"
        "Supported: bengaluru · mumbai · delhi · chennai · hyderabad · "
        "kolkata · pune · ahmedabad · jaipur\n\n"
        "Type /cancel to abort."
    )
    return AWAITING_CITY


async def received_city_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    city_slug = update.message.text.strip().lower()
    return await _apply_city_switch(update, context, city_slug)


async def _apply_city_switch(
    update: Update, context: ContextTypes.DEFAULT_TYPE, city_slug: str
) -> int:
    context.user_data["city"] = city_slug  # type: ignore[index]
    uid = update.effective_user.id
    response = await _run_agent(f"Switch active city to {city_slug}", city_slug, uid)
    await update.message.reply_text(
        f"✅ Active city set to *{city_slug.title()}*.\n\n{response}",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ConversationHandler.END


async def cancel_conversation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


# ── Generic message handler ───────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _auth_gate(update, context):
        return
    city = _get_user_city(context)
    uid = update.effective_user.id
    text = update.message.text or ""
    if not text.strip():
        return

    # Handle 'Running late' responses for proactive departure warnings
    lower = text.strip().lower()
    pending_venue: Optional[str] = context.user_data.get("pending_late_venue")  # type: ignore[assignment]
    if lower == "running late" and pending_venue:
        context.user_data.pop("pending_late_venue", None)  # type: ignore[call-overload]
        response = await _run_agent(
            f"User is running late for {pending_venue}. "
            f"Suggest the best alternative nearby venue in {city}.",
            city,
            uid,
        )
        await update.message.reply_text(f"🔄 Alternative suggestions:\n\n{response}")
        return

    if lower == "yes" and context.user_data.get("pending_late_venue"):
        context.user_data.pop("pending_late_venue", None)  # type: ignore[call-overload]
        await update.message.reply_text("🙌 Great! Have a wonderful time!")
        return

    # Normal agent turn
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )
    response = await _run_agent(text, city, uid)
    await update.message.reply_text(response)


# ── Inline keyboard callback (star ratings) ───────────────────────────────────
async def feedback_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data.startswith("rate:"):
        parts = data.split(":", 2)
        if len(parts) == 3:
            _, venue, stars = parts
            uid = update.effective_user.id
            city = _get_user_city(context)
            await _run_agent(
                f"Record feedback: {stars} stars for venue {venue} from user {uid}",
                city,
                uid,
            )
            await query.edit_message_text(
                f"⭐ Thanks! Rated *{venue}* {stars}/5.",
                parse_mode=ParseMode.MARKDOWN,
            )


# ── Proactive scheduler jobs ──────────────────────────────────────────────────
def _get_db_connection() -> Optional[sqlite3.Connection]:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as exc:
        logger.warning("Cannot open DB for scheduler: %s", exc)
        return None


async def job_departure_warnings(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Runs every 5 minutes.
    Checks active_itineraries for events departing within the next 30 minutes.
    Sends a proactive departure warning to the itinerary owner.
    """
    conn = _get_db_connection()
    if conn is None:
        return

    try:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        window_end = now_ts + 30 * 60  # 30 minutes ahead

        cursor = conn.execute(
            """
            SELECT ai.user_id, ai.venue_name, ai.departure_time, ai.itinerary_id
            FROM active_itineraries ai
            WHERE ai.departure_time BETWEEN ? AND ?
              AND ai.departure_warned = 0
            """,
            (now_ts, window_end),
        )
        rows = cursor.fetchall()
    except sqlite3.OperationalError as exc:
        logger.debug("active_itineraries table may not exist yet: %s", exc)
        rows = []
    finally:
        conn.close()

    for row in rows:
        user_id: int = row["user_id"]
        venue_name: str = row["venue_name"]
        itinerary_id: int = row["itinerary_id"]

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"🚀 *Leaving for {venue_name} soon!*\n"
                    "Still on track?\n\nReply *Yes* or *Running late*"
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
            # Store pending venue in user context (accessed in handle_message via bot_data)
            if context.bot_data is not None:
                context.bot_data.setdefault("pending_late_venues", {})[user_id] = venue_name

            # Mark as warned in DB
            upd_conn = _get_db_connection()
            if upd_conn:
                try:
                    upd_conn.execute(
                        "UPDATE active_itineraries SET departure_warned = 1 "
                        "WHERE itinerary_id = ?",
                        (itinerary_id,),
                    )
                    upd_conn.commit()
                finally:
                    upd_conn.close()
        except Exception as exc:
            logger.warning(
                "Could not send departure warning to user %s: %s", user_id, exc
            )


async def job_feedback_requests(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Runs every 5 minutes.
    Checks itineraries where meeting_time + 1 hour has passed,
    sends a 5-star inline keyboard feedback request.
    """
    conn = _get_db_connection()
    if conn is None:
        return

    try:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        one_hour = 3600

        cursor = conn.execute(
            """
            SELECT ai.user_id, ai.venue_name, ai.meeting_time, ai.itinerary_id
            FROM active_itineraries ai
            WHERE ai.meeting_time IS NOT NULL
              AND (ai.meeting_time + ?) <= ?
              AND ai.feedback_requested = 0
            """,
            (one_hour, now_ts),
        )
        rows = cursor.fetchall()
    except sqlite3.OperationalError as exc:
        logger.debug("active_itineraries feedback query failed: %s", exc)
        rows = []
    finally:
        conn.close()

    for row in rows:
        user_id: int = row["user_id"]
        venue_name: str = row["venue_name"]
        itinerary_id: int = row["itinerary_id"]

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"{i}⭐", callback_data=f"rate:{venue_name}:{i}"
                    )
                    for i in range(1, 6)
                ]
            ]
        )
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🌟 How was *{venue_name}*? Rate your experience:",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN,
            )
            upd_conn = _get_db_connection()
            if upd_conn:
                try:
                    upd_conn.execute(
                        "UPDATE active_itineraries SET feedback_requested = 1 "
                        "WHERE itinerary_id = ?",
                        (itinerary_id,),
                    )
                    upd_conn.commit()
                finally:
                    upd_conn.close()
        except Exception as exc:
            logger.warning(
                "Could not send feedback request to user %s: %s", user_id, exc
            )


async def job_autonomous_checkin(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Runs periodically.
    Queries all active user IDs and asks the root ADK agent to perform
    a status check, invoking its tools and generating a check-in question.
    """
    conn = _get_db_connection()
    if conn is None:
        return

    try:
        # Find all distinct user IDs in the database
        cursor = conn.execute(
            """
            SELECT DISTINCT user_id FROM user_budgets
            UNION
            SELECT DISTINCT user_id FROM active_itineraries
            """
        )
        user_rows = cursor.fetchall()
    except sqlite3.OperationalError as exc:
        logger.debug("Database check for autonomous users failed: %s", exc)
        user_rows = []
    finally:
        conn.close()

    for row in user_rows:
        user_id_str: str = row["user_id"]
        # Convert string ID to int for Telegram chat_id
        try:
            chat_id = int(user_id_str)
        except ValueError:
            # Skip non-numeric test users or placeholder IDs
            continue

        # Get city context for this user
        city = DEFAULT_CITY
        conn = _get_db_connection()
        if conn:
            try:
                city_row = conn.execute(
                    "SELECT c.slug FROM active_itineraries ai "
                    "JOIN cities c ON ai.city_id = c.id "
                    "WHERE ai.user_id = ? "
                    "ORDER BY ai.itinerary_id DESC LIMIT 1",
                    (user_id_str,)
                ).fetchone()
                if city_row:
                    city = city_row["slug"]
            except Exception:
                pass
            finally:
                conn.close()

        logger.info("Running autonomous status check for user_id=%s in city=%s", chat_id, city)
        try:
            # Prompt the agent to perform an audit and generate a check-in question
            prompt = (
                "System: Run a proactive check-in audit. Access my active itineraries, weather forecast, "
                "and budget limits. Identify any upcoming events, potential rain/weather alerts, or budget "
                "limit warnings. Then, formulate a friendly, conversational question to check in with me. "
                "If everything is normal, ask a friendly concierge tip/question about today's plans in the city."
            )
            response = await _run_agent(prompt, city, chat_id)
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=response,
            )
        except Exception as exc:
            logger.warning(
                "Could not send autonomous check-in to user %s: %s", chat_id, exc
            )


# ── Error handler ─────────────────────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "😓 Something went wrong on my end. Please try again in a moment."
        )


# ── Proactive scheduler helper ────────────────────────────────────────────────
def _schedule_jobs(app: Application) -> None:
    """Schedule repeating proactive background jobs on the application's JobQueue."""
    job_queue: JobQueue = app.job_queue  # type: ignore[assignment]
    if job_queue is not None:
        # Check if they are already scheduled to prevent duplicates
        existing = {job.callback.__name__ for job in job_queue.jobs()}
        if "job_departure_warnings" not in existing:
            job_queue.run_repeating(job_departure_warnings, interval=300, first=10)
        if "job_feedback_requests" not in existing:
            job_queue.run_repeating(job_feedback_requests, interval=300, first=30)
        if "job_autonomous_checkin" not in existing:
            job_queue.run_repeating(job_autonomous_checkin, interval=600, first=45)


# ── Application factory (for webhook mode) ────────────────────────────────────
def get_application() -> Application:
    """
    Return a fully-configured Application instance for use by the webhook server.
    Omits the Updater so the webhook server controls incoming updates.
    """
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set.")

    app: Application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .updater(None)  # No updater — webhook server handles updates
        .build()
    )

    _register_handlers(app)
    _schedule_jobs(app)
    return app


def _register_handlers(app: Application) -> None:
    """Attach all handlers and error handler to the given Application."""
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("balances", cmd_balances))
    app.add_handler(CommandHandler("export", cmd_export))
    app.add_handler(CommandHandler("split", cmd_split))

    city_conv = ConversationHandler(
        entry_points=[CommandHandler("switch_city", cmd_switch_city_entry)],
        states={
            AWAITING_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_city_name)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        allow_reentry=True,
    )
    app.add_handler(city_conv)
    app.add_handler(CallbackQueryHandler(feedback_callback, pattern=r"^rate:"))
    # Generic handler must be last
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)


# ── Entry point (long-polling mode) ──────────────────────────────────────────
async def run_telegram_bot() -> None:
    """
    Build and start the Telegram bot in long-polling mode.
    For production/webhook mode use webhook_server.py + get_application().
    """
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set.")

    app: Application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    _register_handlers(app)

    # Schedule proactive jobs
    _schedule_jobs(app)

    logger.info("Starting Oota Telegram bot (long-polling mode)...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    # Keep running until cancelled
    try:
        await asyncio.Event().wait()
    finally:
        logger.info("Stopping Oota Telegram bot...")
        if app.updater.running:
            await app.updater.stop()
        await app.stop()
        await app.shutdown()
