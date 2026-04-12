"""
SpaceAI FC - LLM Service
==========================
Handles LLM calls for "Ask SpaceAI" and explanation endpoints.

Priority:
    1. OPENROUTER_API_KEY  (user's OpenRouter account)
    2. ANTHROPIC_API_KEY   (direct Anthropic)
    3. Knowledge-graph template fallback (no API key needed)
"""

import json
import os
import httpx

from api.config import (
    OPENROUTER_API_KEY,
    ANTHROPIC_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
)


SYSTEM_PROMPT = (
    "You are SpaceAI FC, an expert football tactical analyst. "
    "You analyse matches using spatial data, pass networks, formations, and tactical patterns. "
    "Respond concisely and professionally. Use football terminology correctly. "
    "When match data is provided, ground your answer in the actual numbers. "
    "If no data is available, give general tactical principles."
)


def has_llm() -> bool:
    """Return True if any LLM API key is configured."""
    return bool(OPENROUTER_API_KEY or ANTHROPIC_API_KEY)


async def ask_llm(question: str, context: dict = None) -> tuple[str, str]:
    """
    Send a question to the LLM and return (answer, mode).

    mode is "openrouter", "anthropic", or "knowledge_graph".
    """
    if OPENROUTER_API_KEY:
        answer = await _call_openrouter(question, context)
        return answer, "openrouter"

    if ANTHROPIC_API_KEY:
        answer = await _call_anthropic(question, context)
        return answer, "anthropic"

    answer = _knowledge_graph_fallback(question, context)
    return answer, "knowledge_graph"


async def _call_openrouter(question: str, context: dict = None) -> str:
    """Call OpenRouter API (Claude via OpenAI-compatible endpoint)."""
    user_content = _build_user_message(question, context)

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://spaceaifc.local",
        "X-Title": "SpaceAI FC",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(OPENROUTER_BASE_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_anthropic(question: str, context: dict = None) -> str:
    """Call Anthropic API directly via the anthropic SDK."""
    try:
        import anthropic as ant
    except ImportError:
        return _knowledge_graph_fallback(question, context)

    user_content = _build_user_message(question, context)

    client = ant.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    return message.content[0].text


def _build_user_message(question: str, context: dict = None) -> str:
    """Format the user message, injecting match context if available."""
    if not context:
        return question

    ctx_str = json.dumps(context, indent=2, default=str)
    # Truncate very long context to avoid token limits
    if len(ctx_str) > 3000:
        ctx_str = ctx_str[:3000] + "\n... [truncated]"

    return (
        f"Match context:\n```json\n{ctx_str}\n```\n\n"
        f"Question: {question}"
    )


def _knowledge_graph_fallback(question: str, context: dict = None) -> str:
    """
    Rule-based fallback when no LLM key is available.
    Queries the knowledge graph and returns a structured text response.
    """
    try:
        from engine.intelligence.knowledge_graph import TacticalKnowledgeGraph
        kg = TacticalKnowledgeGraph()

        q_lower = question.lower()
        parts = []

        # Try to detect what the user is asking about
        formation_keywords = ["4-3-3", "4-2-3-1", "3-5-2", "4-4-2", "5-3-2", "5-4-1",
                              "3-4-3", "4-1-4-1"]
        for f in formation_keywords:
            if f in q_lower:
                try:
                    weaknesses = kg.get_formation_weaknesses(f)
                    if weaknesses:
                        w_strs = [w["situation"] if isinstance(w, dict) else str(w) for w in weaknesses[:3]]
                        parts.append(f"Weaknesses of {f}: {', '.join(w_strs)}.")
                except Exception:
                    pass
                try:
                    counters = kg.get_counter_strategies(f)
                    if counters:
                        c_strs = [c["strategy"] if isinstance(c, dict) else str(c) for c in counters[:3]]
                        parts.append(f"Counter strategies: {', '.join(c_strs)}.")
                except Exception:
                    pass

        if parts:
            return (
                "Based on the tactical knowledge base:\n\n"
                + "\n".join(parts)
                + "\n\n(Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY for AI-powered answers.)"
            )

        # Generic fallback
        return (
            f"I understand you're asking: '{question}'\n\n"
            "To provide a detailed AI-powered answer, please set the OPENROUTER_API_KEY "
            "or ANTHROPIC_API_KEY environment variable.\n\n"
            "With the current knowledge base, I can answer questions about specific "
            "formations (e.g. '4-3-3'), tactical situations, and counter-strategies."
        )

    except Exception:
        return (
            "The tactical knowledge base is unavailable. "
            "Please set OPENROUTER_API_KEY for AI-powered answers."
        )
