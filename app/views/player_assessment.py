"""
SpaceAI FC - Player Assessment Page
=====================================
Feature 8: Evaluate individual players with stats, role classification,
radar charts, and AI-powered scouting reports.
"""

import streamlit as st
import math
import numpy as np

from app.components.theme import page_header, section_title, result_card
from app.components.input_forms import (
    demo_button, analyze_button, video_input_tab, dataset_input_tab,
)
from app.components.results_display import check_result, show_visualizations
from app.utils.api_client import upload_video, process_youtube
from app.utils.llm_client import call_openrouter, is_llm_available
from app.demo_data import POSITIONS, FORMATIONS


# ── Pedri demo profile ──────────────────────────────────────────

PEDRI_DEMO = {
    "name": "Pedri",
    "number": 8,
    "age": 23,
    "foot": "Right",
    "position": "CM",
    "height": 174,
    "weight": 60,
    "team_name": "FC Barcelona",
    "formation": "4-2-3-1",
    "player_x": 45.0,
    "player_y": 48.0,
    "speed": 72,
    "acceleration": 75,
    "stamina": 88,
    "strength": 55,
    "passing": 92,
    "dribbling": 85,
    "shooting": 65,
    "crossing": 70,
    "first_touch": 91,
    "positioning": 88,
    "vision": 93,
    "work_rate": 90,
    "pressing": 78,
    "decision_making": 91,
    "strengths": "Exceptional passing range and vision. Maintains composure under pressure. Elite first touch and ball retention. High football IQ with quick decision-making.",
    "weaknesses": "Lacks physicality against stronger midfielders. Can be outmuscled in aerial duels. Shooting from distance needs improvement.",
    "tactical_notes": "Operates as a deep-lying playmaker who drifts between the lines. Key to Barcelona's build-up play. Best used in a double pivot where a more physical partner provides defensive cover.",
}


