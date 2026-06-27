"""
chat_service.py — High-level orchestration for the AI chat feature.

Bridges the FastAPI routes, the session manager, the memory store,
and the LangGraph agent.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from rag.index_manager import get_session
from agent.memory import add_turn, format_history_for_prompt
from agent.agent import run_agent, AgentResponse

logger = logging.getLogger(__name__)


def process_chat_message(session_id: str, question: str) -> Dict[str, Any]:
    """
    Process a single chat message from the user.

    1. Validates the session exists.
    2. Loads conversation history.
    3. Runs the LangGraph agent.
    4. Updates conversation history with the new turn and agent's answer.
    5. Returns the structured dictionary for the API.

    Args:
        session_id: The UUID of the active session.
        question:   The user's input.

    Returns:
        Dictionary matching the AgentResponse schema.
    
    Raises:
        ValueError: If the session does not exist.
    """
    session = get_session(session_id)
    if not session:
        logger.warning(f"Attempted to process message for invalid session: {session_id}")
        raise ValueError("Session not found or has expired. Please upload the chat again.")

    logger.info(f"Processing message for session {session_id}: '{question[:50]}...'")

    # Get history *before* adding the new question, so the prompt 
    # sees the past history distinctly from the current question.
    history_str = format_history_for_prompt(session_id)

    # Run agent
    response: AgentResponse = run_agent(
        question=question,
        session=session,
        history_str=history_str,
    )

    # Update memory
    add_turn(session_id, "user", question)
    add_turn(session_id, "assistant", response.answer)

    return response.to_dict()
