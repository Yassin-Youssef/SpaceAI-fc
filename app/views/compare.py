"""
SpaceAI FC - Compare Page
============================
Feature 10: Compare two teams, two formations, or two tactical setups
side by side.
"""

import streamlit as st
import numpy as np

from app.components.theme import page_header, section_title
from app.components.input_forms import (
    player_table, pass_events_input, team_meta, demo_button, analyze_button,
)
from app.components.results_display import (
    check_result, show_visualizations, metric_row, show_formation_result,
)
from app.utils.api_client import (
    analyze_space_control, analyze_formation, analyze_press_resistance,
    analyze_patterns, build_base_request,
)
from app.utils.llm_client import call_openrouter, is_llm_available
from app.demo_data import (
    BARCA_PLAYERS, MADRID_PLAYERS, DEMO_PASSES, DEMO_PASSES_SIMPLE_TEXT,
    FORMATIONS, TACTICS,
)


TACTIC_LABELS = {
    "high_press": "High Press",
    "low_block": "Low Block",
    "possession": "Possession",
    "counter_attack": "Counter-Attack",
    "wide_play": "Wide Play",
    "narrow_play": "Narrow Play",
}


def render():
    page_header(
        "⚖️", "Compare",
        "Compare two teams, two formations, or two tactical setups side by side. "
        "Identify strengths, weaknesses, and tactical advantages.",
    )

    # ── Session state ─────────────────────────────────────────────
    if "cmp_result" not in st.session_state:
        st.session_state.cmp_result = None
    if "cmp_demo_loaded" not in st.session_state:
        st.session_state.cmp_demo_loaded = False

    # ── Comparison type ───────────────────────────────────────────
    cmp_type = st.selectbox(
        "Comparison type",
        ["Two Teams", "Two Formations", "Two Tactical Setups"],
        key="cmp_type",
    )

    col_demo, _ = st.columns([1, 3])
    with col_demo:
        if demo_button("cmp_demo"):
            st.session_state.cmp_demo_loaded = True
            st.rerun()

    st.markdown("---")
    dl = st.session_state.cmp_demo_loaded

    # ── Two Teams ─────────────────────────────────────────────────
    if cmp_type == "Two Teams":
        _render_two_teams(dl)

    # ── Two Formations ────────────────────────────────────────────
    elif cmp_type == "Two Formations":
        _render_two_formations(dl)

    # ── Two Tactical Setups ───────────────────────────────────────
    else:
        _render_two_setups(dl)

    # ── Results ───────────────────────────────────────────────────
    _show_results()


# ═══════════════════════════════════════════════════════════════
# Two Teams
# ═══════════════════════════════════════════════════════════════

def _render_two_teams(demo_loaded: bool):
    """Full player data for both sides."""
    st.markdown("### Team A")
    c1, c2 = st.columns(2)
    with c1:
        team_a_name, team_a_color = team_meta("cmp_ta", "FC Barcelona" if demo_loaded else "Team A", "#a50044")
    with c2:
        form_a = st.selectbox("Formation (A)", FORMATIONS,
                              index=1 if demo_loaded else 0, key="cmp_form_a")

    players_a = player_table(
        f"{team_a_name} Players",
        key_prefix="cmp_pa",
        default_players=BARCA_PLAYERS if demo_loaded else None,
    )

    st.markdown("---")

    st.markdown("### Team B")
    c3, c4 = st.columns(2)
    with c3:
        team_b_name, team_b_color = team_meta("cmp_tb", "Real Madrid" if demo_loaded else "Team B", "#ffffff")
    with c4:
        form_b = st.selectbox("Formation (B)", FORMATIONS,
                              index=0 if demo_loaded else 0, key="cmp_form_b")

    players_b = player_table(
        f"{team_b_name} Players",
        key_prefix="cmp_pb",
        default_players=MADRID_PLAYERS if demo_loaded else None,
    )

    st.markdown("---")
    if analyze_button("cmp_analyze_teams", "⚖️ Compare Teams"):
        _compare_teams(
            players_a, players_b,
            team_a_name, team_b_name,
            team_a_color, team_b_color,
            form_a, form_b,
        )


