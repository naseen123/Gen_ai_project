"""
tools.py — All 8 agent tools for TeamLens AI.

Each tool receives a session (ChatSession) and a parameters dict,
then returns a ToolResult with content, citations, and confidence.

Tools NEVER rewrite existing analyzer.py or chat_parser.py logic —
they only READ from the cached session data.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

from groq import Groq

from rag.retriever import retrieve, RetrievedChunk
from rag.index_manager import ChatSession
from agent.prompts import WEEKLY_SUMMARY_PROMPT, EVIDENCE_PROMPT

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared result type
# ---------------------------------------------------------------------------

@dataclass
class Citation:
    """A single source message used as evidence."""
    sender: str
    timestamp: str
    message: str


@dataclass
class ToolResult:
    """Structured output from any agent tool."""
    content: str                          # Human-readable summary for the synthesizer
    citations: List[Citation] = field(default_factory=list)
    confidence: float = 0.8
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helper: Groq client
# ---------------------------------------------------------------------------

def _groq() -> Groq:
    """Return a configured Groq client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set.")
    return Groq(api_key=api_key)


def _chunks_to_citations(chunks: List[RetrievedChunk]) -> List[Citation]:
    """Convert retrieved chunks into Citation objects for the frontend."""
    citations: List[Citation] = []
    for chunk in chunks:
        for msg in chunk.source_messages[:3]:  # max 3 messages per chunk
            citations.append(Citation(
                sender=msg.get("name", "Unknown"),
                timestamp=msg.get("timestamp", ""),
                message=msg.get("message", ""),
            ))
    return citations


# ---------------------------------------------------------------------------
# Tool 1: Semantic Chat Search
# ---------------------------------------------------------------------------

def semantic_search(session: ChatSession, params: Dict[str, Any]) -> ToolResult:
    """
    Retrieve the top-k semantically relevant message chunks for a query.

    Args:
        session: The active ChatSession.
        params:  Must contain 'query' (str). Optional 'top_k' (int, default 5).

    Returns:
        ToolResult with retrieved chunk texts and citations.
    """
    query: str = params.get("query", "")
    top_k: int = int(params.get("top_k", 5))

    chunks = retrieve(query, session.faiss_index, top_k=top_k)
    if not chunks:
        return ToolResult(
            content="No relevant messages found for this query.",
            confidence=0.1,
        )

    content_lines = []
    for i, chunk in enumerate(chunks, 1):
        senders = ", ".join(chunk.senders)
        content_lines.append(
            f"[{i}] ({senders} | {chunk.start_ts[:10]} → {chunk.end_ts[:10]} | "
            f"score={chunk.score:.3f}):\n{chunk.text}"
        )

    avg_score = sum(c.score for c in chunks) / len(chunks)
    return ToolResult(
        content="\n\n".join(content_lines),
        citations=_chunks_to_citations(chunks),
        confidence=min(avg_score, 1.0),
    )


# ---------------------------------------------------------------------------
# Tool 2: Contribution Analysis
# ---------------------------------------------------------------------------

def contribution_analysis(session: ChatSession, params: Dict[str, Any]) -> ToolResult:
    """
    Return the cached contribution analysis JSON.

    Reads directly from session.analysis — reuses the output of
    the existing analyzer.py without touching it.
    """
    members = session.analysis.get("analysis", {}).get("members", [])
    if not members:
        return ToolResult(content="No contribution analysis found.", confidence=0.1)

    # Sort by overall_score descending
    sorted_members = sorted(members, key=lambda m: m.get("overall_score", 0), reverse=True)

    lines = ["**Contribution Analysis — All Members**\n"]
    for i, m in enumerate(sorted_members, 1):
        score = m.get("overall_score", 0)
        summary = m.get("summary", "—")
        lines.append(f"{i}. **{m['name']}** — Score: {score:.1f}/10\n   {summary}")

    return ToolResult(
        content="\n".join(lines),
        confidence=0.95,
        metadata={"members": sorted_members},
    )


