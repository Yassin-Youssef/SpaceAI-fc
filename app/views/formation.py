"""
SpaceAI FC - Formation Detection Page
"""

import streamlit as st
from app.components.theme import page_header, section_title
from app.components.input_forms import (
    player_table, team_meta, demo_button, analyze_button, dataset_input_tab,
)
from app.components.results_display import (
    check_result, show_visualizations, metric_row, download_image_button, show_formation_result,
)
from app.utils.api_client import analyze_formation
from app.demo_data import BARCA_PLAYERS, MADRID_PLAYERS


def render():
    page_header(
        "📐", "Formation Detection",
        "Automatically detect team formations using clustering and gap-based analysis. "
        "Identifies defensive, midfield, and attacking lines.",
    )

    if "fm_result" not in st.session_state:
        st.session_state.fm_result = None
    if "fm_a" not in st.session_state:
        st.session_state.fm_a = None
    if "fm_b" not in st.session_state:
        st.session_state.fm_b = None

    tab_manual, tab_dataset = st.tabs(["✏️ Manual Entry", "📂 Dataset Upload"])

    with tab_manual:
        col_demo, _ = st.columns([1, 3])
        with col_demo:
            if demo_button("fm_demo"):
                st.session_state.fm_a = BARCA_PLAYERS
                st.session_state.fm_b = MADRID_PLAYERS
                st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            team_a_name, team_a_color = team_meta("fm_a", "FC Barcelona", "#a50044")
        with c2:
            team_b_name, team_b_color = team_meta("fm_b", "Real Madrid", "#ffffff")

        method = st.selectbox(
            "Detection method",
            ["auto", "clustering", "gap"],
            key="fm_method",
            help="auto = clustering if scikit-learn available, else gap-based",
        )

        st.markdown("---")
        ca, cb = st.columns(2)
        with ca:
            players_a = player_table(
                f"{team_a_name} Players",
                key_prefix="fm_pa",
                default_players=st.session_state.fm_a or BARCA_PLAYERS,
            )
        with cb:
            players_b = player_table(
                f"{team_b_name} Players",
                key_prefix="fm_pb",
                default_players=st.session_state.fm_b or MADRID_PLAYERS,
            )

        st.markdown("---")
        if analyze_button("fm_analyze", "⚽ Detect Formations"):
            _run_analysis(
                players_a, players_b,
                team_a_name, team_b_name,
                team_a_color, team_b_color,
                method,
            )

    with tab_dataset:
        ds = dataset_input_tab("fm_ds")
        if ds.get("file_bytes") and analyze_button("fm_analyze_ds", "⚽ Analyze Dataset"):
            import tempfile
            from pathlib import Path
            tmp = Path(tempfile.mktemp(suffix=Path(ds["filename"]).suffix))
            tmp.write_bytes(ds["file_bytes"])
            with st.spinner("📐 Detecting formations..."):
                st.session_state.fm_result = analyze_formation({
                    "input_type": "dataset", "dataset_file": str(tmp),
                    "team_a_name": "Team A", "team_b_name": "Team B",
                    "team_a_color": "#e74c3c", "team_b_color": "#3498db",
                    "method": "auto",
                })
            st.rerun()

    _show_results()


def _run_analysis(players_a, players_b, team_a_name, team_b_name,
                  team_a_color, team_b_color, method):
    with st.spinner("📐 Detecting formations..."):
        st.session_state.fm_result = analyze_formation({
            "input_type": "manual",
            "team_a": players_a,
            "team_b": players_b,
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
            "team_a_color": team_a_color,
            "team_b_color": team_b_color,
            "method": method,
        })
    st.rerun()


def _show_results():
    result = st.session_state.get("fm_result")
    if result is None:
        return
    if not check_result(result):
        return

    st.markdown("---")
    show_formation_result(result, "Team A", "Team B")

    show_visualizations(result.get("visualizations", []), cols=2)

    # Line groupings
    for team_key, team_label in [("team_a", "Team A"), ("team_b", "Team B")]:
        lines = result.get(f"{team_key}_lines", [])
        if lines:
            section_title(f"🧩 {team_label} — Line Groupings")
            line_names = ["DEF", "MID", "MID2", "ATT"]
            for idx, line in enumerate(lines):
                name = line_names[idx] if idx < len(line_names) else f"Line {idx+1}"
                players_in_line = [f"#{p['number']} {p['name']}" for p in line]
                st.markdown(
                    f'<div class="insight-card">'
                    f'<strong>{name}</strong>: {" · ".join(players_in_line)}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # Downloads
    visuals = result.get("visualizations", [])
    if visuals:
        st.markdown("---")
        cols = st.columns(min(len(visuals), 2))
        for i, viz in enumerate(visuals[:2]):
            with cols[i]:
                download_image_button(viz, key=f"fm_dl_{i}")
