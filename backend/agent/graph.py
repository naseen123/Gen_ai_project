"""
graph.py — LangGraph state machine for TeamLens AI agent.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, Any, Literal, TypedDict, List
from agent.tools import Citation

from langgraph.graph import StateGraph, START, END

from agent.prompts import (
    ROUTER_SYSTEM_PROMPT,
    ROUTER_USER_PROMPT_TEMPLATE,
    SYNTHESIZER_SYSTEM_PROMPT,
    SYNTHESIZER_USER_PROMPT_TEMPLATE,
)
from agent.tools import TOOL_REGISTRY, _groq

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    session: Any
    history: str
    question: str
    tool_name: str
    tool_params: dict
    tool_output: str
    citations: List[Citation]
    confidence: float
    answer: str


def router_node(state: AgentState) -> AgentState:
    logger.info(f"Router node processing question: {state['question'][:50]}...")
    client = _groq()

    prompt = ROUTER_USER_PROMPT_TEMPLATE.format(
        history=state["history"],
        question=state["question"],
    )

    try:
        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content.strip()
        parsed = json.loads(raw)
        tool_name = parsed.get("tool", "semantic_search")
        reason = parsed.get("reason", "No reason provided")
        logger.info(f"Router chose '{tool_name}' because: {reason}")
    except Exception as e:
        logger.warning(f"Router LLM call failed ({e}), defaulting to semantic_search.")
        tool_name = "semantic_search"

    if tool_name not in TOOL_REGISTRY:
        logger.warning(f"Invalid tool '{tool_name}', defaulting to semantic_search.")
        tool_name = "semantic_search"

    params = {"query": state["question"]}
    if tool_name in ("member_profile", "promise_vs_delivery"):
        params["member_name"] = state["question"]
    if tool_name == "evidence_generator":
        params["claim"] = state["question"]

    return {"tool_name": tool_name, "tool_params": params}


def executor_node(state: AgentState) -> AgentState:
    tool_name = state["tool_name"]
    logger.info(f"Executor node running tool: {tool_name}")

    tool_func = TOOL_REGISTRY[tool_name]
    result = tool_func(state["session"], state["tool_params"])

    return {"tool_output": result.content, "citations": result.citations, "confidence": result.confidence}


def synthesizer_node(state: AgentState) -> AgentState:
    logger.info("Synthesizer node composing final answer.")
    client = _groq()

    evidence = ""
    if state["citations"]:
        lines = [f"[{c.timestamp[:10]}] {c.sender}: {c.message}" for c in state["citations"]]
        evidence = "\n".join(lines)
    else:
        evidence = "No specific source messages retrieved."

    safe_history = state.get("history") or ""
    safe_output = str(state.get("tool_output") or "")
    
    prompt = SYNTHESIZER_USER_PROMPT_TEMPLATE.format(
        question=state.get("question", ""),
        tool_name=state.get("tool_name", ""),
        tool_output=safe_output[:3000],
        evidence=evidence[:3000],
        history=safe_history[-2000:],
    )

    try:
        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYNTHESIZER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=800,
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Synthesizer LLM call failed: {e}")
        answer = f"I encountered an error. Raw data:\n\n{state['tool_output']}"

    return {"answer": answer}


def build_agent_graph() -> Any:
    workflow = StateGraph(AgentState)

    workflow.add_node("router", router_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.add_edge(START, "router")
    workflow.add_edge("router", "executor")
    workflow.add_edge("executor", "synthesizer")
    workflow.add_edge("synthesizer", END)

    return workflow.compile()