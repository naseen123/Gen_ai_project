"""
retriever.py — High-level RAG retriever for TeamLens.

Combines the embeddings encoder and FAISS search into a single
clean interface used by the agent tools.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Dict, Any

from rag.chunker import MessageChunk
from rag.embeddings import encode_query
from rag.vector_store import FAISSIndex, search_index

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """A retrieved chunk with its relevance score and source messages."""
    chunk_id: str
    text: str
    senders: List[str]
    start_ts: str
    end_ts: str
    score: float
    source_messages: List[Dict[str, Any]]  # original parsed message dicts


def retrieve(
    query: str,
    faiss_index: FAISSIndex,
    top_k: int = 3,
) -> List[RetrievedChunk]:
    """
    Retrieve the top-k most semantically relevant chunks for a query.

    Args:
        query:       The user's natural-language question.
        faiss_index: Pre-built FAISSIndex for the current session.
        top_k:       Number of chunks to retrieve.

    Returns:
        List of RetrievedChunk objects sorted by cosine similarity (descending).
    """
    if not query.strip():
        logger.warning("retrieve() called with empty query.")
        return []

    query_embedding = encode_query(query)
    raw_results = search_index(faiss_index, query_embedding, top_k=top_k)

    retrieved: List[RetrievedChunk] = []
    for chunk, score in raw_results:
        retrieved.append(
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                senders=chunk.senders,
                start_ts=chunk.start_ts,
                end_ts=chunk.end_ts,
                score=score,
                source_messages=chunk.messages,
            )
        )

    logger.info(
        f"Retrieved {len(retrieved)} chunks for query='{query[:60]}...' "
        f"top_score={retrieved[0].score:.4f}" if retrieved else "no results"
    )
    return retrieved
