"""
SpaceAI FC - Main Demo
========================
Runs the complete Phase 1 + Phase 2 + Phase 3 + Phase 4 analysis pipeline.
Demonstrates the full Sense → Understand → Reason → Act → Explain pipeline.

Phase 4 modules are optional — they skip gracefully if dependencies
are not installed.
"""

import sys
import os
import random
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from engine.visualization.pitch import FootballPitch
from engine.analysis.pass_network import PassNetwork
from engine.analysis.space_control import SpaceControl
from engine.analysis.formation_detection import FormationDetector
from engine.analysis.role_classifier import RoleClassifier
from engine.analysis.press_resistance import PressResistance
from engine.analysis.pattern_detection import PatternDetector
from engine.analysis.match_report import MatchReport
from engine.intelligence.knowledge_graph import TacticalKnowledgeGraph
from engine.intelligence.tactical_reasoning import TacticalReasoner
from engine.intelligence.strategy_recommender import StrategyRecommender
from engine.intelligence.explanation_layer import ExplanationLayer

# Phase 4 — optional imports
HAS_VIDEO = False
HAS_RL = False
HAS_SIM = True  # simulation only needs matplotlib

try:
    from engine.perception.video_analyzer import VideoAnalyzer
    HAS_VIDEO = True
except ImportError:
    pass

try:
    from engine.intelligence.rl_coach import RLCoach, HAS_GYM, HAS_SB3
    if HAS_GYM and HAS_SB3:
        HAS_RL = True
except ImportError:
    pass

try:
    from engine.intelligence.simulation import TacticalSimulation
except ImportError:
    HAS_SIM = False


# ════════════════════════════════════════════════════════════════
# Helper — Phase banner and summary
# ════════════════════════════════════════════════════════════════

def _phase_banner(label):
    """Print a wide phase separator."""
    line = f"━━ {label} "
    line += "━" * max(0, 58 - len(line))
    print(f"\n{line}")


def _phase_done(phase_num, name, saved_count):
    """Print a phase completion line."""
    print(f"  ✓ Phase {phase_num} complete — {name} ({saved_count} outputs saved)")


