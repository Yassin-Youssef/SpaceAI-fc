"""
SpaceAI FC - LLM Service
==========================
Handles LLM calls for "Ask SpaceAI", explanation and scouting endpoints.

Priority:
    1. OPENROUTER_API_KEY  (user's OpenRouter account)
    2. ANTHROPIC_API_KEY   (direct Anthropic)
    3. Knowledge-graph fallback (no API key needed)
"""

import json
import re

import httpx

from api.config import (
    OPENROUTER_API_KEY,
    ANTHROPIC_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    ANTHROPIC_MODEL,
)


SYSTEM_PROMPT = (
    "You are SpaceAI FC, an expert football tactical analyst. "
    "You analyse matches using spatial data, pass networks, formations, and tactical patterns. "
    "Respond concisely and professionally. Use football terminology correctly. "
    "Use short paragraphs or bullet points; bold key terms with **double asterisks**. "
    "When match data is provided, ground your answer in the actual numbers. "
    "If no data is available, give general tactical principles."
)


def has_llm() -> bool:
    """Return True if any LLM API key is configured."""
    return bool(OPENROUTER_API_KEY or ANTHROPIC_API_KEY)


def llm_provider() -> str:
    if OPENROUTER_API_KEY:
        return "openrouter"
    if ANTHROPIC_API_KEY:
        return "anthropic"
    return "knowledge_graph"


async def ask_llm(question: str, context: dict = None) -> tuple[str, str]:
    """
    Send a question to the LLM and return (answer, mode).

    mode is "openrouter", "anthropic", or "knowledge_graph".
    A provider failure falls through to the next option so the caller
    always receives an answer.
    """
    if OPENROUTER_API_KEY:
        try:
            return await _call_openrouter(question, context), "openrouter"
        except Exception as exc:
            print(f"[llm] OpenRouter failed: {exc}")

    if ANTHROPIC_API_KEY:
        try:
            return await _call_anthropic(question, context), "anthropic"
        except Exception as exc:
            print(f"[llm] Anthropic failed: {exc}")

    return _knowledge_graph_fallback(question, context), "knowledge_graph"


async def _call_openrouter(question: str, context: dict = None) -> str:
    """Call OpenRouter API (OpenAI-compatible endpoint)."""
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(question, context)},
        ],
        "max_tokens": 1200,
        "temperature": 0.6,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Yassin-Youssef/SpaceAI-fc",
        "X-Title": "SpaceAI FC",
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.post(OPENROUTER_BASE_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_anthropic(question: str, context: dict = None) -> str:
    """Call the Anthropic API directly via the anthropic SDK."""
    import anthropic as ant

    client = ant.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_message(question, context)}],
    )
    return message.content[0].text


def _build_user_message(question: str, context: dict = None) -> str:
    """Format the user message, injecting match context if available."""
    if not context:
        return question

    ctx_str = json.dumps(context, indent=2, default=str)
    if len(ctx_str) > 3000:
        ctx_str = ctx_str[:3000] + "\n... [truncated]"

    return (
        f"Match context:\n```json\n{ctx_str}\n```\n\n"
        f"Question: {question}"
    )


# ── Knowledge-graph fallback ──────────────────────────────────────

# Phrases that map onto knowledge-graph situation nodes
_SITUATION_KEYWORDS = {
    "low_block": ["low block", "deep block", "sit deep", "sitting deep", "compact defence", "compact defense"],
    "park_the_bus": ["park the bus", "parked the bus", "ultra defensive", "ultra-defensive"],
    "high_press": ["high press", "pressing high", "gegenpress", "counter-press", "counterpress", "press high"],
    "counter_attack": ["counter attack", "counter-attack", "counterattack", "on the break", "transition attack"],
    "possession_play": ["possession", "keep the ball", "tiki", "build-up", "build up", "buildup"],
    "midfield_overload": ["midfield overload", "overload the midfield", "numerical advantage", "outnumbered in midfield"],
    "wide_play": ["wide play", "width", "wingers", "flanks", "crosses", "crossing"],
    "high_line": ["high line", "high defensive line", "offside trap"],
    "transition_moment": ["transition", "turnover", "rest defence", "rest defense"],
    "set_piece_threat": ["set piece", "set-piece", "corner", "free kick", "free-kick"],
}

_TOPIC_NOTES = {
    "half-space": (
        "**Half-spaces** are the vertical channels between the centre and the wing. Overloading them "
        "with an inverted winger, an advanced 8 and an overlapping full-back creates 3v2 situations "
        "that a flat back four struggles to cover without dragging a centre-back out of position."
    ),
    "halfspace": None,
    "inverted": (
        "**Inverted full-backs** step into midfield during build-up to form a 2-3 or 3-2 base. "
        "Use them when you need extra bodies against a midfield press or to protect against "
        "counters; avoid them against teams that pin the wide areas with two wingers."
    ),
    "false nine": (
        "A **false nine** drops from the striker position into midfield to create overloads and pull "
        "a centre-back out. It works best when wingers run in behind into the vacated space."
    ),
    "gegenpress": None,
}
_TOPIC_NOTES["halfspace"] = _TOPIC_NOTES["half-space"]
_TOPIC_NOTES["gegenpress"] = (
    "**Counter-pressing** means winning the ball back within ~5 seconds of losing it while the "
    "opponent is still disorganised. It needs compact rest-defence spacing and clear triggers."
)


