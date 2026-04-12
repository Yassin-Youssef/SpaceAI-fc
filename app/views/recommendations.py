"""
SpaceAI FC - Strategy Recommendations Page
"""

import streamlit as st
from app.components.theme import page_header, section_title
from app.components.input_forms import demo_button, analyze_button
from app.components.results_display import (
    check_result, show_recommendations,
)
from app.utils.api_client import get_recommendations, query_knowledge_graph
from app.demo_data import FORMATIONS, SITUATIONS


def render():
    page_header(
        "🎯", "Strategy Recommendations",
        "Get prioritized tactical recommendations based on formation match-ups, "
        "tactical situations, and knowledge-graph analysis.",
    )

    if "rec_result" not in st.session_state:
        st.session_state.rec_result = None
    if "kg_result" not in st.session_state:
        st.session_state.kg_result = None
    if "rec_defaults_loaded" not in st.session_state:
        st.session_state.rec_defaults_loaded = False

    # ── Demo data ─────────────────────────────────────────────────
    col_demo, _ = st.columns([1, 3])
    with col_demo:
        if demo_button("rec_demo"):
            st.session_state.rec_defaults_loaded = True
            st.rerun()

    st.markdown("---")

    # ── Input form ────────────────────────────────────────────────
    c1, c2 = st.columns(2)

    defaults_loaded = st.session_state.rec_defaults_loaded

    with c1:
        st.markdown("**Our team**")
        own_formation = st.selectbox(
            "Formation",
            FORMATIONS,
            index=1 if defaults_loaded else 0,  # 4-2-3-1 for Barca
            key="rec_own_formation",
        )
        team_name = st.text_input(
            "Team name", value="FC Barcelona" if defaults_loaded else "Team A", key="rec_tname"
        )

    with c2:
        st.markdown("**Opponent**")
        opp_formation = st.selectbox(
            "Formation",
            FORMATIONS,
            index=0 if defaults_loaded else 0,  # 4-3-3 for Madrid
            key="rec_opp_formation",
        )
        opp_name = st.text_input(
            "Opponent name", value="Real Madrid" if defaults_loaded else "Team B", key="rec_oname"
        )

    st.markdown("---")
    c3, c4, c5 = st.columns(3)
    with c3:
        situation = st.selectbox(
            "Main tactical situation",
            SITUATIONS,
            index=1 if defaults_loaded else 0,
            key="rec_situation",
            help="The primary tactical challenge you're facing",
        )
    with c4:
        space_control = st.slider(
            "Our space control %", 0, 100,
            45 if defaults_loaded else 50,
            key="rec_space",
        )
    with c5:
        press_score = st.slider(
            "Press resistance score", 0, 100,
            72 if defaults_loaded else 50,
            key="rec_press",
        )

    weakness_text = st.text_area(
        "Known weakness (optional)",
        value="Vulnerable on left flank against rapid transitions" if defaults_loaded else "",
        height=70,
        key="rec_weakness",
        help="Describe a specific vulnerability to get targeted recommendations",
    )

    st.markdown("---")
    if analyze_button("rec_analyze", "🎯 Get Recommendations"):
        _run_analysis(
            own_formation, opp_formation, situation,
            space_control, press_score, weakness_text,
            team_name, opp_name,
        )

    _show_results()


def _run_analysis(own_formation, opp_formation, situation,
                  space_control, press_score, weakness_text,
                  team_name, opp_name):
    # Build minimal analysis data for recommender
    analysis_data = {
        "formation_a": {"formation": own_formation, "confidence": 0.85},
        "formation_b": {"formation": opp_formation, "confidence": 0.85},
        "space_control": {
            "team_a_control": space_control,
            "team_b_control": 100 - space_control,
            "zones": {},
            "midfield": {"team_a": space_control, "team_b": 100 - space_control},
        },
        "press_resistance": {"press_resistance_score": press_score},
        "patterns_a": [],
        "patterns_b": [],
        "roles_a": [],
        "roles_b": [],
        "pass_summary": {"total_passes": 0, "key_distributor": {}},
    }
    if weakness_text:
        analysis_data["weakness_note"] = weakness_text

    with st.spinner("🎯 Computing recommendations..."):
        st.session_state.rec_result = get_recommendations({
            "analysis_data": analysis_data,
            "team_name": team_name,
            "opponent_name": opp_name,
        })

    # Also query knowledge graph
    with st.spinner("🧠 Querying knowledge graph..."):
        st.session_state.kg_result = query_knowledge_graph({
            "formation": own_formation,
            "situation": situation,
        })

    st.rerun()


def _show_results():
    rec_result = st.session_state.get("rec_result")
    kg_result  = st.session_state.get("kg_result")

    if rec_result is None and kg_result is None:
        return

    st.markdown("---")

    # ── Knowledge graph insights ──────────────────────────────────
    if kg_result and kg_result.get("success"):
        section_title("🧠 Knowledge Graph Insights")

        counters = kg_result.get("counter_strategies", [])
        weaknesses = kg_result.get("weaknesses", [])
        strengths = kg_result.get("strengths", [])

        ckg1, ckg2, ckg3 = st.columns(3)
        with ckg1:
            st.markdown("**Counter strategies**")
            if counters:
                for c in counters[:5]:
                    st.markdown(f'<div class="insight-card">→ {c}</div>', unsafe_allow_html=True)
            else:
                st.caption("None found")

        with ckg2:
            st.markdown("**Formation weaknesses**")
            if weaknesses:
                for w in weaknesses[:5]:
                    st.markdown(f'<div class="warning-card">⚠ {w}</div>', unsafe_allow_html=True)
            else:
                st.caption("None found")

        with ckg3:
            st.markdown("**Formation strengths**")
            if strengths:
                for s in strengths[:5]:
                    st.markdown(f'<div class="insight-card">✓ {s}</div>', unsafe_allow_html=True)
            else:
                st.caption("None found")

    # ── Recommendations ───────────────────────────────────────────
    if rec_result:
        if not check_result(rec_result):
            return

        recs = rec_result.get("recommendations", [])
        if recs:
            show_recommendations(recs)
        else:
            st.info("No recommendations generated. Try providing more match context.")
