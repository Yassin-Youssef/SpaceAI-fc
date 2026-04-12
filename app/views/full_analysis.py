"""
SpaceAI FC - Full Match Analysis Page
Runs the complete Sense → Understand → Reason → Act → Explain pipeline.
"""

import streamlit as st
from app.components.theme import page_header, section_title
from app.components.input_forms import (
    player_table, pass_events_input, team_meta, match_info_form,
    demo_button, analyze_button, video_input_tab, dataset_input_tab,
)
from app.components.results_display import (
    check_result, show_visualizations, metric_row,
    show_swot, show_recommendations, show_explanation,
    show_formation_result, show_patterns, download_image_button, download_docx_button,
)
from app.utils.api_client import (
    analyze_full_match, upload_video, process_youtube, export_docx,
)
from app.demo_data import (
    BARCA_PLAYERS, MADRID_PLAYERS, DEMO_PASSES_SIMPLE_TEXT, DEMO_MATCH_INFO,
)


def render():
    page_header(
        "🏟️", "Full Match Analysis",
        "Complete tactical intelligence pipeline — formation detection, space control, "
        "pass network, press resistance, patterns, SWOT, recommendations, and explanation.",
    )

    # ── Session state ─────────────────────────────────────────────
    if "fa_result" not in st.session_state:
        st.session_state.fa_result = None
    if "fa_a" not in st.session_state:
        st.session_state.fa_a = None
    if "fa_b" not in st.session_state:
        st.session_state.fa_b = None
    if "fa_passes_text" not in st.session_state:
        st.session_state.fa_passes_text = ""
    if "fa_match_info" not in st.session_state:
        st.session_state.fa_match_info = None

    tab_manual, tab_video, tab_dataset = st.tabs(
        ["✏️ Manual Entry", "🎬 Video / YouTube", "📂 Dataset Upload"]
    )

    # ── Manual tab ────────────────────────────────────────────────
    with tab_manual:
        col_demo, _ = st.columns([1, 3])
        with col_demo:
            if demo_button("fa_demo"):
                st.session_state.fa_a = BARCA_PLAYERS
                st.session_state.fa_b = MADRID_PLAYERS
                st.session_state.fa_passes_text = DEMO_PASSES_SIMPLE_TEXT
                st.session_state.fa_match_info = DEMO_MATCH_INFO
                st.rerun()

        st.markdown("### Match Information")
        match_info = match_info_form(
            "fa_mi",
            defaults=st.session_state.fa_match_info,
        )

        st.markdown("---")
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            team_a_name, team_a_color = team_meta("fa_a", "FC Barcelona", "#a50044")
        with c2:
            team_b_name, team_b_color = team_meta("fa_b", "Real Madrid", "#ffffff")
        with c3:
            ball_x = st.number_input("Ball X", 0.0, 120.0, 60.0, 0.5, key="fa_bx")
            ball_y = st.number_input("Ball Y", 0.0, 80.0, 40.0, 0.5, key="fa_by")

        st.markdown("---")
        ca, cb = st.columns(2)
        with ca:
            players_a = player_table(
                f"{team_a_name} (11 players)",
                key_prefix="fa_pa",
                default_players=st.session_state.fa_a or BARCA_PLAYERS,
            )
        with cb:
            players_b = player_table(
                f"{team_b_name} (11 players)",
                key_prefix="fa_pb",
                default_players=st.session_state.fa_b or MADRID_PLAYERS,
            )

        st.markdown("---")
        passes = pass_events_input(
            key="fa_passes",
            default_text=st.session_state.fa_passes_text,
            simple=True,
        )

        st.markdown("---")
        if analyze_button("fa_analyze_manual", "🏟️ Run Full Analysis"):
            _run_analysis(
                players_a, players_b, passes,
                team_a_name, team_b_name,
                team_a_color, team_b_color,
                ball_x, ball_y, match_info,
            )

    # ── Video tab ─────────────────────────────────────────────────
    with tab_video:
        st.info(
            "Upload a match video or provide a YouTube URL. "
            "Player positions will be extracted automatically (requires Phase 4 dependencies). "
            "Demo mode uses El Clásico synthetic data."
        )
        vid = video_input_tab("fa_vid")
        if analyze_button("fa_analyze_vid", "🏟️ Process Video & Analyze"):
            with st.spinner("🎬 Processing video..."):
                if vid["source"] == "file":
                    tracking = upload_video(vid["file_bytes"], vid["filename"])
                elif vid["source"] == "youtube":
                    tracking = process_youtube(vid["url"], demo_mode=vid.get("demo_mode", True))
                else:
                    st.warning("Please upload a video or enter a YouTube URL.")
                    tracking = None

            if tracking and tracking.get("success"):
                td = tracking.get("tracking_data", {})
                st.success(
                    f"✅ Video processed — "
                    f"{len(td.get('team_a',[]))} + {len(td.get('team_b',[]))} players, "
                    f"{td.get('frames_processed', 0)} frames ({td.get('method','?')})"
                )
                _run_analysis(
                    td.get("team_a", BARCA_PLAYERS),
                    td.get("team_b", MADRID_PLAYERS),
                    [],  # no pass events from video
                    "Team A", "Team B", "#e74c3c", "#3498db",
                    60.0, 40.0, None,
                )
            elif tracking:
                st.error(f"Video error: {tracking.get('error', 'Unknown')}")

    # ── Dataset tab ───────────────────────────────────────────────
    with tab_dataset:
        ds = dataset_input_tab("fa_ds")
        if ds.get("file_bytes") and analyze_button("fa_analyze_ds", "🏟️ Analyze Dataset"):
            import tempfile
            from pathlib import Path
            tmp = Path(tempfile.mktemp(suffix=Path(ds["filename"]).suffix))
            tmp.write_bytes(ds["file_bytes"])
            with st.spinner("🏟️ Running full analysis..."):
                st.session_state.fa_result = analyze_full_match({
                    "input_type": "dataset",
                    "dataset_file": str(tmp),
                    "team_a_name": "Team A", "team_b_name": "Team B",
                    "team_a_color": "#e74c3c", "team_b_color": "#3498db",
                    "ball_x": 60.0, "ball_y": 40.0,
                })
            st.rerun()

    # ── Results ───────────────────────────────────────────────────
    _show_results()


