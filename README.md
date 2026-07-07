# 🍛 Oota — India Urban Concierge Agent

> **Privacy-first AI concierge for Indian cities.** All data stays on your device — only Gemini API calls and (optionally) Telegram messages leave your machine.

---

## Overview

**Oota & Commute** is a multi-city, privacy-first AI agent built on Google ADK + FastMCP. It helps you navigate daily urban life in India through natural conversation, without sending your personal data to third-party services.

### Capabilities (22 tools)

- 🗺️ **Restaurant & café discovery** — curated recommendations by cuisine, budget, and neighbourhood
- 🍽️ **Street-food map** — hidden gems and local favourites by city zone
- 🚇 **Metro route planning** — optimal routes with interchange guidance (Namma Metro, Delhi Metro, etc.)
- 🚌 **Bus route lookup** — BMTC, BEST, DTC, and other city bus services
- 🛺 **Auto / cab fare estimation** — typical fare ranges and surge-free windows
- 📅 **Itinerary builder** — day-trip plans with time estimates and travel buffers
- ⏰ **Proactive departure alerts** — "Leaving for Koshy's soon! Still on track?"
- 💸 **Bill splitting** — split any amount among named participants, track who owes what
- 📊 **Expense balances** — running ledger of group expenses with settlement suggestions
- 🛒 **Shopping list builder** — items with suggested markets and price ranges
- 🌦️ **Weather-aware suggestions** — adjust plans based on live local weather context
- 🔍 **Neighbourhood explorer** — walkability, vibe, safety notes, and key landmarks
- 🗣️ **Phrasebook** — Kannada, Hindi, Tamil, Telugu, Bengali, Marathi phrases on demand
- 🏙️ **Multi-city switching** — seamlessly switch between 9 supported cities
- 🔐 **Encrypted local storage** — Fernet-encrypted SQLite + ChromaDB, zero cloud sync
- 📦 **Data export** — portable ZIP backup of all your preferences and history
- 🤖 **Skill auto-generation** — agent learns your patterns and creates reusable skills
- 💾 **Memory curation** — periodically summarises and compresses your preferences
- 📡 **Telegram gateway** — full bot with proactive reminders and inline feedback
- 🌐 **Webhook / REST API** — FastAPI server for web or mobile front-ends
- 🐳 **Docker / Compose deployment** — single-command containerised run
- ☸️ **Kubernetes deployment** — production-grade manifests with health probes and PVCs

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.12+ | Required |
| Google API Key | — | [Get from Google AI Studio](https://aistudio.google.com/app/apikey) |
| Telegram Bot Token | — | Optional — from [@BotFather](https://t.me/BotFather) |
| Docker & Docker Compose | 24+ / v2+ | For containerised deployment |
| kubectl | 1.28+ | For Kubernetes deployment |

---

## Quick Start (Local Terminal)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/oota.git
cd oota

# 2. Configure environment
cp .env.example .env
# Edit .env — fill in GOOGLE_API_KEY and (optionally) TELEGRAM_BOT_TOKEN

# 3. Install dependencies
pip install -e .

# 4. Seed the local database
python data/seed_database.py

# 5. Start the agent
python main.py
```

If no `TELEGRAM_BOT_TOKEN` is set, the agent starts in **interactive terminal mode** using ADK.

---

## Telegram Setup

1. Message **[@BotFather](https://t.me/BotFather)** on Telegram
2. Send `/newbot` and follow the prompts to create your bot
3. Copy the token shown by BotFather
4. Add to `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdef...
   ```
5. Get your Telegram user ID:
   - Message [@userinfobot](https://t.me/userinfobot) — it replies with your numeric ID
6. Add your ID to `.env` (comma-separated for multiple users):
   ```env
   TELEGRAM_ALLOWED_USER_IDS=123456789
   ```
7. Start the bot:
   ```bash
   python main.py
   ```

### Available Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message and feature overview |
| `/help` | Command reference |
| `/switch_city [city]` | Change active city (or prompts interactively) |
| `/split 1200 at MTR for Alice, Bob` | Split a bill |
| `/balances` | Show outstanding group expense balances |
| `/export` | Export all local data as a ZIP backup |
| `/status` | Show system status and today's itinerary |

Just type naturally for everything else — e.g. *"Find a quiet café near Koramangala with good WiFi"*.

---

## Docker Deployment

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env — fill in your API keys

# 2. Build and start
docker compose up --build

# Access the API
curl http://localhost:8000/health
```

The container exposes port **8000** with the following endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Interactive Frontend Dashboard |
| `/health` | GET | Health status + DB connectivity |
| `/cities` | GET | List of supported city slugs |
| `/agent` | POST | Run an agent turn (JSON body) |
| `/webhook/{token}` | POST | Telegram webhook receiver |
| `/docs` | GET | Interactive OpenAPI docs |
| `/api/dashboard/*` | GET/POST | REST endpoints powering the frontend dashboard |

---

## Interactive Frontend Dashboard

Oota comes with a premium single-page **Interactive Frontend Dashboard** built using an **Aquamorphic Design System** (fluid glassmorphism, responsive grids, dark/light theme, and beautiful emojis).

### Dashboard Panels & Features
- 🟢 **System Status** — real-time health of SQLite, ChromaDB, and Telegram Bot
- 🤖 **Agent Hierarchy** — visualize the ADK agent tree and sub-agent statuses
- 💬 **Interactive Chat** — chat directly with Oota; responses populate the system logs
- 🌦️ **Weather Widget** — hourly weather forecast and UV/rain badges for the active city
- 🔧 **Tools & Capabilities** — real-time listing of all 35+ available tools (MCP + Custom)
- 📜 **History & Suggestions** — chronological log of planned itineraries and accessed memories
- 💸 **Expense Tracker** — interactive budget limits gauge and recent ledger logs
- 📱 **Telegram Bot Info** — configuration details and scheduled jobs
- 🧠 **Autonomous Decisions Log** — real-time activity log of what decisions the agent has made

### How to Run the Dashboard
Set the `WEBHOOK_MODE` environment variable to `true` or enable `DASHBOARD_MODE=true` in your `.env`.

```bash
# Start in Webhook/Dashboard mode
$env:WEBHOOK_MODE="true"; python main.py

# Open your browser and navigate to:
http://localhost:8000/
```

---

## Kubernetes Deployment

```bash
# 1. Build and push image to your registry
docker build -t your-registry/oota-agent:latest .
docker push your-registry/oota-agent:latest

# Update image in k8s/deployment.yaml:
#   image: your-registry/oota-agent:latest

# 2. Create secrets (never store real values in secret.yaml)
kubectl create secret generic oota-secrets \
  --from-literal=GOOGLE_API_KEY=your_google_api_key \
  --from-literal=TELEGRAM_BOT_TOKEN=your_telegram_token \
  --from-literal=ENCRYPTION_KEY=your_fernet_key

# 3. Apply all manifests
kubectl apply -f k8s/

# 4. Verify deployment
kubectl get pods -l app=oota-agent
kubectl logs -l app=oota-agent -f

# 5. Set webhook URL (replace with your public URL)
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -d "url=https://your-domain.com/webhook/<TOKEN>"
```

---

## Adding a New City

1. Create `data/cities/{city_slug}.py`
2. Implement `seed_city(conn: sqlite3.Connection, city_id: int) -> None`
3. Register the city in `data/cities/__init__.py` or the main seed list
4. Run `python data/seed_database.py`
5. Say *"Switch to {city}"* in the agent or use `/switch_city {city}` in Telegram

---

## Privacy Architecture

```
Your Device
├── SQLite (oota.db)          ← Fernet-encrypted at rest
│   ├── venues, routes, fares
│   ├── itineraries & expenses
│   └── active_itineraries (scheduler source)
├── ChromaDB (data/chroma/)   ← Local vector store, no cloud sync
│   └── User preference embeddings
└── .agents/skills/           ← Auto-generated reusable skill files

Outbound connections (only):
├── api.google.com            ← Gemini API (planning & reasoning)
└── api.telegram.org          ← Telegram Bot API (if enabled)
```

- **No analytics, no telemetry, no third-party tracking**
- **Backup anytime**: `/export` → portable ZIP of your complete data
- **Fernet key** is stored only in your `.env` file (or k8s Secret)
- Revoke access instantly: delete `.env` and `data/` directory

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Google Gemini API key (**required**) |
| `GEMINI_MODEL` | `gemini-2.0-flash-exp` | Gemini model name |
| `SQLITE_DB_PATH` | `./data/oota.db` | SQLite database path |
| `CHROMA_DATA_DIR` | `./data/chroma_db` | ChromaDB persistence directory |
| `ENCRYPTION_KEY` | — | Fernet key for at-rest encryption |
| `DEFAULT_CITY` | `bengaluru` | City slug if none specified |
| `TELEGRAM_BOT_TOKEN` | — | Bot token from @BotFather |
| `TELEGRAM_ALLOWED_USER_IDS` | *(empty = all)* | Comma-separated allowed IDs |
| `WEBHOOK_MODE` | `false` | `true` → FastAPI webhook server |
| `WEBHOOK_URL` | — | Public HTTPS URL for webhook |
| `DASHBOARD_MODE` | `false` | `true` → Auto-enables webhook mode and serves dashboard |
| `PORT` | `8000` | Server port |
| `OLLAMA_HOST` | `http://localhost:11434` | Local LLM fallback URL |

---

## Project Structure

```
oota/
├── data/
│   ├── cities/              # City seed modules (bengaluru.py, mumbai.py, …)
│   ├── documents/           # Local docs for RAG (menus, transit maps, etc.)
│   └── seed_database.py     # DB initialiser — run once before first use
├── frontend/                # Interactive Frontend Dashboard
│   ├── index.html           # Main dashboard layout
│   ├── styles.css           # Aquamorphic CSS design system
│   └── app.js               # Theme, polling, and interactive chat logic
├── mcp_servers/
│   └── city_data_server.py  # FastMCP server exposing 22 tools
├── oota_agent/
│   ├── agent.py             # Root LlmAgent definition
│   ├── tools.py             # Custom ADK tool implementations
│   ├── prompts.py           # System prompt (city-aware)
│   ├── runner.py            # run_agent_turn() — called by gateways
│   ├── skill_generator.py   # Auto-skill creation from conversation patterns
│   └── memory_curator.py    # Periodic preference summarisation
├── gateway/
│   ├── __init__.py
│   ├── telegram_bot.py      # Full async Telegram bot (python-telegram-bot v20+)
│   └── webhook_server.py    # FastAPI REST + Telegram webhook server + Dashboard API
├── .agents/
│   └── skills/
│       ├── auto/            # Machine-generated skills (committed to git)
│       └── .archive/        # Retired skills (kept for reference)
├── k8s/
│   ├── deployment.yaml      # Kubernetes Deployment
│   ├── service.yaml         # Kubernetes ClusterIP Service
│   ├── pvc.yaml             # PersistentVolumeClaims (data + skills)
│   ├── secret.yaml          # Secret template (fill before applying)
│   └── configmap.yaml       # Non-secret configuration
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # Local containerised run
├── pyproject.toml           # Project metadata & dependencies
├── .env.example             # Environment variable template
└── main.py                  # Entry point — auto-selects run mode
```

---

## Development

```bash
# Run tests
pytest tests/ -v

# Lint
ruff check .

# Format
ruff format .

# Type-check
mypy oota_agent/ gateway/

# Start MCP server in isolation (for debugging)
python mcp_servers/city_data_server.py

# Start FastAPI server directly (without bot)
uvicorn gateway.webhook_server:app --reload
```

---

## Supported Cities

| Slug | City |
|---|---|
| `bengaluru` | Bengaluru (Bangalore) |
| `mumbai` | Mumbai |
| `delhi` | New Delhi |
| `chennai` | Chennai |
| `hyderabad` | Hyderabad |
| `kolkata` | Kolkata |
| `pune` | Pune |
| `ahmedabad` | Ahmedabad |
| `jaipur` | Jaipur |

---

## Kaggle Capstone Evaluation Map

This project demonstrates the key concepts of the agent engineering course:

| Required Concept | Implementation Location / Details |
|---|---|
| **Agent / Multi-agent system (ADK)** | Root agent `oota_concierge` in `oota_agent/agent.py` orchestrating three specialized conversational sub-agents: `travel_planner` (itineraries & transit routing), `expense_tracker` (budget & ledger split tracking), and `curation_agent` (user preferences & vault encryption), plus background sub-modules `skill_generator` and `memory_curator`. |
| **MCP Server** | Custom FastMCP server in `mcp_servers/city_data_server.py` exposing 25 tools for local SQLite transit, geography, midpoint, and budget math. Integrated via `McpToolset` in `agent.py`. |
| **Security Features** | Cryptographic vault (`manage_vault_encryption` in `oota_agent/tools.py`) using Fernet key DB encryption-at-rest. Privacy-pure local ChromaDB embedding preference storage. |
| **Deployability** | Multi-stage `Dockerfile` and `docker-compose.yml` for local sandbox containers, plus full Kubernetes manifests (`deployment`, `service`, `pvc`, `secret`, `configmap`) in `k8s/` folder. |
| **Agent Skills** | Structured YAML frontmatter skill playbooks in `.agents/skills/india-city-navigator/SKILL.md` loaded automatically by the agent engine. |

---

## Made with ❤️