# ---------------------------------------------------------------------------
# Tool 3: Narrative Report
# ---------------------------------------------------------------------------

def narrative_report(session: ChatSession, params: Dict[str, Any]) -> ToolResult:
    """
    Return the cached narrative faculty evaluation report.

    Reads session.analysis['report'] — never calls Groq again.
    """
    report = session.analysis.get("report", "")
    if not report:
        return ToolResult(content="No narrative report available.", confidence=0.1)

    return ToolResult(
        content=report,
        confidence=0.95,
    )


# ---------------------------------------------------------------------------
# Tool 4: Promise vs Delivery
# ---------------------------------------------------------------------------

def promise_vs_delivery(session: ChatSession, params: Dict[str, Any]) -> ToolResult:
    """
    Extract promises made and deliveries confirmed per member.

    Reads from session.analysis (existing analyzer output).
    """
    members = session.analysis.get("analysis", {}).get("members", [])
    if not members:
        return ToolResult(content="No member data found.", confidence=0.1)

    # Filter to specific member if requested
    target_name: Optional[str] = params.get("member_name")
    if target_name:
        members = [m for m in members if target_name.lower() in m.get("name", "").lower()]

    lines = ["**Promise vs Delivery Analysis**\n"]
    citations: List[Citation] = []

    for m in members:
        name = m.get("name", "Unknown")
        promises = m.get("promises", [])
        deliveries = m.get("deliveries", [])
        ratio = m.get("promise_delivery_ratio", 0)
        ratio_pct = f"{ratio * 100:.0f}%"

        lines.append(f"**{name}** (delivery rate: {ratio_pct})")
        if promises:
            lines.append(f"  Promises ({len(promises)}): " + " | ".join(promises[:5]))
        if deliveries:
            lines.append(f"  Delivered ({len(deliveries)}): " + " | ".join(deliveries[:5]))

        pending = max(0, len(promises) - len(deliveries))
        if pending > 0:
            lines.append(f"  ⚠️  {pending} potentially pending promise(s)")
        lines.append("")

        # Add evidence from raw chat for promises
        for promise in promises[:2]:
            matching = [
                msg for msg in session.parsed_chat
                if msg.get("name") == name and any(
                    kw in msg.get("message", "").lower()
                    for kw in ["will", "i'll", "gonna", "going to"]
                )
            ][:2]
            for msg in matching:
                citations.append(Citation(
                    sender=msg.get("name", ""),
                    timestamp=msg.get("timestamp", ""),
                    message=msg.get("message", ""),
                ))

    return ToolResult(
        content="\n".join(lines),
        citations=citations[:10],
        confidence=0.9,
    )


# ---------------------------------------------------------------------------
# Tool 5: Timeline Search
# ---------------------------------------------------------------------------

def timeline_search(session: ChatSession, params: Dict[str, Any]) -> ToolResult:
    """
    Find messages or events within a date range.

    Args:
        params: 'start_date' (YYYY-MM-DD), 'end_date' (YYYY-MM-DD), optional 'member_name'.
    """
    start_str: str = params.get("start_date", "")
    end_str: str = params.get("end_date", "")
    member_name: Optional[str] = params.get("member_name")

    def parse_date(s: str) -> Optional[datetime]:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    start_dt = parse_date(start_str)
    end_dt = parse_date(end_str)

    filtered = []
    for msg in session.parsed_chat:
        try:
            msg_dt = datetime.fromisoformat(msg.get("timestamp", ""))
        except (ValueError, TypeError):
            continue

        if start_dt and msg_dt < start_dt:
            continue
        if end_dt and msg_dt > end_dt:
            continue
        if member_name and member_name.lower() not in msg.get("name", "").lower():
            continue
        filtered.append(msg)

    if not filtered:
        return ToolResult(
            content=f"No messages found between {start_str or 'start'} and {end_str or 'end'}.",
            confidence=0.2,
        )

    # Summarise by member
    by_member: Dict[str, List[Dict]] = {}
    for msg in filtered:
        name = msg.get("name", "Unknown")
        by_member.setdefault(name, []).append(msg)

    lines = [f"**Timeline Search** ({len(filtered)} messages)\n"]
    citations: List[Citation] = []

    for name, msgs in sorted(by_member.items(), key=lambda x: -len(x[1])):
        lines.append(f"**{name}** — {len(msgs)} message(s)")
        for msg in msgs[:3]:
            ts = msg.get("timestamp", "")[:10]
            text = msg.get("message", "")
            lines.append(f"  [{ts}] {text[:100]}")
            citations.append(Citation(sender=name, timestamp=ts, message=text))

    return ToolResult(
        content="\n".join(lines),
        citations=citations[:15],
        confidence=0.85,
    )


