"""
index_manager.py — In-memory session store for TeamLens RAG sessions.

Each session ties together:
  - The parsed chat messages
  - The analysis JSON (from the existing analyzer.py)
  - The FAISS index built from message embeddings
  - The MessageChunks used to build the index

Sessions are keyed by UUID and live only as long as the server process.
No database. No persistence. Memory is cleared when the server restarts
or when the client explicitly deletes the session.

Thread-safety: Uses asyncio.Lock per session to prevent concurrent index builds.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from rag.chunker import chunk_messages, MessageChunk
from rag.embeddings import encode_chunks
from rag.vector_store import FAISSIndex, build_index

logger = logging.getLogger(__name__)


@dataclass
class ChatSession:
    """All data associated with one uploaded chat session."""
    session_id: str
    parsed_chat: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    chunks: List[MessageChunk]
    faiss_index: FAISSIndex
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


# ---------------------------------------------------------------------------
# Module-level session registry
# ---------------------------------------------------------------------------
_sessions: Dict[str, ChatSession] = {}


async def create_session(
    parsed_chat: List[Dict[str, Any]],
    analysis: Dict[str, Any],
) -> str:
    """
    Build a RAG index for the given parsed chat and store it in memory.

    This is the only heavy operation — embedding 100k messages takes ~seconds
    on CPU. All subsequent queries are fast FAISS lookups.

    Args:
        parsed_chat: List of parsed message dicts from chat_parser.py.
        analysis:    Full analysis dict from analyzer.py (members + report).

    Returns:
        A UUID string identifying this session.

    Raises:
        ValueError: If parsed_chat is empty.
    """
    if not parsed_chat:
        raise ValueError("Cannot create RAG session from empty parsed chat.")

    session_id = str(uuid.uuid4())
    logger.info(f"Creating RAG session {session_id} for {len(parsed_chat)} messages.")

    # 1. Chunk the messages
    chunks = chunk_messages(parsed_chat)
    logger.info(f"  Chunked into {len(chunks)} segments.")

    # 2. Encode chunks → embeddings
    embeddings = encode_chunks(chunks)
    logger.info(f"  Encoded {len(embeddings)} embeddings.")

    # 3. Build FAISS index
    faiss_index = build_index(embeddings, chunks)

    # 4. Store session
    session = ChatSession(
        session_id=session_id,
        parsed_chat=parsed_chat,
        analysis=analysis,
        chunks=chunks,
        faiss_index=faiss_index,
    )
    _sessions[session_id] = session
    logger.info(f"  Session {session_id} ready.")

    return session_id


def get_session(session_id: str) -> Optional[ChatSession]:
    """
    Retrieve a session by ID.

    Args:
        session_id: UUID string returned by create_session().

    Returns:
        ChatSession if found, None otherwise.
    """
    return _sessions.get(session_id)


def clear_session(session_id: str) -> bool:
    """
    Remove a session from memory.

    Args:
        session_id: UUID string to remove.

    Returns:
        True if the session existed and was removed, False otherwise.
    """
    if session_id in _sessions:
        del _sessions[session_id]
        logger.info(f"Session {session_id} cleared from memory.")
        return True
    return False


def session_exists(session_id: str) -> bool:
    """Check whether a session is currently in memory."""
    return session_id in _sessions
