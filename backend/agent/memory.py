"""
memory.py — In-memory conversation history for TeamLens AI sessions.

Stores per-session conversation turns (role + content) as a sliding window.
No database. Memory lives as long as the server process.
Frontend clears memory by not sending session_id on page refresh.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Literal

logger = logging.getLogger(__name__)

# Maximum number of conversation turns to keep in context
MAX_TURNS: int = 10

RoleType = Literal["user", "assistant"]


@dataclass
class Turn:
    """A single conversation turn."""
    role: RoleType
    content: str


# Module-level memory store: session_id → list of turns
_memory: Dict[str, List[Turn]] = {}


def add_turn(session_id: str, role: RoleType, content: str) -> None:
    """
    Append a turn to the conversation history for a session.

    Args:
        session_id: The session UUID.
        role:       'user' or 'assistant'.
        content:    The message content.
    """
    if session_id not in _memory:
        _memory[session_id] = []

    _memory[session_id].append(Turn(role=role, content=content))

    # Keep only the last MAX_TURNS turns (sliding window)
    if len(_memory[session_id]) > MAX_TURNS:
        _memory[session_id] = _memory[session_id][-MAX_TURNS:]


def get_history(session_id: str) -> List[Turn]:
    """
    Get the conversation history for a session.

    Args:
        session_id: The session UUID.

    Returns:
        List of Turn objects (up to MAX_TURNS), oldest first.
    """
    return _memory.get(session_id, [])


def format_history_for_prompt(session_id: str) -> str:
    """
    Format conversation history as a readable string for LLM prompts.

    Args:
        session_id: The session UUID.

    Returns:
        Multi-line string with role-prefixed turns, or 'None' if empty.
    """
    turns = get_history(session_id)
    if not turns:
        return "None"
    lines = []
    for turn in turns:
        prefix = "User" if turn.role == "user" else "Assistant"
        lines.append(f"{prefix}: {turn.content}")
    return "\n".join(lines)


def clear_session_memory(session_id: str) -> None:
    """
    Remove all conversation history for a session.

    Args:
        session_id: The session UUID.
    """
    if session_id in _memory:
        del _memory[session_id]
        logger.info(f"Conversation memory cleared for session {session_id}.")
