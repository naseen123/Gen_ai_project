"""
embeddings.py — Singleton embedding model for the TeamLens RAG pipeline.

Uses sentence-transformers/all-MiniLM-L6-v2:
  - 384-dimensional dense vectors
  - Runs entirely on CPU — no GPU required
  - ~80MB model, loaded once at module import time (cached for all requests)
  - Batched encoding for performance on large chats (100k+ messages)
"""

from __future__ import annotations

import logging
import numpy as np
from typing import List

from sentence_transformers import SentenceTransformer

from rag.chunker import MessageChunk

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton model — loaded once, shared across all requests
# ---------------------------------------------------------------------------
_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Return the cached model instance, loading it on first call."""
    global _model
    if _model is None:
        logger.info(f"Loading sentence-transformers model: {_MODEL_NAME}")
        _model = SentenceTransformer(_MODEL_NAME)
        logger.info("Embedding model loaded and cached.")
    return _model


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encode_chunks(
    chunks: List[MessageChunk],
    batch_size: int = 64,
    show_progress: bool = False,
) -> np.ndarray:
    """
    Encode a list of MessageChunks into L2-normalised float32 embedding vectors.

    Args:
        chunks:        List of MessageChunk objects to embed.
        batch_size:    Number of texts to encode per batch (controls memory use).
        show_progress: Whether to show tqdm progress bar.

    Returns:
        numpy ndarray of shape (len(chunks), 384), dtype float32, L2-normalised.
    """
    if not chunks:
        return np.empty((0, 384), dtype=np.float32)

    model = _get_model()
    texts = [chunk.text for chunk in chunks]

    logger.info(f"Encoding {len(texts)} chunks (batch_size={batch_size})...")
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=True,  # L2-normalise → cosine via inner product
    )
    return embeddings.astype(np.float32)


def encode_query(query: str) -> np.ndarray:
    """
    Encode a single query string into an L2-normalised embedding vector.

    Args:
        query: The user's natural-language question.

    Returns:
        numpy ndarray of shape (1, 384), dtype float32, L2-normalised.
    """
    model = _get_model()
    embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return embedding.astype(np.float32)
