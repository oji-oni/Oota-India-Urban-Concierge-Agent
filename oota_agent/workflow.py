"""
Oota travel planning workflow module using google.adk.Workflow.
"""
from __future__ import annotations

import json
from typing import Any
from google.adk.workflow import Workflow, Edge, node, START

@node
async def calculate_midpoint_node(ctx: Any, node_input: Any) -> Any:
    # node_input is a dict containing {"city": city, "areas": [...]}
    # Simulates midpoint calculation or calls mcp server
    city = node_input.get("city", "bengaluru")
    areas = node_input.get("areas", [])
    
    # Simple midpoint response
    return {
        "city": city,
        "areas": areas,
        "calculated_midpoint_station": "Majestic Metro Station" if city == "bengaluru" else "Dadar Local Station",
        "nearest_malls": ["Phoenix Mall", "Orion Mall"] if city == "bengaluru" else ["Palladium Mall"]
    }

@node
async def check_weather_and_budget_node(ctx: Any, node_input: Any) -> Any:
    # node_input is from calculate_midpoint_node
    # Checks rain conditions and budget warnings
    return {
        "calculated_midpoint_station": node_input["calculated_midpoint_station"],
        "recommended_backup_mall": node_input["nearest_malls"][0],
        "rain_forecast_probability": 30,
        "budget_limit_rupees": 5000.0,
        "status": "APPROVED",
        "message": "Itinerary approved. Weather is pleasant (30% rain). Midpoint snapped to transit."
    }

travel_workflow = Workflow(
    name="travel_workflow",
    edges=[
        Edge(from_node=START, to_node=calculate_midpoint_node),
        Edge(from_node=calculate_midpoint_node, to_node=check_weather_and_budget_node)
    ]
)
