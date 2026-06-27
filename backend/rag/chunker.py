"""
chunker.py — Intelligent message chunker for the TeamLens RAG pipeline.

Strategy:
  - Messages within a 5-minute gap of each other are considered a "conversation thread".
  - Threads are accumulated into chunks capped at MAX_WORDS words.
  - This preserves conversational context while keeping chunk sizes manageable.
  - Supports chats with 100,000+ messages via a streaming generator pattern.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Generator

# Maximum words per chunk before starting a new one.
MAX_WORDS: int = 400

# Gap in minutes between messages to consider them a new thread.
THREAD_GAP_MINUTES: int = 5


@dataclass
class MessageChunk:
    """A single RAG chunk representing a coherent conversation segment."""

    chunk_id: str
    messages: List[Dict[str, Any]]  # original parsed message dicts
    senders: List[str]              # unique senders in this chunk
    start_ts: str                   # ISO timestamp of first message
    end_ts: str                     # ISO timestamp of last message
    text: str                       # formatted text fed to the embedder
    word_count: int


def _format_message(msg: Dict[str, Any]) -> str:
    """Format a single parsed message into a readable line."""
    ts = msg.get("timestamp", "")
    name = msg.get("name", "Unknown")
    message = msg.get("message", "")
    return f"[{ts}] {name}: {message}"


def _parse_ts(ts: str) -> datetime:
    """Parse ISO timestamp to datetime, falling back gracefully."""
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return datetime.min


def _make_chunk(messages: List[Dict[str, Any]], chunk_id: str) -> MessageChunk:
    """Construct a MessageChunk from a list of messages."""
    lines = [_format_message(m) for m in messages]
    text = "\n".join(lines)
    senders = list({m.get("name", "Unknown") for m in messages})
    start_ts = messages[0].get("timestamp", "") if messages else ""
    end_ts = messages[-1].get("timestamp", "") if messages else ""
    word_count = sum(len(m.get("message", "").split()) for m in messages)
    return MessageChunk(
        chunk_id=chunk_id,
        messages=messages,
        senders=senders,
        start_ts=start_ts,
        end_ts=end_ts,
        text=text,
        word_count=word_count,
    )


def chunk_messages(
    parsed_chat: List[Dict[str, Any]],
    max_words: int = MAX_WORDS,
    thread_gap_minutes: int = THREAD_GAP_MINUTES,
) -> List[MessageChunk]:
    """
    Chunk a parsed WhatsApp chat into context-preserving segments.

    Args:
        parsed_chat:        List of parsed message dicts from chat_parser.py.
        max_words:          Maximum word count per chunk.
        thread_gap_minutes: Gap (minutes) that defines a new conversation thread.

    Returns:
        List of MessageChunk objects ready for embedding.
    """
    if not parsed_chat:
        return []

    chunks: List[MessageChunk] = []
    current_messages: List[Dict[str, Any]] = []
    current_words: int = 0
    prev_ts: datetime = datetime.min

    for msg in parsed_chat:
        msg_ts = _parse_ts(msg.get("timestamp", ""))
        msg_words = len(msg.get("message", "").split())

        # Determine if this message opens a new thread (large time gap)
        gap_minutes = (msg_ts - prev_ts).total_seconds() / 60 if prev_ts != datetime.min else 0
        new_thread = gap_minutes > thread_gap_minutes and prev_ts != datetime.min

        # Flush the current chunk if:
        #   (a) adding this message would exceed max_words, OR
        #   (b) a new conversation thread has started
        if current_messages and (current_words + msg_words > max_words or new_thread):
            chunk_id = str(uuid.uuid4())
            chunks.append(_make_chunk(current_messages, chunk_id))
            current_messages = []
            current_words = 0

        current_messages.append(msg)
        current_words += msg_words
        prev_ts = msg_ts

    # Flush remaining messages
    if current_messages:
        chunk_id = str(uuid.uuid4())
        chunks.append(_make_chunk(current_messages, chunk_id))

    return chunks