def render():
    page_header(
        "👤", "Player Assessment",
        "Evaluate individual players — role classification, stat analysis, "
        "radar charts, and AI-powered scouting reports.",
    )

    # ── Session state ─────────────────────────────────────────────
    if "pa_result" not in st.session_state:
        st.session_state.pa_result = None
    if "pa_demo_loaded" not in st.session_state:
        st.session_state.pa_demo_loaded = False

    tab_manual, tab_video, tab_dataset = st.tabs(
        ["✏️ Manual Entry", "🎬 Video / YouTube", "📂 Dataset Upload"]
    )

    # ── Manual tab ────────────────────────────────────────────────
    with tab_manual:
        col_demo, _ = st.columns([1, 3])
        with col_demo:
            if demo_button("pa_demo"):
                st.session_state.pa_demo_loaded = True
                st.rerun()

        d = PEDRI_DEMO if st.session_state.pa_demo_loaded else {}

        # ── Basic info ─────────────────────────────────────────
        st.markdown("### Player Information")
        c1, c2, c3, c4 = st.columns([3, 1, 1, 2])
        name     = c1.text_input("Player name", value=d.get("name", ""), key="pa_name")
        number   = c2.number_input("Jersey #", value=d.get("number", 7), min_value=1, max_value=99, key="pa_num")
        age      = c3.number_input("Age", value=d.get("age", 25), min_value=15, max_value=45, key="pa_age")
        foot     = c4.selectbox("Preferred foot", ["Right", "Left", "Both"],
                                index=["Right", "Left", "Both"].index(d.get("foot", "Right")),
                                key="pa_foot")

        c5, c6, c7 = st.columns([2, 1, 1])
        pos_list = ["GK", "CB", "RB", "LB", "CDM", "CM", "CAM", "RW", "LW", "ST"]
        pos_idx  = pos_list.index(d.get("position", "CM")) if d.get("position", "CM") in pos_list else 5
        position = c5.selectbox("Position", pos_list, index=pos_idx, key="pa_pos")
        height   = c6.number_input("Height (cm)", value=d.get("height", 180), min_value=150, max_value=210, key="pa_ht")
        weight   = c7.number_input("Weight (kg)", value=d.get("weight", 75), min_value=50, max_value=120, key="pa_wt")

        st.markdown("---")

        # ── Physical stats ─────────────────────────────────────
        st.markdown("### Physical Stats")
        pc1, pc2, pc3, pc4 = st.columns(4)
        speed        = pc1.slider("Speed",        1, 100, d.get("speed", 70),        key="pa_spd")
        acceleration = pc2.slider("Acceleration", 1, 100, d.get("acceleration", 70), key="pa_acc")
        stamina      = pc3.slider("Stamina",      1, 100, d.get("stamina", 70),      key="pa_stm")
        strength     = pc4.slider("Strength",     1, 100, d.get("strength", 70),     key="pa_str")

        # ── Technical stats ─────────────────────────────────────
        st.markdown("### Technical Stats")
        tc1, tc2, tc3, tc4, tc5 = st.columns(5)
        passing     = tc1.slider("Passing",     1, 100, d.get("passing", 70),     key="pa_pas")
        dribbling   = tc2.slider("Dribbling",   1, 100, d.get("dribbling", 70),   key="pa_drb")
        shooting    = tc3.slider("Shooting",    1, 100, d.get("shooting", 70),    key="pa_sht")
        crossing    = tc4.slider("Crossing",    1, 100, d.get("crossing", 70),    key="pa_crs")
        first_touch = tc5.slider("First Touch", 1, 100, d.get("first_touch", 70), key="pa_ft")

        # ── Tactical stats ──────────────────────────────────────
        st.markdown("### Tactical Stats")
        ta1, ta2, ta3, ta4, ta5 = st.columns(5)
        positioning     = ta1.slider("Positioning",      1, 100, d.get("positioning", 70),     key="pa_psn")
        vision          = ta2.slider("Vision",           1, 100, d.get("vision", 70),          key="pa_vis")
        work_rate       = ta3.slider("Work Rate",        1, 100, d.get("work_rate", 70),       key="pa_wr")
        pressing        = ta4.slider("Pressing Intensity", 1, 100, d.get("pressing", 70),     key="pa_prs")
        decision_making = ta5.slider("Decision Making",  1, 100, d.get("decision_making", 70), key="pa_dm")

        st.markdown("---")

        # ── Qualitative notes ────────────────────────────────────
        st.markdown("### Scouting Notes")
        strengths_text = st.text_area("Strengths", value=d.get("strengths", ""), height=80, key="pa_strengths")
        weaknesses_text = st.text_area("Weaknesses", value=d.get("weaknesses", ""), height=80, key="pa_weaknesses")
        tactical_notes = st.text_area("Tactical notes", value=d.get("tactical_notes", ""), height=80, key="pa_notes")

        st.markdown("---")

        # ── Team context ─────────────────────────────────────────
        st.markdown("### Team Context")
        ctx1, ctx2, ctx3, ctx4 = st.columns([3, 2, 1, 1])
        team_name  = ctx1.text_input("Team name", value=d.get("team_name", ""), key="pa_team")
        formation  = ctx2.selectbox("Formation", FORMATIONS,
                                     index=FORMATIONS.index(d.get("formation", "4-3-3")) if d.get("formation", "4-3-3") in FORMATIONS else 0,
                                     key="pa_form")
        player_x   = ctx3.number_input("X position", 0.0, 120.0, float(d.get("player_x", 60.0)), 0.5, key="pa_px")
        player_y   = ctx4.number_input("Y position", 0.0, 80.0, float(d.get("player_y", 40.0)), 0.5, key="pa_py")

        st.markdown("---")

        player_data = {
            "name": name, "number": int(number), "age": int(age),
            "foot": foot, "position": position,
            "height": int(height), "weight": int(weight),
            "physical": {"speed": speed, "acceleration": acceleration,
                         "stamina": stamina, "strength": strength},
            "technical": {"passing": passing, "dribbling": dribbling,
                          "shooting": shooting, "crossing": crossing,
                          "first_touch": first_touch},
            "tactical": {"positioning": positioning, "vision": vision,
                         "work_rate": work_rate, "pressing": pressing,
                         "decision_making": decision_making},
            "strengths": strengths_text, "weaknesses": weaknesses_text,
            "tactical_notes": tactical_notes,
            "team": {"name": team_name, "formation": formation,
                     "x": player_x, "y": player_y},
        }

        if analyze_button("pa_analyze", "👤 Assess Player"):
            _run_assessment(player_data)

    # ── Video tab ─────────────────────────────────────────────────
    with tab_video:
        st.info(
            "Upload a player clip or provide a YouTube URL. "
            "After processing, physical metrics (distance, speed) will be extracted. "
            "You can also fill in stats manually alongside video data."
        )
        vid = video_input_tab("pa_vid")
        if analyze_button("pa_analyze_vid", "👤 Process Video & Assess"):
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
                    f"✅ Video processed — {td.get('frames_processed', 0)} frames "
                    f"({td.get('method', '?')})"
                )
                # Build basic player data from video tracking
                video_player = {
                    "name": "Unknown Player", "number": 0, "age": 25,
                    "foot": "Right", "position": "CM",
                    "height": 180, "weight": 75,
                    "physical": {"speed": 70, "acceleration": 70, "stamina": 70, "strength": 70},
                    "technical": {"passing": 70, "dribbling": 70, "shooting": 70, "crossing": 70, "first_touch": 70},
                    "tactical": {"positioning": 70, "vision": 70, "work_rate": 70, "pressing": 70, "decision_making": 70},
                    "strengths": "", "weaknesses": "", "tactical_notes": "",
                    "team": {"name": "Team A", "formation": "4-3-3", "x": 60.0, "y": 40.0},
                    "video_data": td,
                }
                _run_assessment(video_player)
            elif tracking:
                st.error(f"Video error: {tracking.get('error', 'Unknown')}")

    # ── Dataset tab ───────────────────────────────────────────────
    with tab_dataset:
        ds = dataset_input_tab("pa_ds")
        if ds.get("file_bytes"):
            st.info("Dataset loaded. Use Manual Entry tab to fill in stats for the player you want to assess.")

    # ── Results ───────────────────────────────────────────────────
    _show_results()


