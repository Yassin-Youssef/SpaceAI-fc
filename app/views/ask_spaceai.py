"""
SpaceAI FC - Ask SpaceAI Page
================================
Feature 9: Chat-style Q&A about football tactics.
Uses OpenRouter LLM or knowledge graph fallback.
"""

import streamlit as st
from app.components.theme import page_header, section_title
from app.components.input_forms import demo_button
from app.utils.llm_client import call_openrouter, is_llm_available


SYSTEM_PROMPT = (
    "You are SpaceAI FC, a professional football tactical intelligence system. "
    "You are an expert in football tactics, formations, player roles, pressing "
    "systems, space control, and match strategy. Answer with clear, specific, "
    "actionable advice. Reference formations, player roles, and tactical concepts. "
    "Be concise but thorough. Use markdown formatting."
)

EXAMPLE_QUESTIONS = [
    "How do you break down a low block defense?",
    "What are the weaknesses of a 4-3-3?",
    "How should I set up against high pressing?",
    "What adjustments when losing 0-1 at halftime?",
    "Explain half-space overloads",
]


def render():
    page_header(
        "💬", "Ask SpaceAI",
        "Ask anything about football tactics — formations, strategies, player roles, "
        "pressing systems, and match management.",
    )

    # ── Session state ─────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ── LLM availability notice ───────────────────────────────────
    if is_llm_available():
        st.markdown(
            '<div style="display:inline-block;background:#1B5E20;color:#FFD700;'
            'padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;'
            'margin-bottom:16px">🟢 AI Mode — Claude Sonnet</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="display:inline-block;background:#FFF8E1;color:#E65100;'
            'padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;'
            'margin-bottom:16px">📚 Knowledge Graph Mode — Set OPENROUTER_API_KEY for AI</div>',
            unsafe_allow_html=True,
        )

    # ── Example questions ─────────────────────────────────────────
    st.markdown("**Try these examples:**")
    example_cols = st.columns(len(EXAMPLE_QUESTIONS))
    example_clicked = None
    for idx, q in enumerate(EXAMPLE_QUESTIONS):
        with example_cols[idx]:
            if st.button(q[:30] + "…" if len(q) > 30 else q, key=f"ex_{idx}",
                         help=q, use_container_width=True):
                example_clicked = q

    st.markdown("---")

    # ── Optional match context ────────────────────────────────────
    include_context = st.checkbox("Include match context", key="ask_ctx_check")
    match_context = None
    if include_context:
        with st.expander("Match Context", expanded=True):
            ctx_c1, ctx_c2 = st.columns(2)
            with ctx_c1:
                our_form = st.selectbox("Our formation",
                    ["4-3-3", "4-2-3-1", "3-5-2", "4-4-2", "5-4-1", "5-3-2", "4-1-4-1", "3-4-3"],
                    key="ask_our_form")
                score_ours = st.number_input("Our score", 0, 20, 0, key="ask_score_ours")
            with ctx_c2:
                opp_form = st.selectbox("Opponent formation",
                    ["4-3-3", "4-2-3-1", "3-5-2", "4-4-2", "5-4-1", "5-3-2", "4-1-4-1", "3-4-3"],
                    key="ask_opp_form")
                score_opp = st.number_input("Opponent score", 0, 20, 0, key="ask_score_opp")
            minute = st.slider("Match minute", 0, 120, 45, key="ask_minute")
            match_context = {
                "our_formation": our_form,
                "opponent_formation": opp_form,
                "our_score": score_ours,
                "opponent_score": score_opp,
                "minute": minute,
            }

    # ── Question input ────────────────────────────────────────────
    question = st.text_area(
        "Ask anything about football tactics...",
        value=example_clicked or "",
        height=100,
        key="ask_question",
        placeholder="e.g., What's the best way to exploit space behind a high defensive line?",
    )

    col_ask, col_clear = st.columns([3, 1])
    with col_ask:
        ask_clicked = st.button("💬 Ask SpaceAI", key="ask_submit",
                                type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑️ Clear History", key="ask_clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    if ask_clicked and question.strip():
        _process_question(question.strip(), match_context)

    # ── Chat history ──────────────────────────────────────────────
    _show_chat_history()


def _process_question(question: str, match_context: dict | None):
    """Process the question using LLM or knowledge graph fallback."""
    with st.spinner("🧠 Thinking..."):

        # Build context string
        context_str = ""
        if match_context:
            context_str = (
                f"\n\nMatch Context:\n"
                f"- Our formation: {match_context.get('our_formation', '?')}\n"
                f"- Opponent formation: {match_context.get('opponent_formation', '?')}\n"
                f"- Score: {match_context.get('our_score', 0)}-{match_context.get('opponent_score', 0)}\n"
                f"- Minute: {match_context.get('minute', 0)}"
            )

        full_question = question + context_str

        # Try LLM
        llm_answer = call_openrouter(SYSTEM_PROMPT, full_question)

        if llm_answer:
            answer = llm_answer
            mode = "ai"
        else:
            # Knowledge graph fallback
            answer = _knowledge_graph_fallback(question)
            mode = "knowledge_graph"

    # Add to history
    st.session_state.chat_history.append({
        "question": question,
        "answer": answer,
        "mode": mode,
        "context": match_context,
    })
    st.rerun()


def _knowledge_graph_fallback(question: str) -> str:
    """Query the engine's knowledge graph for a template response."""
    try:
        from engine.intelligence.knowledge_graph import TacticalKnowledgeGraph
        kg = TacticalKnowledgeGraph()

        q_lower = question.lower()
        answer_parts = []

        # Try to match formations
        formations = ["4-3-3", "4-2-3-1", "3-5-2", "4-4-2", "5-4-1", "5-3-2", "4-1-4-1", "3-4-3"]
        matched_formation = None
        for f in formations:
            if f in q_lower:
                matched_formation = f
                break

        # Try to match situations
        situations = {
            "low block": "low_block", "high press": "high_press",
            "counter": "counter_attack", "possession": "possession_play",
            "wide play": "wide_play", "overload": "midfield_overload",
            "park the bus": "park_the_bus", "high line": "high_line",
            "transition": "transition_moment", "set piece": "set_piece_threat",
        }
        matched_situation = None
        for key, val in situations.items():
            if key in q_lower:
                matched_situation = val
                break

        if matched_formation:
            weaknesses = kg.get_formation_weaknesses(matched_formation)
            strengths = kg.get_formation_strengths(matched_formation)
            if weaknesses:
                answer_parts.append(f"**{matched_formation} Weaknesses:**")
                for w in weaknesses:
                    answer_parts.append(f"- ⚠️ {w['situation'].replace('_', ' ').title()}: {w['description']}")
            if strengths:
                answer_parts.append(f"\n**{matched_formation} Strengths:**")
                for s in strengths:
                    answer_parts.append(f"- ✅ {s['situation'].replace('_', ' ').title()}: {s['description']}")

        if matched_situation:
            counters = kg.get_counter_strategies(matched_situation)
            if counters:
                answer_parts.append(f"\n**Counter Strategies for {matched_situation.replace('_', ' ').title()}:**")
                for c in counters:
                    answer_parts.append(f"- 🎯 {c['strategy'].replace('_', ' ').title()}: {c['description']}")

        if matched_formation and matched_situation:
            result = kg.query(matched_formation, matched_situation)
            if result["is_weak_against"]:
                answer_parts.append(f"\n⚠️ **{matched_formation}** is **weak against** {matched_situation.replace('_', ' ')}.")
            if result["is_strong_in"]:
                answer_parts.append(f"\n✅ **{matched_formation}** is **strong in** {matched_situation.replace('_', ' ')}.")

        if answer_parts:
            return "\n".join(answer_parts) + "\n\n---\n*Response from SpaceAI FC Knowledge Graph*"

        # Generic fallback
        return (
            "I can help with tactical questions about football formations, "
            "situations, and strategies.\n\n"
            "**Try mentioning:**\n"
            "- A formation (e.g., 4-3-3, 4-2-3-1, 3-5-2)\n"
            "- A tactical situation (e.g., low block, high press, counter attack)\n"
            "- Both for specific matchup advice\n\n"
            "**For AI-powered free-form answers**, set your `OPENROUTER_API_KEY` "
            "environment variable.\n\n"
            "---\n*Knowledge Graph Mode — Set OPENROUTER_API_KEY for AI-powered answers*"
        )

    except Exception:
        return (
            "Unable to query the knowledge graph. Please ensure the engine is properly installed.\n\n"
            "Set your `OPENROUTER_API_KEY` environment variable for AI-powered responses."
        )


def _show_chat_history():
    """Render the chat history as styled bubbles."""
    history = st.session_state.get("chat_history", [])
    if not history:
        return

    st.markdown("---")
    section_title("💬 Conversation")

    for i, entry in enumerate(reversed(history)):
        q = entry["question"]
        a = entry["answer"]
        mode = entry.get("mode", "knowledge_graph")
        mode_label = "🤖 AI" if mode == "ai" else "📚 Knowledge Graph"

        # User question (right-aligned)
        st.markdown(
            f'<div style="display:flex;justify-content:flex-end;margin-bottom:8px">'
            f'<div style="background:linear-gradient(135deg,#1B5E20,#2E7D32);color:white;'
            f'padding:14px 20px;border-radius:12px 12px 0 12px;max-width:75%;'
            f'font-size:0.95rem;line-height:1.5;box-shadow:0 2px 8px rgba(27,94,32,0.15)">'
            f'{q}'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # SpaceAI answer (left-aligned)
        st.markdown(
            f'<div style="display:flex;justify-content:flex-start;margin-bottom:4px">'
            f'<div style="background:white;color:#333;'
            f'padding:14px 20px;border-radius:12px 12px 12px 0;max-width:85%;'
            f'font-size:0.95rem;line-height:1.6;border:1px solid #C8E6C9;'
            f'box-shadow:0 2px 8px rgba(0,0,0,0.06)">'
            f'<div style="font-size:0.7rem;color:#888;margin-bottom:8px;'
            f'font-weight:600;letter-spacing:0.5px">⚽ SpaceAI FC · {mode_label}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        # Render markdown content separately for proper formatting
        st.markdown(a)

        if i < len(history) - 1:
            st.markdown(
                '<div style="border-top:1px solid #E8F5E9;margin:16px 0"></div>',
                unsafe_allow_html=True,
            )
