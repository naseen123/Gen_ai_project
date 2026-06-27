"""
vector_store.py — FAISS-based in-memory vector index for TeamLens RAG.

Uses FAISS IndexFlatIP (inner product) on L2-normalised vectors to compute
exact cosine similarity. No approximate nearest neighbour — full precision
for small-to-medium chats and acceptable speed for 100k+ message chats.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Tuple

import faiss
import numpy as np

from rag.chunker import MessageChunk

logger = logging.getLogger(__name__)


@dataclass
class FAISSIndex:
    """Container for the FAISS index and its associated chunk metadata."""
    index: faiss.IndexFlatIP
    chunks: List[MessageChunk]
    dimension: int


def build_index(
    embeddings: np.ndarray,
    chunks: List[MessageChunk],
) -> FAISSIndex:
    """
    Build a FAISS flat inner-product index from pre-computed embeddings.

    Because vectors are L2-normalised (done in embeddings.py), inner product
    is equivalent to cosine similarity — no further normalisation needed here.

    Args:
        embeddings: float32 ndarray of shape (N, D), already L2-normalised.
        chunks:     Corresponding list of MessageChunk objects (len == N).

    Returns:
        FAISSIndex containing the built index and chunk metadata.

    Raises:
        ValueError: If embeddings and chunks lengths do not match.
    """
    if len(embeddings) != len(chunks):
        raise ValueError(
            f"Embeddings ({len(embeddings)}) and chunks ({len(chunks)}) must have equal length."
        )
    if len(embeddings) == 0:
        raise ValueError("Cannot build FAISS index from empty embedding array.")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    logger.info(f"FAISS index built: {index.ntotal} vectors, dim={dimension}")
    return FAISSIndex(index=index, chunks=chunks, dimension=dimension)


def search_index(
    faiss_index: FAISSIndex,
    query_embedding: np.ndarray,
    top_k: int = 5,
) -> List[Tuple[MessageChunk, float]]:
    """
    Search the FAISS index for the top-k most similar chunks.

    Args:
        faiss_index:     The FAISSIndex built by build_index().
        query_embedding: float32 ndarray of shape (1, D), L2-normalised.
        top_k:           Number of results to return.

    Returns:
        List of (MessageChunk, cosine_score) tuples, sorted by score descending.
    """
    # Cap top_k at the number of stored vectors
    k = min(top_k, faiss_index.index.ntotal)
    if k == 0:
        return []

    scores, indices = faiss_index.index.search(query_embedding, k)

    results: List[Tuple[MessageChunk, float]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue  # FAISS sentinel for "no result"
        chunk = faiss_index.chunks[idx]
        results.append((chunk, float(score)))

    return results
