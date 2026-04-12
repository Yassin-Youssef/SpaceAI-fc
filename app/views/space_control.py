"""
SpaceAI FC - Space Control Page
"""

import streamlit as st
from app.components.theme import page_header, section_title
from app.components.input_forms import (
    player_table, team_meta, demo_button, analyze_button,
    video_input_tab, dataset_input_tab,
)
from app.components.results_display import (
    check_result, show_visualizations, metric_row, download_image_button,
)
from app.utils.api_client import analyze_space_control
from app.demo_data import BARCA_PLAYERS, MADRID_PLAYERS


def render():
    page_header(
        "🗺️", "Space Control Analysis",
        "Map territorial dominance using Voronoi tessellation and Gaussian influence models. "
        "See which team controls each zone of the pitch.",
    )

    if "sc_result" not in st.session_state:
        st.session_state.sc_result = None
    if "sc_a" not in st.session_state:
        st.session_state.sc_a = None
    if "sc_b" not in st.session_state:
        st.session_state.sc_b = None

    tab_manual, tab_video, tab_dataset = st.tabs(
        ["✏️ Manual Entry", "🎬 Video / YouTube", "📂 Dataset Upload"]
    )

    with tab_manual:
        col_demo, _ = st.columns([1, 3])
        with col_demo:
            if demo_button("sc_demo"):
                st.session_state.sc_a = BARCA_PLAYERS
                st.session_state.sc_b = MADRID_PLAYERS
                st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            team_a_name, team_a_color = team_meta("sc_a", "FC Barcelona", "#a50044")
        with c2:
            team_b_name, team_b_color = team_meta("sc_b", "Real Madrid", "#ffffff")

        st.markdown("---")
        c_ball1, c_ball2, c_mode = st.columns([1, 1, 2])
        ball_x = c_ball1.number_input("Ball X", 0.0, 120.0, 60.0, 0.5, key="sc_bx")
        ball_y = c_ball2.number_input("Ball Y", 0.0, 80.0, 40.0, 0.5, key="sc_by")
        mode = c_mode.selectbox(
            "Visualisation mode",
            ["both", "voronoi", "influence"],
            key="sc_mode",
            help="Voronoi = nearest player; Influence = Gaussian decay",
        )

        st.markdown("---")
        ca, cb = st.columns(2)
        with ca:
            players_a = player_table(
                f"{team_a_name} Players",
                key_prefix="sc_pa",
                default_players=st.session_state.sc_a or BARCA_PLAYERS,
            )
        with cb:
            players_b = player_table(
                f"{team_b_name} Players",
                key_prefix="sc_pb",
                default_players=st.session_state.sc_b or MADRID_PLAYERS,
            )

        st.markdown("---")
        if analyze_button("sc_analyze", "⚽ Compute Space Control"):
            _run_analysis(players_a, players_b, team_a_name, team_b_name,
                          team_a_color, team_b_color, ball_x, ball_y, mode)

    with tab_dataset:
        ds = dataset_input_tab("sc_ds")
        if ds.get("file_bytes") and analyze_button("sc_analyze_ds", "⚽ Analyze Dataset"):
            import tempfile
            from pathlib import Path
            tmp = Path(tempfile.mktemp(suffix=Path(ds["filename"]).suffix))
            tmp.write_bytes(ds["file_bytes"])
            payload = {
                "input_type": "dataset", "dataset_file": str(tmp),
                "team_a_name": "Team A", "team_b_name": "Team B",
                "team_a_color": "#e74c3c", "team_b_color": "#3498db",
                "ball_x": 60.0, "ball_y": 40.0, "mode": "both",
            }
            with st.spinner("🗺️ Computing space control..."):
                st.session_state.sc_result = analyze_space_control(payload)
            st.rerun()

    with tab_video:
        st.info("Video mode extracts positions from video then computes space control.")
        st.caption("Upload a video or use demo mode below.")
        vid = video_input_tab("sc_vid")
        if analyze_button("sc_analyze_vid", "⚽ Process & Analyze"):
            from app.utils.api_client import upload_video, process_youtube
            with st.spinner("🎬 Processing video..."):
                if vid["source"] == "file":
                    tracking = upload_video(vid["file_bytes"], vid["filename"])
                elif vid["source"] == "youtube":
                    tracking = process_youtube(vid["url"], demo_mode=vid.get("demo_mode", True))
                else:
                    st.warning("Please provide a video source.")
                    tracking = None
            if tracking and tracking.get("success"):
                td = tracking["tracking_data"]
                _run_analysis(
                    td.get("team_a", BARCA_PLAYERS), td.get("team_b", MADRID_PLAYERS),
                    "Team A", "Team B", "#e74c3c", "#3498db", 60.0, 40.0, "both",
                )

    _show_results()


def _run_analysis(players_a, players_b, team_a_name, team_b_name,
                  team_a_color, team_b_color, ball_x, ball_y, mode):
    payload = {
        "input_type": "manual",
        "team_a": players_a,
        "team_b": players_b,
        "team_a_name": team_a_name,
        "team_b_name": team_b_name,
        "team_a_color": team_a_color,
        "team_b_color": team_b_color,
        "ball_x": ball_x,
        "ball_y": ball_y,
        "mode": mode,
    }
    with st.spinner("🗺️ Computing space control..."):
        st.session_state.sc_result = analyze_space_control(payload)
    st.rerun()


def _show_results():
    result = st.session_state.get("sc_result")
    if result is None:
        return
    if not check_result(result):
        return

    st.markdown("---")
    section_title("📊 Space Control Results")

    a_ctrl = result.get("team_a_control", 0)
    b_ctrl = result.get("team_b_control", 0)
    mid = result.get("midfield_control", {})
    zones = result.get("zones", {})

    # Overall metrics
    metric_row([
        ("Team A Control", f"{a_ctrl:.1f}%"),
        ("Team B Control", f"{b_ctrl:.1f}%"),
        ("Midfield (A)", f"{mid.get('team_a', 0):.1f}%"),
        ("Midfield (B)", f"{mid.get('team_b', 0):.1f}%"),
    ])

    # Visualisations
    show_visualizations(result.get("visualizations", []), cols=2)

    # Zone breakdown
    if zones:
        section_title("📏 Zone Breakdown")
        zone_labels = {
            "defensive_third":  "Defensive Third",
            "middle_third":     "Middle Third",
            "attacking_third":  "Attacking Third",
        }
        zone_cols = st.columns(3)
        for idx, (key, label) in enumerate(zone_labels.items()):
            z = zones.get(key, {})
            with zone_cols[idx]:
                st.markdown(f"**{label}**")
                st.metric("Team A", f"{z.get('team_a', 0):.1f}%")
                st.metric("Team B", f"{z.get('team_b', 0):.1f}%")

    # Verdict
    section_title("📋 Verdict")
    if a_ctrl > 55:
        st.markdown('<div class="insight-card">🟢 Team A is <strong>dominating space</strong> across the pitch.</div>',
                    unsafe_allow_html=True)
    elif b_ctrl > 55:
        st.markdown('<div class="warning-card">🔴 Team B is <strong>dominating space</strong> — Team A needs to win back territory.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="insight-card">⚖️ <strong>Balanced space control</strong> — contested match.</div>',
                    unsafe_allow_html=True)

    # Downloads
    visuals = result.get("visualizations", [])
    if visuals:
        st.markdown("---")
        cols = st.columns(len(visuals))
        for i, viz in enumerate(visuals):
            with cols[i]:
                download_image_button(viz, key=f"sc_dl_{i}")
