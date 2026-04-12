"""
SpaceAI FC - Simulation Page
================================
Feature 11: Run tactical simulations (5v5, 7v7) with different
tactic preset matchups.
"""

import streamlit as st
import numpy as np

from app.components.theme import page_header, section_title
from app.components.input_forms import demo_button, analyze_button
from app.components.results_display import check_result, metric_row, show_visualizations
from app.utils.api_client import run_simulation
from app.demo_data import TACTICS


TACTIC_LABELS = {
    "high_press": "High Press",
    "low_block": "Low Block",
    "possession": "Possession",
    "counter_attack": "Counter-Attack",
    "wide_play": "Wide Play",
    "narrow_play": "Narrow Play",
}

TACTIC_DESCRIPTIONS = {
    "high_press": "Aggressive pressing high up the pitch to win the ball early",
    "low_block": "Compact defensive shape sitting deep to absorb pressure",
    "possession": "Patient build-up play prioritizing ball retention",
    "counter_attack": "Quick vertical attacks after winning possession",
    "wide_play": "Stretching the pitch using width to create space",
    "narrow_play": "Compact central play overloading midfield zones",
}


def render():
    page_header(
        "🎮", "Tactical Simulation",
        "Run multi-agent tactical simulations — test different strategies, "
        "compare results across multiple runs, and find the optimal approach.",
    )

    # ── Session state ────────────────────────────────────────────
    if "sim_result" not in st.session_state:
        st.session_state.sim_result = None
    if "sim_multi_results" not in st.session_state:
        st.session_state.sim_multi_results = None

    # ── Input form ───────────────────────────────────────────────
    st.markdown("### Simulation Setup")

    c1, c2, c3 = st.columns(3)
    with c1:
        team_size = st.selectbox("Team size", [5, 7], index=0, key="sim_size",
                                  format_func=lambda x: f"{x}v{x}")
    with c2:
        tactic_a = st.selectbox("Team A tactic", TACTICS, index=0, key="sim_ta",
                                 format_func=lambda x: TACTIC_LABELS.get(x, x))
    with c3:
        tactic_b = st.selectbox("Team B tactic", TACTICS, index=1, key="sim_tb",
                                 format_func=lambda x: TACTIC_LABELS.get(x, x))

    # Tactic descriptions
    tc1, tc2 = st.columns(2)
    with tc1:
        st.caption(f"📋 {TACTIC_LABELS.get(tactic_a, tactic_a)}: {TACTIC_DESCRIPTIONS.get(tactic_a, '')}")
    with tc2:
        st.caption(f"📋 {TACTIC_LABELS.get(tactic_b, tactic_b)}: {TACTIC_DESCRIPTIONS.get(tactic_b, '')}")

    st.markdown("---")

    c4, c5 = st.columns(2)
    with c4:
        steps = st.slider("Simulation steps", 100, 500, 300, 50, key="sim_steps",
                           help="More steps = longer match simulation")
    with c5:
        num_runs = st.slider("Number of runs", 1, 10, 5, key="sim_runs",
                              help="Multiple runs average out randomness")

    st.markdown("---")

    # ── Buttons ──────────────────────────────────────────────────
    bc1, bc2 = st.columns(2)
    with bc1:
        if analyze_button("sim_run", "🎮 Run Simulation"):
            _run_simulation(team_size, tactic_a, tactic_b, steps, num_runs)

    with bc2:
        st.markdown('<div class="demo-btn">', unsafe_allow_html=True)
        if st.button("⚡ Quick Compare: High Press vs Low Block", key="sim_quick"):
            _run_simulation(5, "high_press", "low_block", 300, 5)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Results ──────────────────────────────────────────────────
    _show_results()


def _run_simulation(team_size, tactic_a, tactic_b, steps, num_runs):
    """Run one or multiple simulations via the API or directly."""

    if num_runs == 1:
        # Single run via API
        with st.spinner(f"🎮 Running {team_size}v{team_size} simulation ({steps} steps)..."):
            result = run_simulation({
                "team_size": team_size,
                "tactic_a": tactic_a,
                "tactic_b": tactic_b,
                "steps": steps,
                "seed": 42,
            })

            if result.get("success"):
                st.session_state.sim_result = result
                st.session_state.sim_multi_results = None
            else:
                # Try running directly if API is down
                st.session_state.sim_result = _run_direct(team_size, tactic_a, tactic_b, steps, 42)
                st.session_state.sim_multi_results = None
    else:
        # Multiple runs
        with st.spinner(f"🎮 Running {num_runs} simulations ({team_size}v{team_size}, {steps} steps each)..."):
            all_results = []
            for i in range(num_runs):
                result = run_simulation({
                    "team_size": team_size,
                    "tactic_a": tactic_a,
                    "tactic_b": tactic_b,
                    "steps": steps,
                    "seed": 42 + i,
                })
                if result.get("success"):
                    all_results.append(result)
                else:
                    # Direct fallback
                    direct = _run_direct(team_size, tactic_a, tactic_b, steps, 42 + i)
                    if direct and direct.get("success"):
                        all_results.append(direct)

            if all_results:
                st.session_state.sim_result = all_results[0]  # show first run details
                st.session_state.sim_multi_results = all_results
            else:
                st.session_state.sim_result = {"success": False, "error": "All simulation runs failed."}
                st.session_state.sim_multi_results = None

    st.rerun()


