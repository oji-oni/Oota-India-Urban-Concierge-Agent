# ─────────────────────────────────────────────────────────────────────────────
# gateway/webhook_server.py
# Oota India Urban Concierge — FastAPI Webhook & REST Server
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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


# ── Dashboard API Endpoints ───────────────────────────────────────────────────

CHROMA_DATA_DIR = os.getenv("CHROMA_DATA_DIR", "./data/chroma")
DEFAULT_CITY: str = os.getenv("DEFAULT_CITY", "bengaluru")
_raw_allowed = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "")
WEBHOOK_MODE: bool = os.getenv("WEBHOOK_MODE", "false").lower() == "true"


def _db_query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a read query and return rows as dicts."""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.debug("DB query failed: %s", exc)
        return []


@app.get("/api/dashboard/status", summary="Dashboard: System status")
async def dashboard_status():
    """Returns comprehensive system status for the dashboard."""
    db_ok = _db_connected()
    chroma_ok = Path(CHROMA_DATA_DIR).exists()
    cities = _db_query("SELECT COUNT(*) as cnt FROM cities")
    pois = _db_query("SELECT COUNT(*) as cnt FROM points_of_interest")

    return {
        "status": "ok" if db_ok else "error",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "db_connected": db_ok,
        "chroma_connected": chroma_ok,
        "telegram_configured": bool(TELEGRAM_BOT_TOKEN),
        "cities_count": cities[0]["cnt"] if cities else 0,
        "pois_count": pois[0]["cnt"] if pois else 0,
    }


@app.get("/api/dashboard/agents", summary="Dashboard: Agent hierarchy")
async def dashboard_agents():
    """Returns the agent tree structure."""
    return {
        "root": {
            "name": "oota_concierge",
            "description": "Root supervisor — routes to specialized sub-agents",
            "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            "tools": ["execute_hybrid_routing"],
        },
        "sub_agents": [
            {
                "name": "travel_planner",
                "description": "Plans itineraries, checks weather, calculates transit times & fares",
                "tools": ["city_mcp", "calculate_departure_time", "check_weather_recommendation",
                           "generate_dating_plan", "collect_post_event_feedback", "execute_travel_workflow"],
            },
            {
                "name": "expense_tracker",
                "description": "Tracks shared group expenses, calculates balances & budget guards",
                "tools": ["city_mcp"],
            },
            {
                "name": "curation_agent",
                "description": "Manages preference memory, local RAG indexing & vault encryption",
                "tools": ["chroma_mcp", "save_preference", "recall_preferences",
                           "manage_vault_encryption", "run_document_indexer"],
            },
        ],
    }


@app.get("/api/dashboard/tools", summary="Dashboard: Available tools")
async def dashboard_tools():
    """Returns all MCP and custom tools available to the agent."""
    mcp_tools = [
        {"name": "list_supported_cities", "source": "mcp", "description": "List all supported cities"},
        {"name": "get_area_info", "source": "mcp", "description": "Get neighborhood info and vibe"},
        {"name": "search_points_of_interest", "source": "mcp", "description": "Search restaurants, cafes, temples, parks"},
        {"name": "get_poi_details", "source": "mcp", "description": "Full details of a specific POI"},
        {"name": "find_midpoint_pois", "source": "mcp", "description": "Find POIs near midpoint of two areas"},
        {"name": "calculate_group_midpoint", "source": "mcp", "description": "Geographic centroid for 3+ areas"},
        {"name": "estimate_auto_fare", "source": "mcp", "description": "Auto-rickshaw fare estimate"},
        {"name": "calculate_metro_ticket_fare", "source": "mcp", "description": "Metro fare and interchange delay"},
        {"name": "search_mall_shops", "source": "mcp", "description": "Search shops within a mall"},
        {"name": "search_movies", "source": "mcp", "description": "Movies running in city cinemas"},
        {"name": "save_itinerary", "source": "mcp", "description": "Save travel itinerary to DB"},
        {"name": "get_active_itineraries", "source": "mcp", "description": "Get planned itineraries"},
        {"name": "update_itinerary_status", "source": "mcp", "description": "Update itinerary status"},
        {"name": "get_transit_route", "source": "mcp", "description": "Compute transit routes"},
        {"name": "get_transit_station_nearby", "source": "mcp", "description": "Nearest transit station"},
        {"name": "search_events", "source": "mcp", "description": "Find cultural events"},
        {"name": "estimate_travel_time", "source": "mcp", "description": "Estimate travel time with traffic"},
        {"name": "get_weather_forecast", "source": "mcp", "description": "Weather forecast details"},
        {"name": "get_weather_radar_warning", "source": "mcp", "description": "Rain warning alerts"},
        {"name": "log_shared_expense", "source": "mcp", "description": "Log shared group expense"},
        {"name": "get_expense_balances", "source": "mcp", "description": "Summarized debt balances"},
        {"name": "get_budget_status", "source": "mcp", "description": "Monthly budget status"},
        {"name": "search_local_documents", "source": "mcp", "description": "RAG search on local docs"},
        {"name": "export_local_backup", "source": "mcp", "description": "Export data as ZIP"},
        {"name": "get_city_traffic_rules", "source": "mcp", "description": "Traffic rules and peak hours"},
    ]
    custom_tools = [
        {"name": "save_preference", "source": "custom", "description": "Save user preference to Chroma"},
        {"name": "recall_preferences", "source": "custom", "description": "Semantic search over saved preferences"},
        {"name": "calculate_departure_time", "source": "custom", "description": "Calculate when to leave"},
        {"name": "check_weather_recommendation", "source": "custom", "description": "Weather-based clothing advice"},
        {"name": "execute_hybrid_routing", "source": "custom", "description": "Route to Ollama or Gemini"},
        {"name": "manage_vault_encryption", "source": "custom", "description": "Encrypt/decrypt local DB"},
        {"name": "run_document_indexer", "source": "custom", "description": "Index local documents for RAG"},
        {"name": "generate_dating_plan", "source": "custom", "description": "Suggest romantic date plans"},
        {"name": "collect_post_event_feedback", "source": "custom", "description": "Post-outing feedback & rating"},
        {"name": "execute_travel_workflow", "source": "custom", "description": "ADK Workflow graph execution"},
    ]
    return {"mcp_tools": mcp_tools, "custom_tools": custom_tools}


@app.get("/api/dashboard/history", summary="Dashboard: History & suggestions")
async def dashboard_history():
    """Returns recent itineraries and memory metadata."""
    itineraries = _db_query(
        """
        SELECT a.*, p.name as destination_name, c.name as city_name
        FROM active_itineraries a
        JOIN cities c ON a.city_id = c.id
        LEFT JOIN points_of_interest p ON a.destination_poi_id = p.id
        ORDER BY a.id DESC LIMIT 10
        """
    )
    memories = _db_query(
        "SELECT * FROM memory_metadata ORDER BY last_accessed DESC LIMIT 10"
    )
    return {"itineraries": itineraries, "memories": memories}


@app.get("/api/dashboard/weather", summary="Dashboard: Weather widget")
async def dashboard_weather():
    """Returns weather forecasts for the default city."""
    city_row = _db_query(
        "SELECT id, name FROM cities WHERE slug = ?", (DEFAULT_CITY,)
    )
    city_name = city_row[0]["name"] if city_row else DEFAULT_CITY
    city_id = city_row[0]["id"] if city_row else 1

    forecasts = _db_query(
        "SELECT * FROM weather_forecasts WHERE city_id = ? ORDER BY hour_of_day",
        (city_id,),
    )
    return {"city_name": city_name, "forecasts": forecasts}


@app.get("/api/dashboard/expenses", summary="Dashboard: Expense tracker")
async def dashboard_expenses():
    """Returns budget status and recent expenses."""
    # Budget for a generic dashboard user
    month_yr = datetime.now().strftime("%m-%Y")
    budgets = _db_query(
        "SELECT * FROM user_budgets WHERE month_year = ? ORDER BY id LIMIT 1",
        (month_yr,),
    )
    budget = budgets[0] if budgets else {
        "monthly_limit_rupees": 5000.0,
        "active_spent_rupees": 0.0,
    }

    recent = _db_query(
        "SELECT * FROM shared_expenses ORDER BY id DESC LIMIT 8"
    )

    # Calculate balances
    import json as _json
    balances_raw = _db_query("SELECT * FROM shared_expenses")
    debts = {}
    for exp in balances_raw:
        payer = exp.get("payer_user_id", "")
        split_raw = exp.get("split_data", "")
        if not split_raw:
            continue
        try:
            splits = _json.loads(split_raw)
        except (_json.JSONDecodeError, TypeError):
            names = [n.strip() for n in split_raw.split(",") if n.strip()]
            if names:
                share = exp.get("total_amount_rupees", 0) / len(names)
                splits = {name: share for name in names}
            else:
                splits = {}
        for person, share in splits.items():
            if person == payer:
                continue
            pair = f"{person},{payer}"
            debts[pair] = debts.get(pair, 0.0) + share

    balance_strs = []
    for pair, amount in debts.items():
        if amount > 0:
            parts = pair.split(",")
            balance_strs.append(f"{parts[0]} owes {parts[1]} ₹{round(amount, 2)}")

    return {
        "budget": budget,
        "recent_expenses": recent,
        "balances": balance_strs,
    }


@app.get("/api/dashboard/telegram", summary="Dashboard: Telegram bot status")
async def dashboard_telegram():
    """Returns Telegram bot configuration status."""
    token = TELEGRAM_BOT_TOKEN
    masked = f"{token[:8]}...{token[-4:]}" if len(token) > 12 else ("●●●●●" if token else "—")
    allowed = _raw_allowed if _raw_allowed.strip() else "All (dev mode)"

    mode = "Webhook" if WEBHOOK_MODE else ("Polling" if token else "Inactive")

    return {
        "configured": bool(token),
        "token_masked": masked,
        "allowed_users": allowed,
        "mode": mode,
        "jobs_scheduled": bool(token),
    }


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to send to the agent")
    city: Optional[str] = Field(None, description="City slug")


@app.post("/api/dashboard/chat", summary="Dashboard: Interactive chat")
async def dashboard_chat(req: ChatRequest):
    """Route a chat message through the ADK agent."""
    city = req.city or DEFAULT_CITY
    try:
        from oota_agent.runner import run_agent_turn
        response = await run_agent_turn(message=req.message, city=city, user_id=0)
        return {"response": response, "tools_used": "auto"}
    except ImportError:
        return {"response": f"[Stub] Echo: {req.message!r} (city={city})", "tools_used": "none"}
    except Exception as exc:
        logger.exception("Dashboard chat failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Static file mount for frontend dashboard ──────────────────────────────────
_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_dashboard():
        """Serve the Aquamorphic dashboard at root."""
        return FileResponse(str(_frontend_dir / "index.html"))