# ---------------------------------------------------------------------------
# Tool 6: Member Profile
# ---------------------------------------------------------------------------

def member_profile(session: ChatSession, params: Dict[str, Any]) -> ToolResult:
    """
    Return the full profile of a specific team member.

    Args:
        params: 'member_name' (str) — partial match supported.
    """
    target: str = params.get("member_name", "")
    members = session.analysis.get("analysis", {}).get("members", [])

    # Fuzzy match by name
    matched = [
        m for m in members
        if target.lower() in m.get("name", "").lower()
    ]

    if not matched:
        names = [m.get("name", "") for m in members]
        return ToolResult(
            content=f"Member '{target}' not found. Available members: {', '.join(names)}",
            confidence=0.1,
        )

    m = matched[0]
    name = m.get("name", "Unknown")
    scores = m.get("scores", {})
    overall = m.get("overall_score", 0)
    summary = m.get("summary", "—")
    promises = m.get("promises", [])
    deliveries = m.get("deliveries", [])
    ratio = m.get("promise_delivery_ratio", 0)
    avg_resp = m.get("avg_response_time_hours", None)
    peak_hours = m.get("peak_activity_hours", [])
    top_words = m.get("top_words", [])

    lines = [
        f"## Member Profile: {name}",
        f"**Overall Score:** {overall:.1f}/10",
        f"**Summary:** {summary}",
        "",
        "**Scores:**",
        f"  - Message Frequency: {scores.get('message_frequency', 0):.1f}",
        f"  - Initiative: {scores.get('initiative', 0):.1f}",
        f"  - Task Ownership: {scores.get('task_ownership', 0):.1f}",
        f"  - Follow-Through: {scores.get('follow_through', 0):.1f}",
        f"  - Responsiveness: {scores.get('responsiveness', 0):.1f}",
        "",
        f"**Promise/Delivery Ratio:** {ratio * 100:.0f}%",
        f"**Promises:** {len(promises)} | **Delivered:** {len(deliveries)}",
    ]

    if avg_resp is not None:
        lines.append(f"**Avg Response Time:** {avg_resp:.1f} hours")
    if peak_hours:
        lines.append(f"**Peak Activity Hours:** {peak_hours}")
    if top_words:
        lines.append(f"**Top Words:** {', '.join(top_words[:10])}")

    # Add some evidence from raw chat
    citations: List[Citation] = []
    member_msgs = [msg for msg in session.parsed_chat if msg.get("name") == name]
    for msg in member_msgs[:5]:
        citations.append(Citation(
            sender=name,
            timestamp=msg.get("timestamp", ""),
            message=msg.get("message", ""),
        ))

    return ToolResult(
        content="\n".join(lines),
        citations=citations,
        confidence=0.95,
        metadata={"member": m},
    )


# ---------------------------------------------------------------------------
# Tool 7: Weekly Summary
# ---------------------------------------------------------------------------

