"""
SpaceAI FC - Pass Network Page
"""

import streamlit as st
from app.components.theme import page_header, section_title
from app.components.input_forms import (
    player_table, pass_events_input, team_meta, demo_button,
    analyze_button, video_input_tab, dataset_input_tab,
)
from app.components.results_display import (
    check_result, show_visualizations, metric_row, show_insights, download_image_button,
)
from app.utils.api_client import analyze_pass_network, upload_video, process_youtube
from app.demo_data import BARCA_PLAYERS, DEMO_PASSES_SIMPLE_TEXT


def render():
    page_header(
        "🔗", "Pass Network Analysis",
        "Map passing connections between players, identify key distributors, "
        "top connections, and weak links in the team structure.",
    )

    # ── Session state ─────────────────────────────────────────────
    if "pn_result" not in st.session_state:
        st.session_state.pn_result = None
    if "pn_players" not in st.session_state:
        st.session_state.pn_players = None
    if "pn_passes_text" not in st.session_state:
        st.session_state.pn_passes_text = ""

    # ── Input tabs ────────────────────────────────────────────────
    tab_manual, tab_video, tab_dataset = st.tabs(
        ["✏️ Manual Entry", "🎬 Video / YouTube", "📂 Dataset Upload"]
    )

    # ── Manual tab ────────────────────────────────────────────────
    with tab_manual:
        col_demo, _ = st.columns([1, 3])
        with col_demo:
            if demo_button("pn_demo"):
                st.session_state.pn_players = BARCA_PLAYERS
                st.session_state.pn_passes_text = DEMO_PASSES_SIMPLE_TEXT
                st.rerun()

        team_name, team_color = team_meta("pn", "FC Barcelona", "#a50044")

        st.markdown("---")
        players = player_table(
            "Players (11)",
            key_prefix="pn",
            default_players=st.session_state.pn_players or BARCA_PLAYERS,
        )

        st.markdown("---")
        passes = pass_events_input(
            key="pn_passes",
            default_text=st.session_state.pn_passes_text,
            simple=True,
        )

        st.markdown("---")
        col_a, col_b = st.columns([2, 1])
        with col_a:
            min_passes = st.slider("Minimum passes to show connection", 1, 8, 2, key="pn_min_passes")
        with col_b:
            seq_text = st.text_input(
                "Pass sequence (optional, jersey numbers)",
                placeholder="e.g. 2,4,8,6,9",
                key="pn_seq",
                help="Enter jersey numbers separated by commas to show a specific pass sequence",
            )

        manual_data = {
            "players": players, "passes": passes,
            "team_name": team_name, "team_color": team_color,
            "min_passes": min_passes, "sequence": seq_text,
            "input_type": "manual",
        }

        st.markdown("---")
        if analyze_button("pn_analyze_manual", "⚽ Analyze Pass Network"):
            _run_analysis(manual_data)

    # ── Video tab ─────────────────────────────────────────────────
    with tab_video:
        st.info("Video processing extracts player positions automatically. "
                "Phase 4 dependencies (ultralytics, opencv) needed for real video; "
                "demo mode uses synthetic El Clásico data.")
        vid = video_input_tab("pn_vid")
        if analyze_button("pn_analyze_vid", "⚽ Process Video & Analyze"):
            with st.spinner("🎬 Processing video..."):
                if vid["source"] == "file":
                    tracking = upload_video(vid["file_bytes"], vid["filename"])
                elif vid["source"] == "youtube":
                    tracking = process_youtube(vid["url"], demo_mode=vid.get("demo_mode", True))
                else:
                    st.warning("Please upload a video file or enter a YouTube URL.")
                    tracking = None

            if tracking and tracking.get("success"):
                td = tracking.get("tracking_data", {})
                st.success(
                    f"✅ Video processed — {len(td.get('team_a', []))} + "
                    f"{len(td.get('team_b', []))} players detected "
                    f"({td.get('frames_processed', 0)} frames, method: {td.get('method', '?')})"
                )
                # Use team_a from video as players
                video_data = {
                    "players": td.get("team_a", BARCA_PLAYERS),
                    "passes": [], "team_name": "Team A", "team_color": "#e74c3c",
                    "min_passes": 1, "sequence": None, "input_type": "manual",
                }
                _run_analysis(video_data)
            elif tracking:
                st.error(f"Video processing failed: {tracking.get('error', 'Unknown error')}")

    # ── Dataset tab ───────────────────────────────────────────────
    with tab_dataset:
        ds = dataset_input_tab("pn_ds")
        if ds.get("file_bytes") and analyze_button("pn_analyze_ds", "⚽ Analyze Dataset"):
            import tempfile, os
            from pathlib import Path
            tmp = Path(tempfile.mktemp(suffix=Path(ds["filename"]).suffix))
            tmp.write_bytes(ds["file_bytes"])
            _run_analysis({
                "dataset_file": str(tmp),
                "team_name": "Team A", "team_color": "#e74c3c",
                "min_passes": 2, "sequence": None, "input_type": "dataset",
            })

    # ── Results ───────────────────────────────────────────────────
    _show_results()


def _run_analysis(data: dict):
    """Call the API and store results in session state."""
    players = data.get("players", [])
    passes = data.get("passes", [])

    # Parse sequence
    seq = None
    seq_text = data.get("sequence", "")
    if seq_text:
        try:
            seq = [int(x.strip()) for x in seq_text.split(",") if x.strip()]
        except ValueError:
            seq = None

    payload = {
        "input_type": data.get("input_type", "manual"),
        "team_a": players,
        "team_a_name": data.get("team_name", "Team"),
        "team_a_color": data.get("team_color", "#e74c3c"),
        "passes": passes,
        "min_passes": data.get("min_passes", 2),
        "sequence": seq,
    }
    if data.get("dataset_file"):
        payload["dataset_file"] = data["dataset_file"]

    with st.spinner("🔗 Building pass network..."):
        result = analyze_pass_network(payload)

    st.session_state.pn_result = result
    st.rerun()


def _show_results():
    result = st.session_state.get("pn_result")
    if result is None:
        return
    if not check_result(result):
        return

    st.markdown("---")
    section_title("📊 Pass Network Results")

    # Metrics
    kd = result.get("key_distributor", {})
    mi = result.get("most_involved", {})
    metric_row([
        ("Total Passes", str(result.get("total_passes", 0))),
        ("Key Distributor", kd.get("name", "—")),
        ("Betweenness", f"{kd.get('betweenness', 0):.3f}"),
        ("Most Involved", mi.get("name", "—")),
    ])

    # Visualisations
    show_visualizations(result.get("visualizations", []))

    # Top connections
    top_conn = result.get("top_connections", [])
    if top_conn:
        section_title("🔝 Top Connections")
        for conn in top_conn[:5]:
            st.markdown(
                f'<div class="insight-card">'
                f'<strong>#{conn["from_number"]} {conn["from"]}</strong> → '
                f'<strong>#{conn["to_number"]} {conn["to"]}</strong>: '
                f'{conn["passes"]} passes'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Weak links
    weak = result.get("weak_links", [])
    if weak:
        section_title("⚠️ Weak Links")
        for wl in weak:
            st.markdown(
                f'<div class="warning-card">'
                f'#{wl["number"]} {wl["name"]} — only {wl["total_involvement"]} pass involvements'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Download
    visuals = result.get("visualizations", [])
    if visuals:
        st.markdown("---")
        download_image_button(visuals[0], key="pn_dl_img")