def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  SpaceAI FC — Tactical Intelligence Engine v4           ║")
    print("║  Sense → Understand → Reason → Act → Explain            ║")
    print("╚══════════════════════════════════════════════════════════╝")

    os.makedirs("outputs", exist_ok=True)

    # ── Define teams ────────────────────────────────────────────

    barca = [
        {'name': 'ter Stegen',  'number': 1,  'x': 5,  'y': 40, 'position': 'GK'},
        {'name': 'Koundé',      'number': 23, 'x': 30, 'y': 70, 'position': 'RB'},
        {'name': 'Araújo',      'number': 4,  'x': 25, 'y': 52, 'position': 'CB'},
        {'name': 'Cubarsí',     'number': 2,  'x': 25, 'y': 28, 'position': 'CB'},
        {'name': 'Baldé',       'number': 3,  'x': 30, 'y': 10, 'position': 'LB'},
        {'name': 'Pedri',       'number': 8,  'x': 45, 'y': 48, 'position': 'CM'},
        {'name': 'De Jong',     'number': 21, 'x': 45, 'y': 32, 'position': 'CM'},
        {'name': 'Lamine',      'number': 19, 'x': 65, 'y': 68, 'position': 'RW'},
        {'name': 'Gavi',        'number': 6,  'x': 60, 'y': 40, 'position': 'CAM'},
        {'name': 'Raphinha',    'number': 11, 'x': 65, 'y': 12, 'position': 'LW'},
        {'name': 'Lewandowski', 'number': 9,  'x': 80, 'y': 40, 'position': 'ST'},
    ]

    madrid = [
        {'name': 'Courtois',    'number': 1,  'x': 115, 'y': 40, 'position': 'GK'},
        {'name': 'Carvajal',    'number': 2,  'x': 90,  'y': 70, 'position': 'RB'},
        {'name': 'Rüdiger',     'number': 22, 'x': 93,  'y': 52, 'position': 'CB'},
        {'name': 'Militão',     'number': 3,  'x': 93,  'y': 28, 'position': 'CB'},
        {'name': 'Mendy',       'number': 23, 'x': 90,  'y': 10, 'position': 'LB'},
        {'name': 'Tchouaméni',  'number': 14, 'x': 73,  'y': 40, 'position': 'CDM'},
        {'name': 'Valverde',    'number': 15, 'x': 70,  'y': 58, 'position': 'CM'},
        {'name': 'Bellingham',  'number': 5,  'x': 70,  'y': 22, 'position': 'CM'},
        {'name': 'Rodrygo',     'number': 11, 'x': 55,  'y': 65, 'position': 'RW'},
        {'name': 'Mbappé',      'number': 7,  'x': 50,  'y': 40, 'position': 'ST'},
        {'name': 'Vinícius',    'number': 20, 'x': 55,  'y': 15, 'position': 'LW'},
    ]

    passes = [
        (1, 4), (1, 2), (1, 4),
        (4, 8), (4, 21), (4, 8), (4, 23), (4, 2),
        (2, 21), (2, 3), (2, 8), (2, 21), (2, 4),
        (23, 19), (23, 8), (23, 19), (23, 4),
        (3, 11), (3, 21), (3, 11), (3, 2),
        (8, 6), (8, 19), (8, 23), (8, 21), (8, 9),
        (8, 6), (8, 19), (8, 4), (8, 9), (8, 11),
        (8, 6), (8, 21), (8, 23),
        (21, 8), (21, 2), (21, 3), (21, 6), (21, 11),
        (21, 8), (21, 4), (21, 6),
        (6, 9), (6, 19), (6, 8), (6, 11), (6, 9),
        (6, 8), (6, 19), (6, 21),
        (19, 9), (19, 23), (19, 6), (19, 8),
        (19, 9), (19, 6),
        (11, 9), (11, 3), (11, 6), (11, 21),
        (11, 9), (11, 6),
        (9, 6), (9, 19), (9, 8), (9, 11),
        (6, 8), (19, 8), (9, 6), (11, 21),
    ]

    # ════════════════════════════════════════════════════════════
    # PHASE 1 — FOUNDATION (Sense)
    # ════════════════════════════════════════════════════════════
    _phase_banner("PHASE 1 — FOUNDATION (Sense)")
    p1_count = 0

    # 1.1 Pitch Model
    print("  [1.1] Drawing pitch with player positions...")
    fp = FootballPitch()
    fig1, ax1, pitch1 = fp.draw(title="SpaceAI FC - El Clásico")
    fp.plot_players(ax1, pitch1, barca, madrid,
                    team_a_name="FC Barcelona", team_b_name="Real Madrid",
                    team_a_color="#a50044", team_b_color="#ffffff")
    fp.plot_ball(ax1, 60, 40)
    fp.save(fig1, "01_pitch.png")
    p1_count += 1

    # 1.2 Pass Network
    print("  [1.2] Analyzing pass network...")
    pn = PassNetwork()
    pn.add_players(barca)
    pn.add_passes(passes)
    pn.print_summary()
    fig2, ax2 = pn.draw(title="SpaceAI FC - Barcelona Pass Network",
                         team_color="#a50044", team_name="FC Barcelona", min_passes=2)
    fig2.savefig("outputs/02_pass_network.png", dpi=150, bbox_inches='tight',
                 facecolor=fig2.get_facecolor())
    print("  Saved: outputs/02_pass_network.png")
    p1_count += 1

    # 1.3 Pass Sequence
    print("  [1.3] Drawing pass sequence...")
    sequence = [2, 4, 8, 6, 19, 9]
    fig3, ax3 = pn.draw_sequence(sequence, title="SpaceAI FC - Build-Up Sequence",
                                  team_color="#a50044", team_name="FC Barcelona")
    fig3.savefig("outputs/03_pass_sequence.png", dpi=150, bbox_inches='tight',
                 facecolor=fig3.get_facecolor())
    print("  Saved: outputs/03_pass_sequence.png")
    p1_count += 1

    # 1.4 Space Control (Voronoi)
    print("  [1.4] Computing space control (Voronoi)...")
    sc = SpaceControl()
    sc.set_teams(barca, madrid)
    sc.set_ball(60, 40)
    fig4, ax4, stats4 = sc.draw_voronoi(title="SpaceAI FC - Space Control (Voronoi)",
                                         team_a_name="FC Barcelona", team_b_name="Real Madrid",
                                         team_a_color="#a50044", team_b_color="#ffffff")
    sc.print_analysis(stats4, "FC Barcelona", "Real Madrid")
    fig4.savefig("outputs/04_space_voronoi.png", dpi=150, bbox_inches='tight',
                 facecolor=fig4.get_facecolor())
    print("  Saved: outputs/04_space_voronoi.png")
    p1_count += 1

    # 1.5 Space Control (Influence)
    print("  [1.5] Computing space control (Influence)...")
    fig5, ax5, stats5 = sc.draw_influence(title="SpaceAI FC - Space Control (Influence)",
                                           team_a_name="FC Barcelona", team_b_name="Real Madrid",
                                           team_a_color="#a50044", team_b_color="#ffffff")
    fig5.savefig("outputs/05_space_influence.png", dpi=150, bbox_inches='tight',
                 facecolor=fig5.get_facecolor())
    print("  Saved: outputs/05_space_influence.png")
    p1_count += 1

    _phase_done(1, "Foundation", p1_count)

    # ════════════════════════════════════════════════════════════
    # PHASE 2 — DETECTION (Understand)
    # ════════════════════════════════════════════════════════════
    _phase_banner("PHASE 2 — DETECTION (Understand)")
    p2_count = 0

    # 2.1 Formation Detection
    print("  [2.1] Detecting formations...")
    fd_barca = FormationDetector()
    fd_barca.set_team(barca, "FC Barcelona", "#a50044")
    result_barca = fd_barca.detect()
    fd_barca.print_analysis(result_barca)
    fig6, _ = fd_barca.draw(result_barca, title="SpaceAI FC - Barcelona Formation Detection")
    fd_barca.save(fig6, "06_formation_barca.png")
    p2_count += 1

    fd_madrid = FormationDetector()
    fd_madrid.set_team(madrid, "Real Madrid", "#ffffff")
    result_madrid = fd_madrid.detect()
    fd_madrid.print_analysis(result_madrid)
    fig6b, _ = fd_madrid.draw(result_madrid, title="SpaceAI FC - Real Madrid Formation Detection")
    fd_madrid.save(fig6b, "06_formation_madrid.png")
    p2_count += 1

    # 2.2 Player Role Classification
    print("  [2.2] Classifying player roles...")
    rc_barca = RoleClassifier()
    rc_barca.set_team(barca, "FC Barcelona", "#a50044")
    roles_barca = rc_barca.classify_all()
    rc_barca.print_analysis(roles_barca)
    fig7, _ = rc_barca.draw(roles_barca, title="SpaceAI FC - Barcelona Player Roles")
    rc_barca.save(fig7, "07_roles_barca.png")
    p2_count += 1

    rc_madrid = RoleClassifier()
    rc_madrid.set_team(madrid, "Real Madrid", "#ffffff")
    roles_madrid = rc_madrid.classify_all()
    rc_madrid.print_analysis(roles_madrid)
    fig7b, _ = rc_madrid.draw(roles_madrid, title="SpaceAI FC - Real Madrid Player Roles")
    rc_madrid.save(fig7b, "07_roles_madrid.png")
    p2_count += 1

    # 2.3 Press Resistance
    print("  [2.3] Analyzing press resistance...")
    random.seed(42)
    pass_events = []
    barca_outfield = [p for p in barca if p['position'] != 'GK']
    for _ in range(65):
        passer = random.choice(barca_outfield)
        receiver = random.choice(barca_outfield)
        px = max(0, min(120, passer['x'] + random.gauss(0, 3)))
        py = max(0, min(80, passer['y'] + random.gauss(0, 3)))
        end_x = receiver['x'] + random.gauss(0, 3)
        end_y = receiver['y'] + random.gauss(0, 3)
        opp_pos = np.array([[p['x'], p['y']] for p in madrid])
        dist = np.linalg.norm(opp_pos - np.array([px, py]), axis=1)
        nearby = np.sum(dist < 10)
        success = random.random() < (0.55 if nearby >= 2 else (0.75 if nearby >= 1 else 0.90))
        pass_events.append({'passer': passer['number'], 'receiver': receiver['number'],
                            'success': success, 'x': px, 'y': py, 'end_x': end_x, 'end_y': end_y})

    pr = PressResistance(pressure_radius=10.0, pressure_threshold=2)
    pr.set_teams(barca, madrid, team_name="FC Barcelona", team_color="#a50044", opponent_name="Real Madrid")
    pr.add_pass_events(pass_events)
    pr_result = pr.analyze()
    pr.print_analysis(pr_result)
    fig8, _ = pr.draw(pr_result, title="SpaceAI FC - Barcelona Press Resistance")
    pr.save(fig8, "08_press_resistance.png")
    p2_count += 1

    # 2.4 Tactical Pattern Detection
    print("  [2.4] Detecting tactical patterns...")
    ptd = PatternDetector()
    ptd.set_teams(barca, madrid, team_a_name="FC Barcelona", team_b_name="Real Madrid",
                  team_a_color="#a50044", team_b_color="#ffffff")
    ptd.print_analysis(team="a")
    fig9, _ = ptd.draw(team="a", title="SpaceAI FC - Barcelona Tactical Patterns")
    ptd.save(fig9, "09_patterns_barca.png")
    p2_count += 1
    ptd.print_analysis(team="b")
    fig9b, _ = ptd.draw(team="b", title="SpaceAI FC - Real Madrid Tactical Patterns")
    ptd.save(fig9b, "09_patterns_madrid.png")
    p2_count += 1

    _phase_done(2, "Detection", p2_count)

    # ════════════════════════════════════════════════════════════
    # PHASE 3 — INTELLIGENCE (Reason → Act → Explain)
    # ════════════════════════════════════════════════════════════
    _phase_banner("PHASE 3 — INTELLIGENCE (Reason → Act → Explain)")
    p3_count = 0

    # Build analysis data dict for reasoning
    grid, stats = sc.compute_influence_control()
    midfield = sc.get_midfield_control(grid)

    analysis_data = {
        'formation_a': result_barca,
        'formation_b': result_madrid,
        'space_control': {
            'team_a_control': stats['team_a_control'],
            'team_b_control': stats['team_b_control'],
            'zones': stats['zones'],
            'midfield': midfield,
        },
        'pass_summary': pn.get_summary(),
        'press_resistance': pr_result,
        'patterns_a': ptd.detect_all(team="a"),
        'patterns_b': ptd.detect_all(team="b"),
        'roles_a': roles_barca,
        'roles_b': roles_madrid,
    }

    # 3.1 Knowledge Graph
    print("  [3.1] Building knowledge graph...")
    kg = TacticalKnowledgeGraph()
    kg.print_knowledge_base()
    fig10, _ = kg.draw(title="SpaceAI FC - Tactical Knowledge Graph")
    kg.save(fig10, "10_knowledge_graph.png")
    p3_count += 1

    # 3.2 Tactical Reasoning (SWOT)
    print("  [3.2] Running tactical reasoning...")
    reasoner = TacticalReasoner(knowledge_graph=kg)
    reasoner.set_analysis(analysis_data, "FC Barcelona", "Real Madrid")
    swot = reasoner.reason()
    reasoner.print_analysis(swot)
    fig11, _ = reasoner.draw(swot, title="SpaceAI FC - Tactical SWOT Analysis")
    reasoner.save(fig11, "11_swot_analysis.png")
    p3_count += 1

    # 3.3 Strategy Recommendations
    print("  [3.3] Generating strategy recommendations...")
    sr = StrategyRecommender(knowledge_graph=kg)
    sr.set_reasoning(swot, analysis_data, "FC Barcelona", "Real Madrid")
    recs = sr.recommend()
    sr.print_recommendations(recs)
    fig12, _ = sr.draw(recs, title="SpaceAI FC - Strategy Recommendations")
    sr.save(fig12, "12_recommendations.png")
    p3_count += 1

    # 3.4 Explanation Generation
    print("  [3.4] Generating tactical explanation...")

    mr_temp = MatchReport()
    mr_temp.set_match_info("FC Barcelona", "Real Madrid", 2, 1, 72, "La Liga", "2026-03-22")
    mr_temp.set_team_a("FC Barcelona", "#a50044", barca)
    mr_temp.set_team_b("Real Madrid", "#ffffff", madrid)
    mr_temp.set_ball(60, 40)
    mr_temp.set_pass_network(pn)
    mr_temp.set_space_control(sc)
    mr_temp.set_formation_detector(fd_barca, fd_madrid)
    mr_temp.set_role_classifier(rc_barca, rc_madrid)
    mr_temp.set_press_resistance(pr)
    mr_temp.set_pattern_detector(ptd)
    report_data = mr_temp.generate_report()

    el = ExplanationLayer(mode="template")
    el.set_data(
        match_info={'home_team': 'FC Barcelona', 'away_team': 'Real Madrid',
                    'score_home': 2, 'score_away': 1, 'minute': 72,
                    'competition': 'La Liga'},
        report_data=report_data,
        swot_results=swot,
        recommendations=recs,
        team_name="FC Barcelona",
        opponent_name="Real Madrid",
    )
    explanation_text = el.generate()
    el.print_explanation(explanation_text)
    el.save_text(explanation_text, "13_tactical_explanation.txt")
    p3_count += 1

    _phase_done(3, "Intelligence", p3_count)

    # ════════════════════════════════════════════════════════════
    # PHASE 4 — ADVANCED AI (Perceive + Learn + Simulate)
    # ════════════════════════════════════════════════════════════
    _phase_banner("PHASE 4 — ADVANCED AI (Perceive + Learn + Simulate)")
    p4_count = 0

    video_summary = None
    rl_summary = None
    sim_summary = None

    # 4.1 Video Analysis (optional)
    print("  [4.1] Video tactical analysis...")
    if HAS_VIDEO:
        try:
            va = VideoAnalyzer()
            va.team_a_name = "FC Barcelona"
            va.team_b_name = "Real Madrid"
            va.team_a_color = "#a50044"
            va.team_b_color = "#ffffff"
            data = va.run_synthetic_demo(n_frames=100)
            va.print_summary()

            fig_v, _ = va.draw_frame(frame_idx=50)
            fig_v.savefig("outputs/16_video_frame.png", dpi=150, bbox_inches='tight',
                          facecolor=fig_v.get_facecolor())
            plt.close(fig_v)
            p4_count += 1

            player_data = va.track_individual(player_id=10, team='A')
            if 'error' not in player_data:
                fig_t = va.draw_player_tracking(player_data)
                fig_t.savefig("outputs/16_player_tracking.png", dpi=150,
                              bbox_inches='tight', facecolor=fig_t.get_facecolor())
                plt.close(fig_t)
                p4_count += 1

            video_summary = va.get_summary_data()
            print("  ✓ Video analysis complete")
        except Exception as e:
            print(f"  ⚠ Video analysis error: {e}")
    else:
        print("    Skipping — dependencies not available.")
        print("    Run: pip install ultralytics opencv-python yt-dlp")

    # 4.2 RL Coach (optional)
    print("  [4.2] RL tactical coach...")
    if HAS_RL:
        try:
            coach = RLCoach()
            coach.train(timesteps=50_000, seed=42)
            coach.draw_training_curve()
            p4_count += 1

            eval_results = coach.evaluate(n_episodes=20)
            coach.print_evaluation(eval_results)
            coach.draw_decision_distribution(eval_results)
            p4_count += 1

            rl_summary = coach.get_summary_data()
            print("  ✓ RL Coach complete")
        except Exception as e:
            print(f"  ⚠ RL Coach error: {e}")
    else:
        print("    Skipping — dependencies not available.")
        print("    Run: pip install gymnasium stable-baselines3")

    # 4.3 Multi-Agent Simulation
    print("  [4.3] Multi-agent simulation...")
    if HAS_SIM:
        try:
            sim = TacticalSimulation(team_size=5, seed=42)
            sim.set_tactics('high_press', 'low_block')
            sim_stats = sim.run(n_steps=300)
            sim.print_summary(sim_stats)

            fig_sf, _ = sim.draw_frame(step=150)
            fig_sf.savefig("outputs/18_simulation_frame.png", dpi=150,
                           bbox_inches='tight', facecolor=fig_sf.get_facecolor())
            plt.close(fig_sf)
            p4_count += 1

            comparison = sim.compare_tactics('high_press', 'low_block', n_runs=5, n_steps=300)
            sim.draw_comparison(comparison)
            p4_count += 1

            sim_summary = sim.get_summary_data()
            print("  ✓ Simulation complete")
        except Exception as e:
            print(f"  ⚠ Simulation error: {e}")
    else:
        print("    Skipping — import error.")

    _phase_done(4, "Advanced AI", p4_count)

    # ════════════════════════════════════════════════════════════
    # FINAL REPORT
    # ════════════════════════════════════════════════════════════
    _phase_banner("FINAL REPORT")

    # F.1 Full Match Report Dashboard
    print("  [F.1] Generating match report dashboard...")
    mr = MatchReport()
    mr.set_match_info("FC Barcelona", "Real Madrid", 2, 1, 72, "La Liga", "2026-03-22")
    mr.set_team_a("FC Barcelona", "#a50044", barca)
    mr.set_team_b("Real Madrid", "#ffffff", madrid)
    mr.set_ball(60, 40)
    mr.set_pass_network(pn)
    mr.set_space_control(sc)
    mr.set_formation_detector(fd_barca, fd_madrid)
    mr.set_role_classifier(rc_barca, rc_madrid)
    mr.set_press_resistance(pr)
    mr.set_pattern_detector(ptd)
    mr.set_reasoning_results(swot)
    mr.set_recommendations(recs)
    mr.set_explanation(explanation_text)

    # Phase 4 data
    if video_summary:
        mr.set_video_analysis(video_summary)
    if rl_summary:
        mr.set_rl_recommendations(rl_summary)
    if sim_summary:
        mr.set_simulation_results(sim_summary)

    mr.print_report()
    fig14 = mr.draw_dashboard()
    mr.save_dashboard(fig14, "14_match_dashboard.png")

    # F.2 Export Word Document
    print("  [F.2] Exporting match report document...")
    mr.export_document("el_clasico_report.docx")

    # ════════════════════════════════════════════════════════════
    # DONE
    # ════════════════════════════════════════════════════════════
    total = p1_count + p2_count + p3_count + p4_count + 2  # +2 for dashboard + docx
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print(f"║  All Phases Complete! {total} outputs saved to outputs/      ║")
    print("║  SpaceAI FC Engine v4 — Sense → Understand → Reason      ║")
    print("║  → Act → Explain → Perceive → Learn → Simulate           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    plt.close('all')


if __name__ == "__main__":
    main()
