"""
SpaceAI FC - Tactical Patterns Page
"""

import streamlit as st
from app.components.theme import page_header, section_title
from app.components.input_forms import (
    player_table, team_meta, demo_button, analyze_button, dataset_input_tab,
)
from app.components.results_display import (
    check_result, show_visualizations, show_patterns, download_image_button,
)
from app.utils.api_client import analyze_patterns
from app.demo_data import BARCA_PLAYERS, MADRID_PLAYERS


def render():
    page_header(
        "🔍", "Tactical Pattern Detection",
        "Detect overlapping runs, compact blocks, wide overloads, "
        "high/low defensive lines, and other tactical patterns.",
    )

    if "pt_result" not in st.session_state:
        st.session_state.pt_result = None
    if "pt_a" not in st.session_state:
        st.session_state.pt_a = None
    if "pt_b" not in st.session_state:
        st.session_state.pt_b = None

    tab_manual, tab_dataset = st.tabs(["✏️ Manual Entry", "📂 Dataset Upload"])

    with tab_manual:
        col_demo, _ = st.columns([1, 3])
        with col_demo:
            if demo_button("pt_demo"):
                st.session_state.pt_a = BARCA_PLAYERS
                st.session_state.pt_b = MADRID_PLAYERS
                st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            team_a_name, team_a_color = team_meta("pt_a", "FC Barcelona", "#a50044")
        with c2:
            team_b_name, team_b_color = team_meta("pt_b", "Real Madrid", "#ffffff")

        analyze_team = st.radio(
            "Analyze patterns for",
            ["Both teams", "Team A only", "Team B only"],
            horizontal=True,
            key="pt_which",
        )
        team_map = {"Both teams": "both", "Team A only": "a", "Team B only": "b"}

        st.markdown("---")
        ca, cb = st.columns(2)
        with ca:
            players_a = player_table(
                f"{team_a_name} Players",
                key_prefix="pt_pa",
                default_players=st.session_state.pt_a or BARCA_PLAYERS,
            )
        with cb:
            players_b = player_table(
                f"{team_b_name} Players",
                key_prefix="pt_pb",
                default_players=st.session_state.pt_b or MADRID_PLAYERS,
            )

        st.markdown("---")
        if analyze_button("pt_analyze", "⚽ Detect Patterns"):
            _run_analysis(
                players_a, players_b,
                team_a_name, team_b_name,
                team_a_color, team_b_color,
                team_map[analyze_team],
            )

    with tab_dataset:
        ds = dataset_input_tab("pt_ds")
        if ds.get("file_bytes") and analyze_button("pt_analyze_ds", "⚽ Analyze Dataset"):
            import tempfile
            from pathlib import Path
            tmp = Path(tempfile.mktemp(suffix=Path(ds["filename"]).suffix))
            tmp.write_bytes(ds["file_bytes"])
            with st.spinner("🔍 Detecting patterns..."):
                st.session_state.pt_result = analyze_patterns({
                    "input_type": "dataset", "dataset_file": str(tmp),
                    "team_a_name": "Team A", "team_b_name": "Team B",
                    "team_a_color": "#e74c3c", "team_b_color": "#3498db",
                    "analyze_team": "both",
                })
            st.rerun()

    _show_results()


def _run_analysis(players_a, players_b, team_a_name, team_b_name,
                  team_a_color, team_b_color, analyze_team):
    with st.spinner("🔍 Detecting tactical patterns..."):
        st.session_state.pt_result = analyze_patterns({
            "input_type": "manual",
            "team_a": players_a,
            "team_b": players_b,
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
            "team_a_color": team_a_color,
            "team_b_color": team_b_color,
            "analyze_team": analyze_team,
        })
    st.rerun()


def _show_results():
    result = st.session_state.get("pt_result")
    if result is None:
        return
    if not check_result(result):
        return

    st.markdown("---")

    show_visualizations(result.get("visualizations", []))

    patterns_a = result.get("team_a_patterns", [])
    patterns_b = result.get("team_b_patterns", [])

    if patterns_a:
        show_patterns(patterns_a, "Team A")
    if patterns_b:
        show_patterns(patterns_b, "Team B")

    if not patterns_a and not patterns_b:
        st.info("No pattern data returned. Check that both teams have valid player positions.")

    visuals = result.get("visualizations", [])
    if visuals:
        st.markdown("---")
        download_image_button(visuals[0], key="pt_dl")
