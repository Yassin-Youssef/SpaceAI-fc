"""
SpaceAI FC - Tactical Explanation Page
=========================================
Feature 12: Generate full tactical explanations from match data.
Supports template and AI modes.
"""

import streamlit as st

from app.components.theme import page_header, section_title
from app.components.input_forms import (
    player_table, pass_events_input, team_meta, match_info_form,
    demo_button, analyze_button, video_input_tab, dataset_input_tab,
)
from app.components.results_display import check_result, show_visualizations, metric_row
from app.utils.api_client import get_explanation, export_docx
from app.utils.llm_client import call_openrouter, is_llm_available
from app.demo_data import (
    BARCA_PLAYERS, MADRID_PLAYERS, DEMO_PASSES_SIMPLE_TEXT, DEMO_MATCH_INFO,
)


def render():
    page_header(
        "📝", "Tactical Explanation",
        "Generate comprehensive, AI-powered or template-based tactical explanations "
        "of a match situation. Download as text or Word document.",
    )

    # ── Session state ─────────────────────────────────────────────
    if "exp_result" not in st.session_state:
        st.session_state.exp_result = None
    if "exp_a" not in st.session_state:
        st.session_state.exp_a = None
    if "exp_b" not in st.session_state:
        st.session_state.exp_b = None
    if "exp_passes_text" not in st.session_state:
        st.session_state.exp_passes_text = ""
    if "exp_match_info" not in st.session_state:
        st.session_state.exp_match_info = None

    # ── Mode selection ────────────────────────────────────────────
    mode = st.radio(
        "Explanation mode",
        ["Template Mode (Free)", "AI Mode (Requires API Key)"],
        horizontal=True,
        key="exp_mode_radio",
    )
    api_mode = "llm" if "AI Mode" in mode else "template"

    if api_mode == "llm" and not is_llm_available():
        st.warning(
            "⚠️ Set your `OPENROUTER_API_KEY` environment variable to enable AI-powered explanations. "
            "Falling back to template mode."
        )
        api_mode = "template"

    # ── Use Previous Analysis ─────────────────────────────────────
    use_previous = st.checkbox(
        "Use Previous Analysis (if Full Match Analysis was run)",
        key="exp_use_prev",
    )

    if use_previous and st.session_state.get("fa_result"):
        st.success("✅ Using results from previous Full Match Analysis.")
        prev_result = st.session_state.fa_result
        if st.button("📝 Generate Explanation from Previous Analysis", key="exp_from_prev"):
            _run_from_previous(prev_result, api_mode)
        _show_results()
        return
    elif use_previous:
        st.info("ℹ️ No previous Full Match Analysis found. Please run one first or enter data below.")

    st.markdown("---")

    # ── Input tabs ────────────────────────────────────────────────
    tab_manual, tab_video, tab_dataset = st.tabs(
        ["✏️ Manual Entry", "🎬 Video / YouTube", "📂 Dataset Upload"]
    )

    # ── Manual tab ────────────────────────────────────────────────
    with tab_manual:
        col_demo, _ = st.columns([1, 3])
        with col_demo:
            if demo_button("exp_demo"):
                st.session_state.exp_a = BARCA_PLAYERS
                st.session_state.exp_b = MADRID_PLAYERS
                st.session_state.exp_passes_text = DEMO_PASSES_SIMPLE_TEXT
                st.session_state.exp_match_info = DEMO_MATCH_INFO
                st.rerun()

        st.markdown("### Match Information")
        match_info = match_info_form(
            "exp_mi",
            defaults=st.session_state.exp_match_info,
        )

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            team_a_name, team_a_color = team_meta("exp_a", "FC Barcelona", "#a50044")
        with c2:
            team_b_name, team_b_color = team_meta("exp_b", "Real Madrid", "#ffffff")

        c_ball1, c_ball2 = st.columns(2)
        ball_x = c_ball1.number_input("Ball X", 0.0, 120.0, 60.0, 0.5, key="exp_bx")
        ball_y = c_ball2.number_input("Ball Y", 0.0, 80.0, 40.0, 0.5, key="exp_by")

        st.markdown("---")
        ca, cb = st.columns(2)
        with ca:
            players_a = player_table(
                f"{team_a_name} (11 players)",
                key_prefix="exp_pa",
                default_players=st.session_state.exp_a or BARCA_PLAYERS,
            )
        with cb:
            players_b = player_table(
                f"{team_b_name} (11 players)",
                key_prefix="exp_pb",
                default_players=st.session_state.exp_b or MADRID_PLAYERS,
            )

        st.markdown("---")
        passes = pass_events_input(
            key="exp_passes",
            default_text=st.session_state.exp_passes_text,
            simple=True,
        )

        st.markdown("---")
        if analyze_button("exp_analyze", "📝 Generate Explanation"):
            _run_explanation(
                api_mode,
                players_a, players_b, passes,
                team_a_name, team_b_name,
                team_a_color, team_b_color,
                ball_x, ball_y, match_info,
            )

    # ── Video tab ─────────────────────────────────────────────────
    with tab_video:
        st.info("Upload a match video or YouTube URL for automatic position extraction.")
        vid = video_input_tab("exp_vid")
        if analyze_button("exp_analyze_vid", "📝 Process & Explain"):
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
                td = tracking.get("tracking_data", {})
                _run_explanation(
                    api_mode,
                    td.get("team_a", BARCA_PLAYERS),
                    td.get("team_b", MADRID_PLAYERS),
                    [], "Team A", "Team B", "#e74c3c", "#3498db",
                    60.0, 40.0, None,
                )
            elif tracking:
                st.error(f"Video error: {tracking.get('error', 'Unknown')}")

    # ── Dataset tab ───────────────────────────────────────────────
    with tab_dataset:
        ds = dataset_input_tab("exp_ds")
        if ds.get("file_bytes") and analyze_button("exp_analyze_ds", "📝 Explain Dataset"):
            import tempfile
            from pathlib import Path
            tmp = Path(tempfile.mktemp(suffix=Path(ds["filename"]).suffix))
            tmp.write_bytes(ds["file_bytes"])
            with st.spinner("📝 Generating explanation..."):
                st.session_state.exp_result = get_explanation({
                    "mode": api_mode,
                    "report_data": {"dataset_file": str(tmp)},
                    "team_name": "Team A", "opponent_name": "Team B",
                })
            st.rerun()

    # ── Results ───────────────────────────────────────────────────
    _show_results()