def weekly_summary(session: ChatSession, params: Dict[str, Any]) -> ToolResult:
    """
    Generate week-by-week summaries using only retrieved chunks (not full chat).

    Calls Groq only on small, relevant chunks — not the entire chat.
    """
    # Group raw messages by ISO week
    weeks: Dict[str, List[Dict]] = {}
    for msg in session.parsed_chat:
        try:
            dt = datetime.fromisoformat(msg.get("timestamp", ""))
            week_key = dt.strftime("%Y-W%W")
        except (ValueError, TypeError):
            week_key = "Unknown"
        weeks.setdefault(week_key, []).append(msg)

    if not weeks:
        return ToolResult(content="No messages to summarise.", confidence=0.1)

    client = _groq()
    summaries: List[str] = []
    sorted_weeks = sorted(weeks.keys())

    for week in sorted_weeks:
        msgs = weeks[week]
        # Format a sample of messages (max 60 messages per week to stay in token budget)
        sample = msgs[:60]
        text = "\n".join(
            f"[{m.get('timestamp','')[:10]}] {m.get('name','')}: {m.get('message','')}"
            for m in sample
        )
        prompt = WEEKLY_SUMMARY_PROMPT.format(messages=text)
        try:
            resp = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=300,
            )
            week_summary = resp.choices[0].message.content.strip()
        except Exception as e:
            week_summary = f"(Summary unavailable: {e})"

        summaries.append(f"**Week {week}** ({len(msgs)} messages)\n{week_summary}")

    return ToolResult(
        content="\n\n---\n\n".join(summaries),
        confidence=0.85,
    )


# ---------------------------------------------------------------------------
# Tool 8: Evidence Generator
# ---------------------------------------------------------------------------

def evidence_generator(session: ChatSession, params: Dict[str, Any]) -> ToolResult:
    """
    Find raw WhatsApp messages that directly support a given claim.

    Uses both semantic search (FAISS) and Groq to identify the most
    directly relevant supporting messages.

    Args:
        params: 'claim' (str) — the statement to find evidence for.
    """
    claim: str = params.get("claim", "")
    if not claim:
        return ToolResult(content="No claim provided.", confidence=0.0)

    # Step 1: Semantic retrieval
    chunks = retrieve(claim, session.faiss_index, top_k=3)
    if not chunks:
        return ToolResult(content="No evidence found for this claim.", confidence=0.1)

    # Collect candidate messages from top chunks
    candidate_msgs = []
    for chunk in chunks:
        candidate_msgs.extend(chunk.source_messages)
    candidate_msgs = candidate_msgs[:30]  # Limit to 30 messages for Groq

    # Step 2: Ask Groq to filter to the most direct evidence
    messages_text = "\n".join(
        f"[{m.get('timestamp','')[:10]}] {m.get('name','')}: {m.get('message','')}"
        for m in candidate_msgs
    )
    prompt = EVIDENCE_PROMPT.format(claim=claim, messages=messages_text)

    client = _groq()
    try:
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content.strip()
        # Parse the JSON — it may be an object with an array key
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            evidence_list = parsed
        else:
            # Get the first list value
            evidence_list = next(
                (v for v in parsed.values() if isinstance(v, list)), []
            )
    except Exception as e:
        logger.warning(f"Evidence generator Groq call failed: {e}")
        evidence_list = []

    if not evidence_list:
        # Fall back to chunk citations
        return ToolResult(
            content=f"Found {len(chunks)} potentially relevant message groups for: '{claim}'",
            citations=_chunks_to_citations(chunks),
            confidence=0.5,
        )

    citations = [
        Citation(
            sender=e.get("sender", "Unknown"),
            timestamp=e.get("timestamp", ""),
            message=e.get("message", ""),
        )
        for e in evidence_list[:10]
    ]
    content_lines = [f"**Evidence for:** {claim}\n"]
    for c in citations:
        content_lines.append(f"[{c.timestamp[:10]}] **{c.sender}**: {c.message}")

    return ToolResult(
        content="\n".join(content_lines),
        citations=citations,
        confidence=0.9,
    )


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

TOOL_REGISTRY: Dict[str, Any] = {
    "semantic_search":       semantic_search,
    "contribution_analysis": contribution_analysis,
    "narrative_report":      narrative_report,
    "promise_vs_delivery":   promise_vs_delivery,
    "timeline_search":       timeline_search,
    "member_profile":        member_profile,
    "weekly_summary":        weekly_summary,
    "evidence_generator":    evidence_generator,
}