def _run_direct(team_size, tactic_a, tactic_b, steps, seed):
    """Run simulation directly using the engine (fallback when API is down)."""
    try:
        from engine.intelligence.simulation import TacticalSimulation
        sim = TacticalSimulation(team_size=team_size, max_steps=steps, seed=seed)
        sim.set_tactics(tactic_a, tactic_b)
        stats = sim.run(n_steps=steps)

        # Generate a frame snapshot
        frame_b64 = _generate_frame_image(sim, steps // 2)

        return {
            "success": True,
            "tactic_a": stats.get("tactic_a", tactic_a),
            "tactic_b": stats.get("tactic_b", tactic_b),
            "goals_a": stats.get("goals_a", 0),
            "goals_b": stats.get("goals_b", 0),
            "possession_a": round(stats.get("possession_a", 50.0), 1),
            "possession_b": round(stats.get("possession_b", 50.0), 1),
            "territorial_control_a": round(stats.get("territorial_control_a", 50.0), 1),
            "steps": steps,
            "events": stats.get("events", [])[:20],
            "frame_base64": frame_b64,
        }
    except Exception as e:
        return {"success": False, "error": f"Direct simulation failed: {e}"}


def _generate_frame_image(sim, step):
    """Generate a frame image and return as base64."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import base64
        from io import BytesIO

        fig, ax = sim.draw_frame(step=step)

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
    except Exception:
        return None


def _show_results():
    result = st.session_state.get("sim_result")
    if result is None:
        return
    if not check_result(result):
        return

    st.markdown("---")

    tactic_a = result.get("tactic_a", "Team A")
    tactic_b = result.get("tactic_b", "Team B")
    goals_a = result.get("goals_a", 0)
    goals_b = result.get("goals_b", 0)

    # ── Scoreboard ────────────────────────────────────────────
    section_title("🏆 Simulation Result")

    winner = tactic_a if goals_a > goals_b else (tactic_b if goals_b > goals_a else "Draw")
    winner_color = "#FFD700" if winner != "Draw" else "#aaaaaa"

    st.markdown(
        f'<div style="text-align:center;padding:24px;background:linear-gradient(135deg,#1B5E20,#2E7D32);'
        f'border-radius:12px;margin-bottom:16px">'
        f'<div style="color:rgba(255,255,255,0.7);font-size:0.8rem;letter-spacing:1px;margin-bottom:6px">'
        f'TACTICAL SIMULATION</div>'
        f'<div style="color:white;font-size:2.2rem;font-weight:800;letter-spacing:2px">'
        f'{tactic_a} <span style="color:#FFD700">{goals_a} – {goals_b}</span> {tactic_b}</div>'
        f'<div style="color:{winner_color};font-size:0.95rem;font-weight:600;margin-top:8px">'
        f'{"🏆 " + winner + " wins!" if winner != "Draw" else "⚖️ Match ended in a draw"}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Stats ─────────────────────────────────────────────────
    poss_a = result.get("possession_a", 50)
    poss_b = 100 - poss_a
    terr_a = result.get("territorial_control_a", 50)
    terr_b = 100 - terr_a

    metric_row([
        (f"{tactic_a} Possession", f"{poss_a:.0f}%"),
        (f"{tactic_b} Possession", f"{poss_b:.0f}%"),
        (f"{tactic_a} Territory", f"{terr_a:.0f}%"),
        ("Steps", str(result.get("steps", 0))),
    ])

    # ── Stats table ───────────────────────────────────────────
    section_title("📊 Match Statistics")

    table_data = [
        ("Goals", str(goals_a), str(goals_b)),
        ("Possession", f"{poss_a:.0f}%", f"{poss_b:.0f}%"),
        ("Territorial Control", f"{terr_a:.0f}%", f"{terr_b:.0f}%"),
    ]

    table_html = (
        '<table style="width:100%;border-collapse:collapse;margin:8px 0">'
        f'<tr style="background:#1B5E20;color:white">'
        f'<th style="padding:10px 16px;text-align:left">Stat</th>'
        f'<th style="padding:10px 16px;text-align:center">{tactic_a}</th>'
        f'<th style="padding:10px 16px;text-align:center">{tactic_b}</th>'
        f'</tr>'
    )
    for label, val_a, val_b in table_data:
        table_html += (
            f'<tr>'
            f'<td style="padding:10px 16px;border-bottom:1px solid #E0E0E0;font-weight:600">{label}</td>'
            f'<td style="padding:10px 16px;border-bottom:1px solid #E0E0E0;text-align:center">{val_a}</td>'
            f'<td style="padding:10px 16px;border-bottom:1px solid #E0E0E0;text-align:center">{val_b}</td>'
            f'</tr>'
        )
    table_html += '</table>'
    st.markdown(table_html, unsafe_allow_html=True)

    # ── Frame snapshot ────────────────────────────────────────
    frame_b64 = result.get("frame_base64")
    if frame_b64:
        section_title("🖼️ Simulation Snapshot")
        from app.utils.api_client import base64_to_image
        img = base64_to_image(frame_b64)
        st.image(img, caption="Simulation frame snapshot", use_container_width=True)

    # ── Events ────────────────────────────────────────────────
    events = result.get("events", [])
    if events:
        section_title("⚡ Match Events")
        for ev in events:
            icon = "⚽" if ev.get("type") == "goal" else "📌"
            team = ev.get("team", "?")
            step = ev.get("step", "?")
            st.markdown(
                f'<div class="insight-card">{icon} Step {step} — '
                f'Team {team} {ev.get("type", "event").title()}</div>',
                unsafe_allow_html=True,
            )

    # ── Multi-run results ─────────────────────────────────────
    multi = st.session_state.get("sim_multi_results")
    if multi and len(multi) > 1:
        section_title(f"📈 Multi-Run Results ({len(multi)} runs)")

        wins_a = sum(1 for r in multi if r.get("goals_a", 0) > r.get("goals_b", 0))
        wins_b = sum(1 for r in multi if r.get("goals_b", 0) > r.get("goals_a", 0))
        draws = sum(1 for r in multi if r.get("goals_a", 0) == r.get("goals_b", 0))

        avg_goals_a = np.mean([r.get("goals_a", 0) for r in multi])
        avg_goals_b = np.mean([r.get("goals_b", 0) for r in multi])
        avg_poss_a = np.mean([r.get("possession_a", 50) for r in multi])
        avg_terr_a = np.mean([r.get("territorial_control_a", 50) for r in multi])

        # W/D/L bar
        total = len(multi)
        w_pct = wins_a / total * 100
        d_pct = draws / total * 100
        l_pct = wins_b / total * 100

        st.markdown(
            f'<div style="display:flex;border-radius:8px;overflow:hidden;height:32px;margin-bottom:16px">'
            f'<div style="background:#2E7D32;width:{w_pct}%;display:flex;align-items:center;'
            f'justify-content:center;color:white;font-weight:700;font-size:0.85rem">'
            f'{wins_a}W</div>'
            f'<div style="background:#F57F17;width:{d_pct}%;display:flex;align-items:center;'
            f'justify-content:center;color:white;font-weight:700;font-size:0.85rem">'
            f'{draws}D</div>'
            f'<div style="background:#C62828;width:{l_pct}%;display:flex;align-items:center;'
            f'justify-content:center;color:white;font-weight:700;font-size:0.85rem">'
            f'{wins_b}L</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        metric_row([
            ("Record", f"{wins_a}W / {draws}D / {wins_b}L"),
            ("Avg Goals (A)", f"{avg_goals_a:.1f}"),
            ("Avg Goals (B)", f"{avg_goals_b:.1f}"),
            ("Avg Possession (A)", f"{avg_poss_a:.0f}%"),
        ])

        # Per-run breakdown
        with st.expander("Per-run breakdown"):
            for idx, r in enumerate(multi):
                ga = r.get("goals_a", 0)
                gb = r.get("goals_b", 0)
                result_emoji = "🟢" if ga > gb else ("🔴" if gb > ga else "⚖️")
                st.markdown(
                    f'{result_emoji} **Run {idx+1}:** {tactic_a} {ga} – {gb} {tactic_b} '
                    f'(Possession: {r.get("possession_a", 50):.0f}%)'
                )

        # ── Tactical insight ──────────────────────────────────
        section_title("💡 Tactical Insight")
        if wins_a > wins_b:
            insight = (
                f"**{tactic_a}** outperformed **{tactic_b}** across {len(multi)} simulations, "
                f"winning {wins_a} out of {total} matches. With an average possession of "
                f"{avg_poss_a:.0f}% and {avg_goals_a:.1f} goals per match, the "
                f"{tactic_a.lower()} approach proved more effective in this matchup."
            )
        elif wins_b > wins_a:
            insight = (
                f"**{tactic_b}** proved superior to **{tactic_a}** across {len(multi)} simulations, "
                f"winning {wins_b} out of {total} matches. Despite {tactic_a}'s average possession of "
                f"{avg_poss_a:.0f}%, {tactic_b} was more clinical, averaging "
                f"{avg_goals_b:.1f} goals per match."
            )
        else:
            insight = (
                f"**{tactic_a}** and **{tactic_b}** are evenly matched in this simulation series, "
                f"with {wins_a} wins each and {draws} draws across {total} runs. "
                f"Consider adjusting parameters or trying different tactical combinations."
            )

        st.markdown(
            f'<div class="insight-card">{insight}</div>',
            unsafe_allow_html=True,
        )