def _compare_teams(players_a, players_b, team_a_name, team_b_name,
                   team_a_color, team_b_color, form_a, form_b):
    """Run analysis on both teams and compare results."""
    with st.spinner("⚖️ Comparing teams..."):
        # Space control
        sc_result = analyze_space_control({
            "input_type": "manual",
            "team_a": players_a, "team_b": players_b,
            "team_a_name": team_a_name, "team_b_name": team_b_name,
            "team_a_color": team_a_color, "team_b_color": team_b_color,
            "ball_x": 60.0, "ball_y": 40.0, "mode": "both",
        })

        # Formation detection
        fm_result = analyze_formation({
            "input_type": "manual",
            "team_a": players_a, "team_b": players_b,
            "team_a_name": team_a_name, "team_b_name": team_b_name,
            "team_a_color": team_a_color, "team_b_color": team_b_color,
            "method": "auto",
        })

        # Patterns
        pt_result = analyze_patterns({
            "input_type": "manual",
            "team_a": players_a, "team_b": players_b,
            "team_a_name": team_a_name, "team_b_name": team_b_name,
            "team_a_color": team_a_color, "team_b_color": team_b_color,
            "analyze_team": "both",
        })

        # Build comparison result
        a_control = sc_result.get("team_a_control", 50) if sc_result.get("success") else 50
        b_control = sc_result.get("team_b_control", 50) if sc_result.get("success") else 50

        det_form_a = fm_result.get("team_a_formation", form_a) if fm_result.get("success") else form_a
        det_form_b = fm_result.get("team_b_formation", form_b) if fm_result.get("success") else form_b

        patterns_a = pt_result.get("team_a_patterns", []) if pt_result.get("success") else []
        patterns_b = pt_result.get("team_b_patterns", []) if pt_result.get("success") else []
        detected_a = [p["name"] for p in patterns_a if p.get("detected")]
        detected_b = [p["name"] for p in patterns_b if p.get("detected")]

        # Verdict
        verdict = _generate_verdict(
            team_a_name, team_b_name,
            det_form_a, det_form_b,
            a_control, b_control,
            detected_a, detected_b,
        )

        st.session_state.cmp_result = {
            "success": True,
            "type": "teams",
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
            "space_control": sc_result,
            "formation": fm_result,
            "patterns": pt_result,
            "metrics": {
                "team_a_control": a_control,
                "team_b_control": b_control,
                "formation_a": det_form_a,
                "formation_b": det_form_b,
                "patterns_a": detected_a,
                "patterns_b": detected_b,
            },
            "verdict": verdict,
        }
    st.rerun()


# ═══════════════════════════════════════════════════════════════
# Two Formations
# ═══════════════════════════════════════════════════════════════

def _render_two_formations(demo_loaded: bool):
    """Simple formation comparison using knowledge graph."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Formation A")
        form_a = st.selectbox("Select formation",
                              FORMATIONS, index=1 if demo_loaded else 0, key="cmp_ff_a")
    with c2:
        st.markdown("### Formation B")
        form_b = st.selectbox("Select formation",
                              FORMATIONS, index=0 if demo_loaded else 1, key="cmp_ff_b")

    st.markdown("---")
    if analyze_button("cmp_analyze_formations", "⚖️ Compare Formations"):
        _compare_formations(form_a, form_b)


def _compare_formations(form_a: str, form_b: str):
    """Compare two formations using knowledge graph."""
    with st.spinner("⚖️ Comparing formations..."):
        try:
            from engine.intelligence.knowledge_graph import TacticalKnowledgeGraph
            kg = TacticalKnowledgeGraph()

            weak_a = kg.get_formation_weaknesses(form_a)
            strong_a = kg.get_formation_strengths(form_a)
            weak_b = kg.get_formation_weaknesses(form_b)
            strong_b = kg.get_formation_strengths(form_b)

            # Build comparison
            differences = []
            a_strong_situations = {s["situation"] for s in strong_a}
            b_strong_situations = {s["situation"] for s in strong_b}
            a_weak_situations = {w["situation"] for w in weak_a}
            b_weak_situations = {w["situation"] for w in weak_b}

            # Where A is strong but B is weak
            a_advantages = a_strong_situations & b_weak_situations
            b_advantages = b_strong_situations & a_weak_situations

            for adv in a_advantages:
                differences.append(f"🟢 **{form_a}** has an advantage in **{adv.replace('_', ' ')}** where {form_b} is vulnerable")
            for adv in b_advantages:
                differences.append(f"🔴 **{form_b}** has an advantage in **{adv.replace('_', ' ')}** where {form_a} is vulnerable")

            verdict = _generate_verdict(
                form_a, form_b,
                form_a, form_b,
                50, 50,  # balanced by default
                [s["situation"] for s in strong_a],
                [s["situation"] for s in strong_b],
                formation_mode=True,
            )

            st.session_state.cmp_result = {
                "success": True,
                "type": "formations",
                "team_a_name": form_a,
                "team_b_name": form_b,
                "metrics": {
                    "formation_a": form_a,
                    "formation_b": form_b,
                    "strengths_a": [s["situation"].replace("_", " ").title() for s in strong_a],
                    "strengths_b": [s["situation"].replace("_", " ").title() for s in strong_b],
                    "weaknesses_a": [w["situation"].replace("_", " ").title() for w in weak_a],
                    "weaknesses_b": [w["situation"].replace("_", " ").title() for w in weak_b],
                },
                "differences": differences,
                "verdict": verdict,
            }
        except Exception as e:
            st.session_state.cmp_result = {"success": False, "error": str(e)}
    st.rerun()


# ═══════════════════════════════════════════════════════════════
# Two Tactical Setups
# ═══════════════════════════════════════════════════════════════

def _render_two_setups(demo_loaded: bool):
    """Compare formation + tactic preset combinations."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Setup A")
        form_a = st.selectbox("Formation", FORMATIONS,
                              index=1 if demo_loaded else 0, key="cmp_ts_fa")
        tactic_a = st.selectbox("Tactic", TACTICS,
                                index=TACTICS.index("possession") if demo_loaded else 0,
                                key="cmp_ts_ta",
                                format_func=lambda x: TACTIC_LABELS.get(x, x))
    with c2:
        st.markdown("### Setup B")
        form_b = st.selectbox("Formation", FORMATIONS,
                              index=0, key="cmp_ts_fb")
        tactic_b = st.selectbox("Tactic", TACTICS,
                                index=TACTICS.index("high_press") if demo_loaded else 0,
                                key="cmp_ts_tb",
                                format_func=lambda x: TACTIC_LABELS.get(x, x))

    st.markdown("---")
    if analyze_button("cmp_analyze_setups", "⚖️ Compare Setups"):
        _compare_setups(form_a, tactic_a, form_b, tactic_b)


def _compare_setups(form_a, tactic_a, form_b, tactic_b):
    """Compare two tactical setups using knowledge graph + simulation insights."""
    with st.spinner("⚖️ Comparing tactical setups..."):
        try:
            from engine.intelligence.knowledge_graph import TacticalKnowledgeGraph
            kg = TacticalKnowledgeGraph()

            # Map tactics to situations
            tactic_to_situation = {
                "high_press": "high_press",
                "low_block": "low_block",
                "possession": "possession_play",
                "counter_attack": "counter_attack",
                "wide_play": "wide_play",
                "narrow_play": "midfield_overload",
            }

            sit_a = tactic_to_situation.get(tactic_a, "possession_play")
            sit_b = tactic_to_situation.get(tactic_b, "low_block")

            result_a = kg.query(form_a, sit_b)  # A facing B's situation
            result_b = kg.query(form_b, sit_a)  # B facing A's situation

            counters_a = kg.get_counter_strategies(sit_b)
            counters_b = kg.get_counter_strategies(sit_a)

            differences = []
            if result_a.get("is_weak_against"):
                differences.append(f"⚠️ **{form_a} ({TACTIC_LABELS.get(tactic_a, tactic_a)})** is weak against {sit_b.replace('_', ' ')}")
            if result_a.get("is_strong_in"):
                differences.append(f"✅ **{form_a}** is strong in situations created by {sit_b.replace('_', ' ')}")
            if result_b.get("is_weak_against"):
                differences.append(f"⚠️ **{form_b} ({TACTIC_LABELS.get(tactic_b, tactic_b)})** is weak against {sit_a.replace('_', ' ')}")
            if result_b.get("is_strong_in"):
                differences.append(f"✅ **{form_b}** is strong in situations created by {sit_a.replace('_', ' ')}")

            label_a = f"{form_a} ({TACTIC_LABELS.get(tactic_a, tactic_a)})"
            label_b = f"{form_b} ({TACTIC_LABELS.get(tactic_b, tactic_b)})"

            verdict = _generate_verdict(
                label_a, label_b,
                form_a, form_b,
                50, 50,
                [c["strategy"] for c in counters_a],
                [c["strategy"] for c in counters_b],
                formation_mode=True,
            )

            st.session_state.cmp_result = {
                "success": True,
                "type": "setups",
                "team_a_name": label_a,
                "team_b_name": label_b,
                "metrics": {
                    "formation_a": form_a,
                    "formation_b": form_b,
                    "tactic_a": TACTIC_LABELS.get(tactic_a, tactic_a),
                    "tactic_b": TACTIC_LABELS.get(tactic_b, tactic_b),
                    "counters_a": [c["strategy"].replace("_", " ").title() for c in counters_a],
                    "counters_b": [c["strategy"].replace("_", " ").title() for c in counters_b],
                },
                "differences": differences,
                "verdict": verdict,
            }
        except Exception as e:
            st.session_state.cmp_result = {"success": False, "error": str(e)}
    st.rerun()


# ═══════════════════════════════════════════════════════════════
# Verdict generator
# ═══════════════════════════════════════════════════════════════

def _generate_verdict(name_a, name_b, form_a, form_b,
                      control_a, control_b,
                      items_a, items_b,
                      formation_mode=False) -> str:
    """Generate a comparison verdict using LLM or template."""

    summary = (
        f"Comparison: {name_a} vs {name_b}\n"
        f"Formation A: {form_a}, Formation B: {form_b}\n"
        f"Space Control: A={control_a:.1f}%, B={control_b:.1f}%\n"
        f"Key items A: {', '.join(str(x) for x in items_a[:5])}\n"
        f"Key items B: {', '.join(str(x) for x in items_b[:5])}"
    )

    llm_answer = call_openrouter(
        "You are SpaceAI FC, a football tactical analysis system. "
        "Write a concise tactical comparison verdict (3-5 sentences). "
        "Be specific about advantages and disadvantages.",
        summary,
    )

    if llm_answer:
        return llm_answer

    # Template fallback
    if control_a > control_b + 5:
        adv = f"**{name_a}** holds a space control advantage ({control_a:.0f}% vs {control_b:.0f}%)."
    elif control_b > control_a + 5:
        adv = f"**{name_b}** holds a space control advantage ({control_b:.0f}% vs {control_a:.0f}%)."
    else:
        adv = "Space control is evenly contested."

    a_count = len(items_a)
    b_count = len(items_b)
    if a_count > b_count:
        pattern_adv = f"**{name_a}** shows more tactical activity with {a_count} detected items vs {b_count}."
    elif b_count > a_count:
        pattern_adv = f"**{name_b}** shows more tactical activity with {b_count} detected items vs {a_count}."
    else:
        pattern_adv = "Both sides show similar levels of tactical activity."

    return f"{adv} {pattern_adv}"


# ═══════════════════════════════════════════════════════════════
# Results display
# ═══════════════════════════════════════════════════════════════

def _show_results():
    result = st.session_state.get("cmp_result")
    if result is None:
        return
    if not check_result(result):
        return

    st.markdown("---")
    cmp_type = result.get("type", "teams")
    team_a = result.get("team_a_name", "A")
    team_b = result.get("team_b_name", "B")
    metrics = result.get("metrics", {})

    # ── Header ────────────────────────────────────────────────
    section_title(f"⚖️ {team_a} vs {team_b}")

    # ── Comparison metrics table ──────────────────────────────
    if cmp_type == "teams":
        _show_team_comparison(result, team_a, team_b, metrics)
    elif cmp_type == "formations":
        _show_formation_comparison(team_a, team_b, metrics)
    else:
        _show_setup_comparison(team_a, team_b, metrics)

    # ── Key differences ───────────────────────────────────────
    diffs = result.get("differences", [])
    if diffs:
        section_title("📌 Key Differences")
        for d in diffs:
            st.markdown(
                f'<div class="insight-card">{d}</div>',
                unsafe_allow_html=True,
            )

    # ── Verdict ───────────────────────────────────────────────
    verdict = result.get("verdict", "")
    if verdict:
        section_title("📋 Verdict")
        # Mode badge
        if is_llm_available():
            badge = ('<div style="display:inline-block;background:#1B5E20;color:#FFD700;'
                     'padding:4px 12px;border-radius:20px;font-size:0.72rem;font-weight:600;'
                     'margin-bottom:8px">AI Mode (Claude)</div>')
        else:
            badge = ('<div style="display:inline-block;background:#E8F5E9;color:#1B5E20;'
                     'padding:4px 12px;border-radius:20px;font-size:0.72rem;font-weight:600;'
                     'margin-bottom:8px">Template Mode</div>')
        st.markdown(badge, unsafe_allow_html=True)
        st.markdown(
            f'<div class="result-card" style="line-height:1.7">{verdict}</div>',
            unsafe_allow_html=True,
        )

    # ── Visualizations from team comparison ───────────────────
    if cmp_type == "teams":
        sc = result.get("space_control", {})
        if sc.get("success"):
            show_visualizations(sc.get("visualizations", []), cols=2)
        fm = result.get("formation", {})
        if fm.get("success"):
            show_visualizations(fm.get("visualizations", []), cols=2)


