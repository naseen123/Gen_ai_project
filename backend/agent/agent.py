"""
agent.py — Public entry point for the TeamLens AI agent.

Wraps the LangGraph execution, handles formatting, and constructs
the final structured response for the API layer.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Dict, Any

from agent.graph import build_agent_graph
from agent.tools import Citation
from rag.index_manager import ChatSession

logger = logging.getLogger(__name__)

# Compile graph once
_agent_app = build_agent_graph()


@dataclass
class AgentResponse:
    """The final structured response returned to the frontend."""
    answer: str
    citations: List[Citation]
    tool_used: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [
                {
                    "sender": c.sender,
                    "timestamp": c.timestamp,
                    "message": c.message,
                }
                for c in self.citations
            ],
            "tool_used": self.tool_used,
            "confidence": self.confidence,
        }


def run_agent(
    question: str,
    session: ChatSession,
    history_str: str,
) -> AgentResponse:
    """
    Execute the full agent workflow for a user's question.

    Args:
        question:    The user's natural language question.
        session:     The active ChatSession containing RAG index and parsed data.
        history_str: Formatted conversation history string.

    Returns:
        AgentResponse containing the answer, citations, tool used, and confidence.
    """
    logger.info(f"run_agent invoked for session '{session.session_id}'")

    initial_state = {
        "session": session,
        "history": history_str,
        "question": question,
        "tool_name": "",
        "tool_params": {},
        "tool_output": "",
        "citations": [],
        "confidence": 0.0,
        "answer": "",
    }

    try:
        # Run the compiled LangGraph app
        final_state = _agent_app.invoke(initial_state)
        
        return AgentResponse(
            answer=final_state["answer"],
            citations=final_state["citations"],
            tool_used=final_state["tool_name"],
            confidence=final_state["confidence"],
        )
    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        return AgentResponse(
            answer="An unexpected error occurred while processing your request.",
            citations=[],
            tool_used="error",
            confidence=0.0,
        )