def _knowledge_graph_fallback(question: str, context: dict = None) -> str:
    """
    Rule-based fallback when no LLM key is available.
    Extracts formations, situations and topics from the question, queries the
    knowledge graph, and composes a structured answer.
    """
    try:
        from engine.intelligence.knowledge_graph import TacticalKnowledgeGraph
        kg = TacticalKnowledgeGraph()
    except Exception:
        return (
            "The tactical knowledge base could not be loaded. "
            "Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY for AI-powered answers."
        )

    q = question.lower()
    sections = []

    # 1. Formations mentioned in the question
    formations = re.findall(r"\b\d(?:-\d){2,3}\b", q)
    for f in dict.fromkeys(formations):
        node = kg.graph.nodes.get(f)
        if not node:
            continue
        lines = [f"**{f}** — {node.get('description', '')}"]
        strengths = kg.get_formation_strengths(f)
        weaknesses = kg.get_formation_weaknesses(f)
        if strengths:
            lines.append("Strong in: " + ", ".join(
                f"{s['situation'].replace('_', ' ')}" for s in strengths))
        if weaknesses:
            lines.append("Vulnerable against: " + ", ".join(
                f"{w['situation'].replace('_', ' ')}" for w in weaknesses))
            counters = []
            for w in weaknesses:
                counters += [c["strategy"].replace("_", " ") for c in kg.get_counter_strategies(w["situation"])]
            if counters:
                lines.append("If you face those scenarios, lean on: " + ", ".join(dict.fromkeys(counters)) + ".")
        sections.append("\n".join(lines))

    # 2. Tactical situations mentioned in the question
    matched_situations = [
        node for node, keys in _SITUATION_KEYWORDS.items() if any(k in q for k in keys)
    ]
    for s in matched_situations:
        node = kg.graph.nodes.get(s, {})
        counters = kg.get_counter_strategies(s)
        lines = [f"**{s.replace('_', ' ').title()}** — {node.get('description', '')}"]
        if counters:
            lines.append("How to counter it:")
            for c in counters:
                lines.append(f"• **{c['strategy'].replace('_', ' ').title()}** — {c['description']}")
        strong = [f for f, _, d in kg.graph.in_edges(s, data=True) if d.get("relation") == "strong_in"]
        weak = [f for f, _, d in kg.graph.in_edges(s, data=True) if d.get("relation") == "weak_against"]
        if strong:
            lines.append("Formations that thrive here: " + ", ".join(strong))
        if weak:
            lines.append("Formations that struggle here: " + ", ".join(weak))
        sections.append("\n".join(lines))

    # 3. Concept notes
    for key, note in _TOPIC_NOTES.items():
        if note and key in q and note not in sections:
            sections.append(note)

    # 4. Ground in supplied match context
    if context:
        ctx_lines = []
        fa = _dig(context, "formation", "team_a_formation") or _dig(context, "formation_a", "formation")
        fb = _dig(context, "formation", "team_b_formation") or _dig(context, "formation_b", "formation")
        if fa or fb:
            ctx_lines.append(f"Detected shapes: {fa or '?'} vs {fb or '?'}.")
        ca = _dig(context, "space_control", "team_a_control") or context.get("team_a_control")
        if ca is not None:
            ctx_lines.append(f"Territorial control for your side: {ca}%.")
        pr = _dig(context, "press_resistance", "press_resistance_score") or context.get("press_resistance_score")
        if pr is not None:
            ctx_lines.append(f"Press resistance score: {pr}/100.")
        if ctx_lines:
            sections.insert(0, "**From your current analysis:** " + " ".join(ctx_lines))

    if sections:
        return (
            "\n\n".join(sections)
            + "\n\n_Answered from the built-in tactical knowledge graph. "
              "Add OPENROUTER_API_KEY or ANTHROPIC_API_KEY for full AI answers._"
        )

    # Generic guidance when nothing matched
    try:
        formations_known = ", ".join(
            n["name"] if isinstance(n, dict) else str(n) for n in kg.get_all_nodes("formation")
        )
    except Exception:
        formations_known = "4-3-3, 4-2-3-1, 3-5-2"
    situations_known = ", ".join(n.replace("_", " ") for n in _SITUATION_KEYWORDS)
    return (
        "I can answer from the built-in tactical knowledge graph without an AI key.\n\n"
        "Try asking about a **formation** (" + formations_known + ") "
        "or a **situation** (" + situations_known + "), for example:\n"
        "• How do I beat a low block?\n"
        "• What are the weaknesses of a 4-3-3?\n"
        "• Which formations thrive under a high press?\n\n"
        "*Set an OpenRouter or Anthropic API key on the backend for open-ended answers.*"
    )


def _dig(obj, *keys):
    cur = obj
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur
