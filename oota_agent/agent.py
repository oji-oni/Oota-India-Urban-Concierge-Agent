"""
Oota root concierge agent definition.
"""
from __future__ import annotations

import os
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from oota_agent.prompts import (
    ROOT_INSTRUCTION,
    TRAVEL_PLANNER_INSTRUCTION,
    EXPENSE_TRACKER_INSTRUCTION,
    CURATION_INSTRUCTION
)
from oota_agent.tools import (
    save_preference, recall_preferences, calculate_departure_time,
    check_weather_recommendation, execute_hybrid_routing,
    manage_vault_encryption, run_document_indexer,
    generate_dating_plan, collect_post_event_feedback,
    execute_travel_workflow
)

load_dotenv()

def find_executable(name: str) -> str:
    # 1. Check if name exists directly in PATH
    path = shutil.which(name)
    if path:
        return path
    
    # 2. If Windows and not found, check common python user/system scripts dirs
    if os.name == "nt":
        # check user site scripts
        try:
            import site
            user_base = site.getuserbase()
            if user_base:
                win_path = Path(user_base) / "Scripts" / f"{name}.exe"
                if win_path.exists():
                    return str(win_path)
        except Exception:
            pass
        try:
            prefix_path = Path(sys.prefix) / "Scripts" / f"{name}.exe"
            if prefix_path.exists():
                return str(prefix_path)
        except Exception:
            pass
            
        # fallback path in %APPDATA%
        try:
            appdata = os.environ.get("APPDATA")
            if appdata:
                py_version = f"Python{sys.version_info.major}{sys.version_info.minor}"
                appdata_path = Path(appdata) / "Python" / py_version / "Scripts" / f"{name}.exe"
                if appdata_path.exists():
                    return str(appdata_path)
        except Exception:
            pass
                
    return name

# PYTHONUNBUFFERED=1 forces the OS-level binary buffer off so TextIOWrapper
# (used by mcp's stdio_server) flushes every JSON-RPC line immediately.
_mcp_env = {**os.environ, "PYTHONUNBUFFERED": "1"}
_project_root = str(Path(__file__).parent.parent.resolve())

# Configure the local database FastMCP server as a Toolset
city_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=["-u", "mcp_servers/city_data_server.py"],
            env=_mcp_env,
            cwd=_project_root
        ),
        timeout=90.0   # fastmcp takes ~14s (or more) to import on Windows cold-start
    )
)

# Connect to local ChromaDB via Stdio or local directory
chroma_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=["-u", "mcp_servers/chroma_mcp_wrapper.py",
                  "--client-type", "persistent",
                  "--data-dir", os.getenv("CHROMA_DATA_DIR", "./data/chroma")],
            env=_mcp_env,
            cwd=_project_root
        ),
        timeout=90.0   # fastmcp takes ~14s (or more) to import on Windows cold-start
    )
)

# Define Travel Planner Agent
travel_planner = LlmAgent(
    name="travel_planner",
    description="Plans travel itineraries, checks weather, calculates transit times, fares, and finds food or landmarks.",
    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction=TRAVEL_PLANNER_INSTRUCTION,
    tools=[
        city_mcp,
        calculate_departure_time,
        check_weather_recommendation,
        generate_dating_plan,
        collect_post_event_feedback,
        execute_travel_workflow
    ]
)

# Define Expense Tracker Agent
expense_tracker = LlmAgent(
    name="expense_tracker",
    description="Tracks shared group expenses, calculates balances, and guards the user's monthly budget limit.",
    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction=EXPENSE_TRACKER_INSTRUCTION,
    tools=[
        city_mcp
    ]
)

# Define Curation and Memory Agent
curation_agent = LlmAgent(
    name="curation_agent",
    description="Manages user preference memory, local document indexing (RAG), and data encryption/vault security.",
    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction=CURATION_INSTRUCTION,
    tools=[
        chroma_mcp,
        save_preference,
        recall_preferences,
        manage_vault_encryption,
        run_document_indexer
    ]
)

# Root Supervisor Agent
root_agent = LlmAgent(
    name="oota_concierge",
    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction=ROOT_INSTRUCTION,
    sub_agents=[
        travel_planner,
        expense_tracker,
        curation_agent
    ],
    tools=[
        execute_hybrid_routing
    ]
)