def _run_assessment(player_data: dict):
    """Run player assessment using the engine's role classifier + LLM scouting report."""
    with st.spinner("👤 Assessing player..."):
        # ── Role classification using engine ──────────────────
        try:
            from engine.analysis.role_classifier import RoleClassifier
            rc = RoleClassifier()
            player_for_rc = {
                "name": player_data["name"],
                "number": player_data["number"],
                "x": player_data["team"]["x"],
                "y": player_data["team"]["y"],
                "position": player_data["position"],
            }
            rc.set_team([player_for_rc], team_name=player_data["team"].get("name", "Team"))
            role_results = rc.classify_all()
            role_info = role_results[0] if role_results else None
        except Exception:
            role_info = None

        # ── Radar chart ──────────────────────────────────────
        radar_b64 = _create_radar_chart(player_data)

        # ── Scouting report ──────────────────────────────────
        scouting_report = _generate_scouting_report(player_data, role_info)

        # ── Store result ─────────────────────────────────────
        st.session_state.pa_result = {
            "success": True,
            "player": player_data,
            "role": role_info,
            "radar_base64": radar_b64,
            "scouting_report": scouting_report,
        }
    st.rerun()


def _create_radar_chart(player_data: dict) -> str | None:
    """Create a matplotlib radar chart and return as base64 PNG."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import base64
        from io import BytesIO

        # Collect all stats
        phys = player_data.get("physical", {})
        tech = player_data.get("technical", {})
        tact = player_data.get("tactical", {})

        labels = [
            "Speed", "Acceleration", "Stamina", "Strength",
            "Passing", "Dribbling", "Shooting", "Crossing", "First Touch",
            "Positioning", "Vision", "Work Rate", "Pressing", "Decision Making",
        ]
        values = [
            phys.get("speed", 50), phys.get("acceleration", 50),
            phys.get("stamina", 50), phys.get("strength", 50),
            tech.get("passing", 50), tech.get("dribbling", 50),
            tech.get("shooting", 50), tech.get("crossing", 50),
            tech.get("first_touch", 50),
            tact.get("positioning", 50), tact.get("vision", 50),
            tact.get("work_rate", 50), tact.get("pressing", 50),
            tact.get("decision_making", 50),
        ]

        N = len(labels)
        angles = [n / float(N) * 2 * math.pi for n in range(N)]
        angles += angles[:1]
        values += values[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#1a1a2e")

        # Draw the radar
        ax.plot(angles, values, "o-", linewidth=2, color="#FFD700", markersize=6)
        ax.fill(angles, values, alpha=0.25, color="#FFD700")

        # Grid and labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, color="white", fontsize=8, fontweight="bold")
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(["20", "40", "60", "80", "100"],
                           color="#888888", fontsize=7)
        ax.set_ylim(0, 100)
        ax.spines["polar"].set_color("#444444")
        ax.grid(color="#444444", linewidth=0.5)
        ax.tick_params(axis="x", pad=15)

        # Title
        name = player_data.get("name", "Player")
        pos = player_data.get("position", "")
        fig.suptitle(f"{name} — {pos} Radar Profile",
                     color="white", fontsize=14, fontweight="bold", y=0.98)

        # Category averages annotation
        phys_avg = round(np.mean([phys.get("speed", 50), phys.get("acceleration", 50),
                                   phys.get("stamina", 50), phys.get("strength", 50)]))
        tech_avg = round(np.mean([tech.get("passing", 50), tech.get("dribbling", 50),
                                   tech.get("shooting", 50), tech.get("crossing", 50),
                                   tech.get("first_touch", 50)]))
        tact_avg = round(np.mean([tact.get("positioning", 50), tact.get("vision", 50),
                                   tact.get("work_rate", 50), tact.get("pressing", 50),
                                   tact.get("decision_making", 50)]))
        overall = round(np.mean(values[:-1]))

        fig.text(0.5, 0.02,
                 f"Physical: {phys_avg}  |  Technical: {tech_avg}  |  "
                 f"Tactical: {tact_avg}  |  Overall: {overall}",
                 ha="center", color="#aaaaaa", fontsize=9)

        # Convert to base64
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    except Exception:
        return None


def _generate_scouting_report(player_data: dict, role_info: dict | None) -> str:
    """Generate a scouting report using LLM or template fallback."""

    name = player_data.get("name", "Unknown")
    pos = player_data.get("position", "")
    age = player_data.get("age", "")
    foot = player_data.get("foot", "")
    team = player_data.get("team", {}).get("name", "")
    formation = player_data.get("team", {}).get("formation", "")
    role_name = role_info.get("role", "Unknown") if role_info else "Unknown"
    role_conf = role_info.get("confidence", 0) if role_info else 0
    role_reason = role_info.get("reasoning", "") if role_info else ""

    phys = player_data.get("physical", {})
    tech = player_data.get("technical", {})
    tact = player_data.get("tactical", {})
    strengths = player_data.get("strengths", "")
    weaknesses = player_data.get("weaknesses", "")
    tactical_notes = player_data.get("tactical_notes", "")

    # Build stat summary
    stat_summary = (
        f"Physical — Speed: {phys.get('speed', '?')}, Acceleration: {phys.get('acceleration', '?')}, "
        f"Stamina: {phys.get('stamina', '?')}, Strength: {phys.get('strength', '?')}\n"
        f"Technical — Passing: {tech.get('passing', '?')}, Dribbling: {tech.get('dribbling', '?')}, "
        f"Shooting: {tech.get('shooting', '?')}, Crossing: {tech.get('crossing', '?')}, "
        f"First Touch: {tech.get('first_touch', '?')}\n"
        f"Tactical — Positioning: {tact.get('positioning', '?')}, Vision: {tact.get('vision', '?')}, "
        f"Work Rate: {tact.get('work_rate', '?')}, Pressing: {tact.get('pressing', '?')}, "
        f"Decision Making: {tact.get('decision_making', '?')}"
    )

    # Try LLM
    system_prompt = (
        "You are a professional football scout. Write a concise scouting report "
        "covering strengths, weaknesses, tactical role, and which systems suit this player. "
        "Be specific and reference the stats provided. Use markdown formatting with headers."
    )
    user_message = (
        f"Player: {name}, Age: {age}, Position: {pos}, Preferred Foot: {foot}\n"
        f"Team: {team}, Formation: {formation}\n"
        f"Classified Role: {role_name} ({role_conf:.0%} confidence)\n"
        f"Role Reasoning: {role_reason}\n\n"
        f"Stats (1-100 scale):\n{stat_summary}\n\n"
        f"Known Strengths: {strengths}\n"
        f"Known Weaknesses: {weaknesses}\n"
        f"Tactical Notes: {tactical_notes}"
    )

    llm_response = call_openrouter(system_prompt, user_message)
    if llm_response:
        return llm_response

    # ── Template fallback ─────────────────────────────────────
    phys_avg = round(np.mean([phys.get("speed", 50), phys.get("acceleration", 50),
                               phys.get("stamina", 50), phys.get("strength", 50)]))
    tech_avg = round(np.mean([tech.get("passing", 50), tech.get("dribbling", 50),
                               tech.get("shooting", 50), tech.get("crossing", 50),
                               tech.get("first_touch", 50)]))
    tact_avg = round(np.mean([tact.get("positioning", 50), tact.get("vision", 50),
                               tact.get("work_rate", 50), tact.get("pressing", 50),
                               tact.get("decision_making", 50)]))
    overall = round(np.mean([phys_avg, tech_avg, tact_avg]))

    # Find top 3 stats
    all_stats = {
        "Speed": phys.get("speed", 50), "Acceleration": phys.get("acceleration", 50),
        "Stamina": phys.get("stamina", 50), "Strength": phys.get("strength", 50),
        "Passing": tech.get("passing", 50), "Dribbling": tech.get("dribbling", 50),
        "Shooting": tech.get("shooting", 50), "Crossing": tech.get("crossing", 50),
        "First Touch": tech.get("first_touch", 50),
        "Positioning": tact.get("positioning", 50), "Vision": tact.get("vision", 50),
        "Work Rate": tact.get("work_rate", 50), "Pressing": tact.get("pressing", 50),
        "Decision Making": tact.get("decision_making", 50),
    }
    top_3 = sorted(all_stats.items(), key=lambda x: x[1], reverse=True)[:3]
    bottom_3 = sorted(all_stats.items(), key=lambda x: x[1])[:3]

    report = f"""## Scouting Report: {name}