def _run_analysis(players_a, players_b, passes,
                  team_a_name, team_b_name,
                  team_a_color, team_b_color,
                  ball_x, ball_y, match_info):
    payload = {
        "input_type": "manual",
        "team_a": players_a,
        "team_b": players_b,
        "passes": passes,
        "team_a_name": team_a_name,
        "team_b_name": team_b_name,
        "team_a_color": team_a_color,
        "team_b_color": team_b_color,
        "ball_x": ball_x,
        "ball_y": ball_y,
    }
    if match_info:
        payload["match_info"] = match_info

    with st.spinner("🏟️ Running full tactical analysis… this takes 15–30 seconds"):
        st.session_state.fa_result = analyze_full_match(payload)
        st.session_state.fa_match_info_display = match_info
        st.session_state.fa_team_a_name = team_a_name
        st.session_state.fa_team_b_name = team_b_name
    st.rerun()


def _show_results():
    result = st.session_state.get("fa_result")
    if result is None:
        return
    if not check_result(result):
        return

    team_a_name = st.session_state.get("fa_team_a_name", "Team A")
    team_b_name = st.session_state.get("fa_team_b_name", "Team B")

    st.markdown("---")

    # ── Match header ──────────────────────────────────────────────
    mi = result.get("match_info", {})
    if mi:
        score_a = mi.get("score_home", "?")
        score_b = mi.get("score_away", "?")
        comp    = mi.get("competition", "")
        minute  = mi.get("minute", "")
        st.markdown(
            f'<div style="text-align:center;padding:16px;background:linear-gradient(135deg,#1B5E20,#2E7D32);'
            f'border-radius:12px;margin-bottom:20px;">'
            f'<div style="color:rgba(255,255,255,0.7);font-size:0.8rem">{comp} — {minute}\'"</div>'
            f'<div style="color:white;font-size:2rem;font-weight:800;letter-spacing:2px">'
            f'{team_a_name} <span style="color:#FFD700">{score_a} – {score_b}</span> {team_b_name}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Formation ─────────────────────────────────────────────────
    fm = result.get("formation")
    if fm and fm.get("success"):
        show_formation_result(fm, team_a_name, team_b_name)
        show_visualizations(fm.get("visualizations", []), cols=2)

    # ── Space control ─────────────────────────────────────────────
    sc = result.get("space_control")
    if sc and sc.get("success"):
        section_title("🗺️ Space Control")
        metric_row([
            (f"{team_a_name} Control", f"{sc.get('team_a_control', 0):.1f}%"),
            (f"{team_b_name} Control", f"{sc.get('team_b_control', 0):.1f}%"),
            ("Midfield (A)", f"{sc.get('midfield_control',{}).get('team_a', 0):.1f}%"),
            ("Midfield (B)", f"{sc.get('midfield_control',{}).get('team_b', 0):.1f}%"),
        ])
        show_visualizations(sc.get("visualizations", []), cols=2)

    # ── Pass network ──────────────────────────────────────────────
    pn = result.get("pass_network")
    if pn and pn.get("success"):
        section_title("🔗 Pass Network")
        kd = pn.get("key_distributor", {})
        metric_row([
            ("Total Passes", str(pn.get("total_passes", 0))),
            ("Key Distributor", kd.get("name", "—")),
            ("Betweenness", f"{kd.get('betweenness', 0):.3f}"),
        ])
        show_visualizations(pn.get("visualizations", []))

    # ── Press resistance ──────────────────────────────────────────
    pr = result.get("press_resistance")
    if pr and pr.get("success"):
        section_title("💪 Press Resistance")
        metric_row([
            ("Score", f"{pr.get('press_resistance_score', 0):.0f}/100"),
            ("Success Under Press", f"{pr.get('pass_success_under_pressure', 0):.0%}"),
            ("Escape Rate", f"{pr.get('escape_rate', 0):.0%}"),
        ])
        show_visualizations(pr.get("visualizations", []))

    # ── Roles ─────────────────────────────────────────────────────
    roles = result.get("roles")
    if roles and roles.get("success"):
        section_title("👤 Player Roles")
        show_visualizations(roles.get("visualizations", []), cols=2)

    # ── Patterns ──────────────────────────────────────────────────
    pt = result.get("patterns")
    if pt and pt.get("success"):
        show_patterns(pt.get("team_a_patterns", []), team_a_name)
        show_patterns(pt.get("team_b_patterns", []), team_b_name)
        show_visualizations(pt.get("visualizations", []))

    # ── Intelligence ──────────────────────────────────────────────
    intel = result.get("intelligence")
    if intel and intel.get("success"):
        show_swot(intel.get("swot", []))
        show_recommendations(intel.get("recommendations", []))

    # ── Explanation ───────────────────────────────────────────────
    exp = result.get("explanation")
    if exp and exp.get("success"):
        show_explanation(exp.get("text", ""))

    # ── Downloads ─────────────────────────────────────────────────
    st.markdown("---")
    section_title("⬇️ Download Report")

    dl_cols = st.columns(3)
    visuals_all = result.get("visualizations", [])
    if visuals_all:
        with dl_cols[0]:
            download_image_button(visuals_all[0], key="fa_dl_img")

    with dl_cols[1]:
        if st.button("📄 Download Word Report", key="fa_dl_docx_btn"):
            with st.spinner("Generating Word document..."):
                docx_bytes = export_docx({
                    "analysis_data": result,
                    "team_name": team_a_name,
                    "opponent_name": team_b_name,
                })
            if docx_bytes:
                download_docx_button(
                    docx_bytes,
                    f"SpaceAI_{team_a_name}_vs_{team_b_name}.docx".replace(" ", "_"),
                    key="fa_dl_docx",
                )
            else:
                st.warning("Word export requires python-docx.")