def _show_team_comparison(result, team_a, team_b, metrics):
    """Display team comparison metrics with color coding."""
    a_ctrl = metrics.get("team_a_control", 50)
    b_ctrl = metrics.get("team_b_control", 50)
    form_a = metrics.get("formation_a", "?")
    form_b = metrics.get("formation_b", "?")
    patt_a = len(metrics.get("patterns_a", []))
    patt_b = len(metrics.get("patterns_b", []))

    # Metrics row
    metric_row([
        (f"{team_a} Control", f"{a_ctrl:.1f}%"),
        (f"{team_b} Control", f"{b_ctrl:.1f}%"),
        (f"{team_a} Formation", form_a),
        (f"{team_b} Formation", form_b),
    ])

    # Comparison table
    st.markdown("---")
    rows = [
        ("Space Control", f"{a_ctrl:.1f}%", f"{b_ctrl:.1f}%", a_ctrl > b_ctrl),
        ("Formation", form_a, form_b, None),
        ("Patterns Detected", str(patt_a), str(patt_b), patt_a > patt_b),
    ]

    table_html = (
        '<table style="width:100%;border-collapse:collapse;margin:8px 0">'
        '<tr style="background:#1B5E20;color:white">'
        f'<th style="padding:10px 16px;text-align:left">Metric</th>'
        f'<th style="padding:10px 16px;text-align:center">{team_a}</th>'
        f'<th style="padding:10px 16px;text-align:center">{team_b}</th>'
        '</tr>'
    )
    for label, val_a, val_b, a_better in rows:
        color_a = "#E8F5E9" if a_better is True else ("#FFEBEE" if a_better is False else "white")
        color_b = "#E8F5E9" if a_better is False else ("#FFEBEE" if a_better is True else "white")
        table_html += (
            f'<tr>'
            f'<td style="padding:10px 16px;border-bottom:1px solid #E0E0E0;font-weight:600">{label}</td>'
            f'<td style="padding:10px 16px;border-bottom:1px solid #E0E0E0;text-align:center;'
            f'background:{color_a}">{val_a}</td>'
            f'<td style="padding:10px 16px;border-bottom:1px solid #E0E0E0;text-align:center;'
            f'background:{color_b}">{val_b}</td>'
            f'</tr>'
        )
    table_html += '</table>'
    st.markdown(table_html, unsafe_allow_html=True)


def _show_formation_comparison(form_a, form_b, metrics):
    """Display formation comparison."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### {form_a}")
        strengths = metrics.get("strengths_a", [])
        weaknesses = metrics.get("weaknesses_a", [])
        if strengths:
            st.markdown("**Strengths:**")
            for s in strengths:
                st.markdown(f'<div class="insight-card">✅ {s}</div>', unsafe_allow_html=True)
        if weaknesses:
            st.markdown("**Weaknesses:**")
            for w in weaknesses:
                st.markdown(f'<div class="warning-card">⚠️ {w}</div>', unsafe_allow_html=True)

    with c2:
        st.markdown(f"### {form_b}")
        strengths = metrics.get("strengths_b", [])
        weaknesses = metrics.get("weaknesses_b", [])
        if strengths:
            st.markdown("**Strengths:**")
            for s in strengths:
                st.markdown(f'<div class="insight-card">✅ {s}</div>', unsafe_allow_html=True)
        if weaknesses:
            st.markdown("**Weaknesses:**")
            for w in weaknesses:
                st.markdown(f'<div class="warning-card">⚠️ {w}</div>', unsafe_allow_html=True)


def _show_setup_comparison(label_a, label_b, metrics):
    """Display tactical setup comparison."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### {label_a}")
        st.markdown(f"**Formation:** {metrics.get('formation_a', '?')}")
        st.markdown(f"**Tactic:** {metrics.get('tactic_a', '?')}")
        counters = metrics.get("counters_a", [])
        if counters:
            st.markdown("**Counter strategies available:**")
            for c in counters[:5]:
                st.markdown(f'<div class="insight-card">🎯 {c}</div>', unsafe_allow_html=True)

    with c2:
        st.markdown(f"### {label_b}")
        st.markdown(f"**Formation:** {metrics.get('formation_b', '?')}")
        st.markdown(f"**Tactic:** {metrics.get('tactic_b', '?')}")
        counters = metrics.get("counters_b", [])
        if counters:
            st.markdown("**Counter strategies available:**")
            for c in counters[:5]:
                st.markdown(f'<div class="insight-card">🎯 {c}</div>', unsafe_allow_html=True)
