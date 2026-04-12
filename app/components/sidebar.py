"""
SpaceAI FC - Sidebar Navigation
=================================
Renders the left sidebar with logo, feature navigation, and status indicator.
"""

import streamlit as st
from app.utils.api_client import health_check

PAGES = {
    "🏟️  Full Match Analysis": "full_analysis",
    "🔗  Pass Network":        "pass_network",
    "🗺️  Space Control":       "space_control",
    "📐  Formation Detection": "formation",
    "💪  Press Resistance":    "press_resistance",
    "🔍  Tactical Patterns":   "patterns",
    "🎯  Strategy Recommendations": "recommendations",
    "👤  Player Assessment":    "player_assessment",
    "💬  Ask SpaceAI":          "ask_spaceai",
    "⚖️  Compare":             "compare",
    "🎮  Simulation":           "simulation",
    "📝  Tactical Explanation": "explanation",
}


def render_sidebar() -> str:
    """
    Render the full sidebar and return the key of the selected page
    (e.g., "pass_network").
    """
    with st.sidebar:
        # ── Logo ──────────────────────────────────────────────────
        st.markdown(
            """
            <div class="logo-container">
                <div class="logo-title">⚽ SpaceAI FC</div>
                <div class="logo-subtitle">Tactical Intelligence</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # ── Navigation ────────────────────────────────────────────
        st.markdown(
            '<p style="color:rgba(255,255,255,0.6);font-size:0.75rem;'
            'letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;">'
            "FEATURES</p>",
            unsafe_allow_html=True,
        )

        selected_label = st.radio(
            label="nav",
            options=list(PAGES.keys()),
            label_visibility="collapsed",
        )
        selected_page = PAGES[selected_label]

        st.markdown("---")

        # ── API Status ────────────────────────────────────────────
        status = health_check()
        if status.get("status") == "ok":
            st.markdown(
                '<p style="color:#A5D6A7;font-size:0.8rem;">🟢 Engine online — v'
                + status.get("version", "4.0")
                + "</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p style="color:#EF9A9A;font-size:0.8rem;">🔴 Engine offline</p>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p style="color:rgba(255,255,255,0.5);font-size:0.72rem;">'
                "Run: uvicorn api.main:app --reload --port 8000</p>",
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # ── About ─────────────────────────────────────────────────
        st.markdown(
            """
            <p style="color:rgba(255,255,255,0.5);font-size:0.72rem;line-height:1.5;">
            SpaceAI FC v4.0<br>
            Agentic Tactical Intelligence<br>
            Sense → Understand → Reason<br>
            → Act → Explain
            </p>
            """,
            unsafe_allow_html=True,
        )

    return selected_page
