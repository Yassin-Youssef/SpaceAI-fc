"""
SpaceAI FC - Press Resistance Page
"""

import streamlit as st
from app.components.theme import page_header, section_title
from app.components.input_forms import (
    player_table, team_meta, demo_button, analyze_button,
    pass_events_input, dataset_input_tab,
)
from app.components.results_display import (
    check_result, show_visualizations, metric_row, download_image_button,
)
from app.utils.api_client import analyze_press_resistance
from app.demo_data import BARCA_PLAYERS, MADRID_PLAYERS, DEMO_PASSES_TEXT


def render():
    page_header(
        "💪", "Press Resistance Analysis",
        "Measure how well a team handles opponent pressure. "
        "Identifies vulnerable zones and pass success rates under press.",
    )

    if "pr_result" not in st.session_state:
        st.session_state.pr_result = None
    if "pr_a" not in st.session_state:
        st.session_state.pr_a = None
    if "pr_b" not in st.session_state:
        st.session_state.pr_b = None
    if "pr_passes_text" not in st.session_state:
        st.session_state.pr_passes_text = ""

    tab_manual, tab_dataset = st.tabs(["✏️ Manual Entry", "📂 Dataset Upload"])

    with tab_manual:
        col_demo, _ = st.columns([1, 3])
        with col_demo:
            if demo_button("pr_demo"):
                st.session_state.pr_a = BARCA_PLAYERS
                st.session_state.pr_b = MADRID_PLAYERS
                st.session_state.pr_passes_text = DEMO_PASSES_TEXT
                st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            team_name, team_color = team_meta("pr_a", "FC Barcelona", "#a50044")
        with c2:
            opp_name, _ = team_meta("pr_b", "Real Madrid", "#ffffff")

        st.markdown("---")
        c_r, c_t = st.columns([1, 1])
        pressure_radius    = c_r.slider("Pressure radius (metres)", 3.0, 25.0, 10.0, 0.5, key="pr_radius")
        pressure_threshold = c_t.slider("Min nearby opponents = under pressure", 1, 5, 2, key="pr_thresh")

        st.markdown("---")
        ca, cb = st.columns(2)
        with ca:
            players_a = player_table(
                f"{team_name} Players (being analysed)",
                key_prefix="pr_pa",
                default_players=st.session_state.pr_a or BARCA_PLAYERS,
            )
        with cb:
            players_b = player_table(
                f"{opp_name} Players (pressing team)",
                key_prefix="pr_pb",
                default_players=st.session_state.pr_b or MADRID_PLAYERS,
            )

        st.markdown("---")
        st.markdown("**Pass events with outcome**")
        passes = pass_events_input(
            key="pr_passes",
            default_text=st.session_state.pr_passes_text,
            simple=False,
        )

        st.markdown("---")
        if analyze_button("pr_analyze", "⚽ Analyze Press Resistance"):
            _run_analysis(
                players_a, players_b, passes,
                team_name, team_color, opp_name,
                pressure_radius, pressure_threshold,
            )

    with tab_dataset:
        ds = dataset_input_tab("pr_ds")
        if ds.get("file_bytes") and analyze_button("pr_analyze_ds", "⚽ Analyze Dataset"):
            import tempfile
            from pathlib import Path
            tmp = Path(tempfile.mktemp(suffix=Path(ds["filename"]).suffix))
            tmp.write_bytes(ds["file_bytes"])
            with st.spinner("💪 Analyzing press resistance..."):
                st.session_state.pr_result = analyze_press_resistance({
                    "input_type": "dataset", "dataset_file": str(tmp),
                    "team_a_name": "Team A", "team_b_name": "Team B",
                    "team_a_color": "#e74c3c", "team_b_color": "#3498db",
                    "pressure_radius": 10.0, "pressure_threshold": 2,
                })
            st.rerun()

    _show_results()


def _run_analysis(players_a, players_b, passes, team_name, team_color,
                  opp_name, pressure_radius, pressure_threshold):
    with st.spinner("💪 Analyzing press resistance..."):
        st.session_state.pr_result = analyze_press_resistance({
            "input_type": "manual",
            "team_a": players_a,
            "team_b": players_b,
            "passes": passes,
            "team_a_name": team_name,
            "team_b_name": opp_name,
            "team_a_color": team_color,
            "team_b_color": "#3498db",
            "pressure_radius": pressure_radius,
            "pressure_threshold": pressure_threshold,
        })
    st.rerun()


def _show_results():
    result = st.session_state.get("pr_result")
    if result is None:
        return
    if not check_result(result):
        return

    st.markdown("---")
    section_title("📊 Press Resistance Results")

    score = result.get("press_resistance_score", 0)
    pass_overall = result.get("pass_success_overall", 0)
    pass_pressure = result.get("pass_success_under_pressure", 0)
    escape = result.get("escape_rate", 0)
    total = result.get("total_passes", 0)
    under_press = result.get("passes_under_pressure", 0)

    # Score indicator
    if score >= 70:
        score_color, score_label = "#2E7D32", "Excellent"
    elif score >= 50:
        score_color, score_label = "#F57F17", "Moderate"
    else:
        score_color, score_label = "#C62828", "Vulnerable"

    st.markdown(
        f'<div style="text-align:center;padding:20px;background:linear-gradient(135deg,#1B5E20,#2E7D32);'
        f'border-radius:12px;margin-bottom:16px;">'
        f'<div style="color:rgba(255,255,255,0.7);font-size:0.85rem;letter-spacing:1px">PRESS RESISTANCE SCORE</div>'
        f'<div style="color:#FFD700;font-size:3.5rem;font-weight:800;line-height:1.1">{score:.0f}</div>'
        f'<div style="color:{score_color};background:rgba(255,255,255,0.15);display:inline-block;'
        f'padding:4px 16px;border-radius:20px;font-weight:600;margin-top:4px">{score_label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    metric_row([
        ("Total Passes", str(total)),
        ("Under Pressure", str(under_press)),
        ("Success Overall", f"{pass_overall:.0%}"),
        ("Success Under Press", f"{pass_pressure:.0%}"),
        ("Escape Rate", f"{escape:.0%}"),
    ])

    show_visualizations(result.get("visualizations", []))

    # Vulnerable zones
    zones = result.get("vulnerable_zones", [])
    if zones:
        section_title("⚠️ Vulnerable Zones")
        for z in zones:
            z_name = f"Zone ({z.get('zone_x','?')},{z.get('zone_y','?')})"
            success = z.get("success_rate", 0)
            passes = z.get("total_passes", 0)
            st.markdown(
                f'<div class="danger-card">'
                f'<strong>{z_name}</strong> — Success rate: {success:.0%} '
                f'({passes} passes in this zone)'
                f'</div>',
                unsafe_allow_html=True,
            )

    visuals = result.get("visualizations", [])
    if visuals:
        st.markdown("---")
        download_image_button(visuals[0], key="pr_dl")