**Position:** {pos} | **Age:** {age} | **Foot:** {foot} | **Team:** {team}
**Classified Role:** {role_name} ({role_conf:.0%} confidence)

---

### Overall Assessment
{name} is a **{pos}** classified as a **{role_name}** with an overall rating of **{overall}/100**.
- Physical: {phys_avg}/100
- Technical: {tech_avg}/100
- Tactical: {tact_avg}/100

### Key Strengths
{name}'s standout attributes are **{top_3[0][0]}** ({top_3[0][1]}), **{top_3[1][0]}** ({top_3[1][1]}), and **{top_3[2][0]}** ({top_3[2][1]}).
{('**Scout notes:** ' + strengths) if strengths else ''}

### Areas for Improvement
The weakest areas are **{bottom_3[0][0]}** ({bottom_3[0][1]}), **{bottom_3[1][0]}** ({bottom_3[1][1]}), and **{bottom_3[2][0]}** ({bottom_3[2][1]}).
{('**Scout notes:** ' + weaknesses) if weaknesses else ''}

### Tactical Role
{role_reason}

### System Fit
Best suited for a **{formation}** formation where {name} can operate as a **{role_name}**.
{('**Additional notes:** ' + tactical_notes) if tactical_notes else ''}

---
*Report generated by SpaceAI FC (Template Mode)*
"""
    return report


def _show_results():
    result = st.session_state.get("pa_result")
    if result is None:
        return
    if not result.get("success"):
        st.error("Assessment failed.")
        return

    player = result["player"]
    role = result.get("role")
    radar_b64 = result.get("radar_base64")
    scouting = result.get("scouting_report", "")

    st.markdown("---")

    # ── Player profile card ────────────────────────────────────
    section_title("🪪 Player Profile")
    name = player.get("name", "Unknown")
    number = player.get("number", 0)
    pos = player.get("position", "")
    age = player.get("age", "")
    foot = player.get("foot", "")
    team = player.get("team", {}).get("name", "")
    h = player.get("height", "")
    w = player.get("weight", "")

    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1B5E20,#2E7D32);border-radius:12px;'
        f'padding:20px 28px;color:white;margin-bottom:16px;border-left:5px solid #FFD700;'
        f'box-shadow:0 4px 15px rgba(27,94,32,0.3)">'
        f'<div style="display:flex;align-items:center;gap:24px">'
        f'<div style="background:rgba(255,215,0,0.2);border:2px solid #FFD700;'
        f'border-radius:50%;width:70px;height:70px;display:flex;align-items:center;'
        f'justify-content:center;font-size:1.8rem;font-weight:800;color:#FFD700">#{number}</div>'
        f'<div>'
        f'<div style="font-size:1.6rem;font-weight:800;letter-spacing:0.5px">{name}</div>'
        f'<div style="color:rgba(255,255,255,0.8);font-size:0.95rem;margin-top:4px">'
        f'{pos} · {foot} foot · Age {age} · {h}cm / {w}kg</div>'
        f'<div style="color:rgba(255,255,255,0.6);font-size:0.85rem;margin-top:2px">'
        f'{team}</div>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

    # ── Role classification ────────────────────────────────────
    if role:
        section_title("🎭 Role Classification")
        role_name = role.get("role", "Unknown")
        conf = role.get("confidence", 0)
        reasoning = role.get("reasoning", "")

        st.markdown(
            f'<div class="result-card">'
            f'<div style="display:flex;align-items:center;gap:16px">'
            f'<div style="background:linear-gradient(135deg,#1B5E20,#2E7D32);color:#FFD700;'
            f'padding:10px 20px;border-radius:8px;font-weight:700;font-size:1.1rem">'
            f'{role_name}</div>'
            f'<div style="color:#2E7D32;font-weight:600">{conf:.0%} confidence</div>'
            f'</div>'
            f'<p style="color:#555;margin-top:12px;line-height:1.6">{reasoning}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Radar chart ────────────────────────────────────────────
    if radar_b64:
        section_title("📊 Stat Radar")
        from app.utils.api_client import base64_to_image
        img = base64_to_image(radar_b64)
        st.image(img, caption=f"{name} — Radar Profile", use_container_width=True)

    # ── Scouting report ────────────────────────────────────────
    if scouting:
        section_title("📋 Scouting Report")

        # Mode badge
        if is_llm_available():
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

        st.markdown(
            f'<div class="result-card" style="line-height:1.7">{""}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(scouting)

    # ── Download ───────────────────────────────────────────────
    if scouting:
        st.markdown("---")
        st.download_button(
            "⬇️ Download Scouting Report",
            data=scouting,
            file_name=f"scouting_report_{player.get('name', 'player').replace(' ', '_')}.md",
            mime="text/markdown",
            key="pa_dl_report",
        )