def _run_explanation(mode, players_a, players_b, passes,
                     team_a_name, team_b_name,
                     team_a_color, team_b_color,
                     ball_x, ball_y, match_info):
    """Generate a tactical explanation."""
    with st.spinner("📝 Generating tactical explanation..."):

        if mode == "llm" and is_llm_available():
            # Build context for LLM
            explanation_text = _llm_explanation(
                players_a, players_b, passes,
                team_a_name, team_b_name,
                match_info,
            )
            actual_mode = "llm"
        else:
            # Use API template endpoint
            report_data = {
                "team_a": players_a,
                "team_b": players_b,
                "passes": passes,
                "team_a_name": team_a_name,
                "team_b_name": team_b_name,
                "ball_x": ball_x,
                "ball_y": ball_y,
            }
            result = get_explanation({
                "mode": "template",
                "match_info": match_info,
                "report_data": report_data,
                "team_name": team_a_name,
                "opponent_name": team_b_name,
            })

            if result.get("success"):
                explanation_text = result.get("text", "")
                actual_mode = "template"
            else:
                # Fallback: generate a basic template locally
                explanation_text = _local_template(
                    players_a, players_b, passes,
                    team_a_name, team_b_name, match_info,
                )
                actual_mode = "template"

        st.session_state.exp_result = {
            "success": True,
            "text": explanation_text,
            "mode": actual_mode,
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
        }
    st.rerun()


def _run_from_previous(prev_result, mode):
    """Generate explanation from previous Full Match Analysis."""
    with st.spinner("📝 Generating explanation from previous analysis..."):
        team_a_name = st.session_state.get("fa_team_a_name", "Team A")
        team_b_name = st.session_state.get("fa_team_b_name", "Team B")

        if mode == "llm" and is_llm_available():
            # Build comprehensive context from previous analysis
            parts = [f"Match: {team_a_name} vs {team_b_name}"]

            mi = prev_result.get("match_info", {})
            if mi:
                parts.append(f"Score: {mi.get('score_home', '?')}-{mi.get('score_away', '?')}, "
                             f"Minute: {mi.get('minute', '?')}")

            fm = prev_result.get("formation", {})
            if fm.get("success"):
                parts.append(f"Formation A: {fm.get('team_a_formation', '?')}, "
                             f"Formation B: {fm.get('team_b_formation', '?')}")

            sc = prev_result.get("space_control", {})
            if sc.get("success"):
                parts.append(f"Space Control: A={sc.get('team_a_control', 50):.1f}%, "
                             f"B={sc.get('team_b_control', 50):.1f}%")

            pr = prev_result.get("press_resistance", {})
            if pr.get("success"):
                parts.append(f"Press Resistance Score: {pr.get('press_resistance_score', 0):.0f}/100")

            context = "\n".join(parts)

            explanation_text = call_openrouter(
                "You are SpaceAI FC, a professional football tactical intelligence system. "
                "Write a comprehensive tactical explanation of this match situation. "
                "Cover formations, space control, press resistance, key patterns, "
                "and strategic recommendations. Use markdown formatting with clear headers.",
                context,
            )

            if not explanation_text:
                explanation_text = _template_from_result(prev_result, team_a_name, team_b_name)
                mode = "template"
        else:
            explanation_text = _template_from_result(prev_result, team_a_name, team_b_name)
            mode = "template"

        st.session_state.exp_result = {
            "success": True,
            "text": explanation_text,
            "mode": mode,
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
        }
    st.rerun()


