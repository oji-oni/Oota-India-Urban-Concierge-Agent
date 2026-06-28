"""
Oota root concierge agent definition.
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import McpToolset, StdioConnectionParams
from oota_agent.prompts import SYSTEM_PROMPT
from oota_agent.tools import (
    save_preference, recall_preferences, calculate_departure_time,
    check_weather_recommendation, execute_hybrid_routing,
    manage_vault_encryption, run_document_indexer,
    generate_dating_plan, collect_post_event_feedback
)

load_dotenv()

# Configure the local database FastMCP server as a Toolset
city_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        command="python",
        args=["mcp_servers/city_data_server.py"]
    )
)

# Connect to local ChromaDB via Stdio or local directory
chroma_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        command="chroma-mcp",
        args=["--client-type", "persistent", "--data-dir", os.getenv("CHROMA_DATA_DIR", "./data/chroma")]
    )
)

root_agent = LlmAgent(
    name="oota_concierge",
    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    instruction=SYSTEM_PROMPT,
    tools=[
        city_mcp,
        chroma_mcp,
        save_preference,
        recall_preferences,
        calculate_departure_time,
        check_weather_recommendation,
        execute_hybrid_routing,
        manage_vault_encryption,
        run_document_indexer,
        generate_dating_plan,
        collect_post_event_feedback
    ]
)
