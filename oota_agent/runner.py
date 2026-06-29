"""
Oota Agent Runner interface for Gateway integration.
"""
from __future__ import annotations

import os
from typing import Any, Optional
from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions import Session
from google.adk.cli.utils.service_factory import (
    create_session_service_from_options,
    create_artifact_service_from_options,
    create_memory_service_from_options,
)
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.genai import types
from google.adk.utils.context_utils import Aclosing
from oota_agent.agent import root_agent

async def run_agent_turn(message: str, city: str, user_id: int) -> str:
    """Run a single interaction turn with the Oota concierge agent.

    Args:
        message: The user's input message.
        city: The city context for the request.
        user_id: The unique ID of the user.

    Returns:
        The response text from the agent.
    """
    # Create services for local storage
    session_service = create_session_service_from_options(
        base_dir=".",
        use_local_storage=True,
    )
    artifact_service = create_artifact_service_from_options(
        base_dir=".",
        use_local_storage=True,
    )
    memory_service = create_memory_service_from_options(
        base_dir=".",
    )
    credential_service = InMemoryCredentialService()

    app = App(name="oota_agent", root_agent=root_agent)
    runner = Runner(
        app=app,
        artifact_service=artifact_service,
        session_service=session_service,
        memory_service=memory_service,
        credential_service=credential_service,
        auto_create_session=True,
    )

    session_id = f"session_{user_id}"
    next_message = types.Content(role='user', parts=[types.Part(text=message)])

    response_text = ""
    async with Aclosing(
        runner.run_async(
            user_id=str(user_id),
            session_id=session_id,
            new_message=next_message,
            state_delta={"city": city}
        )
    ) as agen:
        async for event in agen:
            if event.content and event.content.role == 'model' and event.content.parts:
                for part in event.content.parts:
                    if part.text and not part.thought:
                        response_text += part.text

    await runner.close()
    return response_text