def _llm_explanation(players_a, players_b, passes,
                     team_a_name, team_b_name, match_info) -> str:
    """Generate explanation using LLM."""
    # Build context
    parts = [f"Match: {team_a_name} vs {team_b_name}"]
    if match_info:
        parts.append(f"Score: {match_info.get('score_home', 0)}-{match_info.get('score_away', 0)}")
        parts.append(f"Minute: {match_info.get('minute', 0)}")

    # Player positions summary
    if players_a:
        positions_a = ", ".join(f"#{p.get('number', '?')} {p.get('name', '?')} ({p.get('position', '?')} at x={p.get('x', 0):.0f},y={p.get('y', 0):.0f})"
                                for p in players_a[:5])
        parts.append(f"{team_a_name} key players: {positions_a}...")

    if players_b:
        positions_b = ", ".join(f"#{p.get('number', '?')} {p.get('name', '?')} ({p.get('position', '?')} at x={p.get('x', 0):.0f},y={p.get('y', 0):.0f})"
                                for p in players_b[:5])
        parts.append(f"{team_b_name} key players: {positions_b}...")

    parts.append(f"Total passes: {len(passes)}")

    context = "\n".join(parts)

    result = call_openrouter(
        "You are SpaceAI FC, a professional football tactical intelligence system. "
        "Write a comprehensive tactical explanation of this match situation. "
        "Cover: 1) Formation analysis, 2) Space control and territorial dominance, "
        "3) Key tactical patterns, 4) Press resistance assessment, "
        "5) Strategic recommendations. Use markdown with headers. Be specific and reference player data.",
        context,
    )

    return result or _local_template(players_a, players_b, passes, team_a_name, team_b_name, match_info)


def _local_template(players_a, players_b, passes, team_a_name, team_b_name, match_info) -> str:
    """Generate a local template-based explanation."""
    mi_str = ""
    if match_info:
        mi_str = (
            f"**{team_a_name}** {match_info.get('score_home', 0)} – "
            f"{match_info.get('score_away', 0)} **{team_b_name}** "
            f"(Minute {match_info.get('minute', 0)})"
        )

    n_a = len(players_a) if players_a else 0
    n_b = len(players_b) if players_b else 0
    n_passes = len(passes) if passes else 0

    # Compute average positions
    avg_x_a = sum(p.get("x", 60) for p in players_a) / max(n_a, 1) if players_a else 60
    avg_x_b = sum(p.get("x", 60) for p in players_b) / max(n_b, 1) if players_b else 60

    compactness_a = "high" if avg_x_a < 50 else "moderate" if avg_x_a < 65 else "stretched"
    compactness_b = "high" if avg_x_b > 70 else "moderate" if avg_x_b > 55 else "stretched"

    return f"""## Tactical Explanation

{f'### Match Situation{chr(10)}{mi_str}' if mi_str else ''}

### Formation Analysis
{team_a_name} deployed **{n_a} players** with an average x-position of **{avg_x_a:.0f}**, indicating a {compactness_a} defensive structure.

{team_b_name} positioned their **{n_b} players** with an average x-position of **{avg_x_b:.0f}**, showing a {compactness_b} setup.

### Passing & Build-up
A total of **{n_passes} passes** were recorded in this analysis. {"The passing network suggests active ball circulation." if n_passes > 15 else "Limited passing data available for deep analysis."}

### Space Control
Based on player positions, {"the home side appears to control more territory in the attacking half." if avg_x_a > 50 else "the away side seems to be dominating territorial control."}

### Key Observations
- Average team A position: {avg_x_a:.0f}m from goal line
- Average team B position: {avg_x_b:.0f}m from goal line
- Passing volume: {n_passes} events recorded

### Recommendations
1. {"Press higher to gain territory" if avg_x_a < 50 else "Maintain current pressing line"}
2. {"Increase passing tempo" if n_passes < 15 else "Continue building through possession"}
3. {"Look for switches of play to exploit width" if abs(avg_x_a - avg_x_b) < 15 else "Capitalize on territorial advantage"}

---
*Generated by SpaceAI FC — Template Mode*
"""


