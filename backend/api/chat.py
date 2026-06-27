"""
chat.py — FastAPI router for TeamLens AI chat endpoints.
"""

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from rag.index_manager import create_session, clear_session as clear_session_from_manager
from agent.memory import clear_session_memory
from agent.chat_service import process_chat_message

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Chat"])

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class InitSessionRequest(BaseModel):
    parsed_chat: List[Dict[str, Any]]
    analysis: Dict[str, Any]

class ChatRequest(BaseModel):
    session_id: str
    question: str

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/init-session")
async def init_session(req: InitSessionRequest):
    """
    Initialise a new RAG session in memory.
    Builds the FAISS index from the uploaded parsed chat.
    """
    try:
        session_id = await create_session(
            parsed_chat=req.parsed_chat,
            analysis=req.analysis,
        )
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Failed to init session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize AI session: {str(e)}",
        )


@router.post("/chat")
async def chat(req: ChatRequest):
    """
    Process a chat question using the LangGraph agent.
    """
    try:
        response_dict = process_chat_message(
            session_id=req.session_id,
            question=req.question,
        )
        return response_dict
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat: {str(e)}",
        )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Clear a session and its memory.
    """
    from rag.index_manager import clear_session as clear_index
    index_cleared = clear_index(session_id)
    clear_session_memory(session_id)
    
    if not index_cleared:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )
    return {"status": "ok", "message": "Session cleared."}