def _template_from_result(result, team_a_name, team_b_name) -> str:
    """Generate template explanation from a full analysis result dict."""
    parts = [f"## Tactical Explanation: {team_a_name} vs {team_b_name}\n"]

    fm = result.get("formation", {})
    if fm.get("success"):
        parts.append(f"### Formation Detection")
        parts.append(f"- {team_a_name}: **{fm.get('team_a_formation', 'Unknown')}** ({fm.get('team_a_confidence', 0):.0%} confidence)")
        parts.append(f"- {team_b_name}: **{fm.get('team_b_formation', 'Unknown')}** ({fm.get('team_b_confidence', 0):.0%} confidence)")
        parts.append("")

    sc = result.get("space_control", {})
    if sc.get("success"):
        parts.append("### Space Control")
        parts.append(f"- {team_a_name}: **{sc.get('team_a_control', 50):.1f}%**")
        parts.append(f"- {team_b_name}: **{sc.get('team_b_control', 50):.1f}%**")
        parts.append("")

    pr = result.get("press_resistance", {})
    if pr.get("success"):
        parts.append("### Press Resistance")
        parts.append(f"- Score: **{pr.get('press_resistance_score', 0):.0f}/100**")
        parts.append(f"- Pass success under pressure: **{pr.get('pass_success_under_pressure', 0):.0%}**")
        parts.append("")

    pn = result.get("pass_network", {})
    if pn.get("success"):
        parts.append("### Pass Network")
        kd = pn.get("key_distributor", {})
        parts.append(f"- Total passes: {pn.get('total_passes', 0)}")
        parts.append(f"- Key distributor: {kd.get('name', 'Unknown')}")
        parts.append("")

    parts.append("---\n*Generated by SpaceAI FC — Template Mode*")
    return "\n".join(parts)


def _show_results():
    result = st.session_state.get("exp_result")
    if result is None:
        return
    if not result.get("success"):
        if result.get("error"):
            st.error(f"❌ {result['error']}")
        return

    text = result.get("text", "")
    mode = result.get("mode", "template")
    team_a = result.get("team_a_name", "Team A")
    team_b = result.get("team_b_name", "Team B")

    st.markdown("---")
    section_title("📝 Tactical Explanation")

    # ── Mode badge ────────────────────────────────────────────
    if mode == "llm":
        st.markdown(
            '<div style="display:inline-block;background:#1B5E20;color:#FFD700;'
            'padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;'
            'margin-bottom:12px">AI Mode (Claude)</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="display:inline-block;background:#E8F5E9;color:#1B5E20;'
            'padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;'
            'margin-bottom:12px">Template Mode</div>',
            unsafe_allow_html=True,
        )

    # ── Explanation text ──────────────────────────────────────
    st.markdown(
        f'<div class="result-card" style="line-height:1.8;padding:24px 28px">'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(text)

    # ── Action buttons ────────────────────────────────────────
    st.markdown("---")
    section_title("⬇️ Download & Share")

    dc1, dc2, dc3 = st.columns(3)

    with dc1:
        # Copy to clipboard (JavaScript)
        st.markdown(
            f'<button onclick="navigator.clipboard.writeText(`{text[:500].replace(chr(96), "")}`);'
            f'this.textContent=\'✅ Copied!\'"'
            f' style="background:linear-gradient(135deg,#2E7D32,#1B5E20);color:white;'
            f'border:none;padding:10px 24px;border-radius:8px;font-weight:600;'
            f'cursor:pointer;font-size:0.9rem;width:100%">'
            f'📋 Copy to Clipboard</button>',
            unsafe_allow_html=True,
        )

    with dc2:
        st.download_button(
            "📄 Download as Text",
            data=text,
            file_name=f"SpaceAI_explanation_{team_a}_vs_{team_b}.txt".replace(" ", "_"),
            mime="text/plain",
            key="exp_dl_txt",
            use_container_width=True,
        )

    with dc3:
        if st.button("📄 Download as Word", key="exp_dl_docx_btn", use_container_width=True):
            with st.spinner("Generating Word document..."):
                docx_bytes = export_docx({
                    "analysis_data": {"explanation": {"text": text}},
                    "team_name": team_a,
                    "opponent_name": team_b,
                })
            if docx_bytes:
                st.download_button(
                    "⬇️ Save Word File",
                    data=docx_bytes,
                    file_name=f"SpaceAI_explanation_{team_a}_vs_{team_b}.docx".replace(" ", "_"),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="exp_dl_docx",
                )
            else:
                st.warning("Word export requires python-docx and the API to be running.")
