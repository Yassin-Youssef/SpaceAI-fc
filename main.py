"""
SpaceAI FC - Main Demo
========================
Runs the complete Phase 1 + Phase 2 analysis pipeline.
Demonstrates: pitch model, pass network, space control,
formation detection, player roles, press resistance,
tactical patterns, and full match report.
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


def main():
    print("\n" + "=" * 60)
    print("  SpaceAI FC - Tactical Analysis Engine v2")
    print("  Phase 2 Demo: El Clásico Analysis")
    print("=" * 60)
    
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
    # PHASE 1 STEPS
    # ════════════════════════════════════════════════════════════
    
    # 1. Pitch Model
    print("\n[1/11] Drawing pitch with player positions...")
    
    fp = FootballPitch()
    fig1, ax1, pitch1 = fp.draw(title="SpaceAI FC - El Clásico")
    fp.plot_players(ax1, pitch1, barca, madrid,
                    team_a_name="FC Barcelona", team_b_name="Real Madrid",
                    team_a_color="#a50044", team_b_color="#ffffff")
    fp.plot_ball(ax1, 60, 40)
    fp.save(fig1, "01_pitch.png")
    
    # 2. Pass Network
    print("[2/11] Analyzing pass network...")
    
    pn = PassNetwork()
    pn.add_players(barca)
    pn.add_passes(passes)
    pn.print_summary()
    
    fig2, ax2 = pn.draw(
        title="SpaceAI FC - Barcelona Pass Network",
        team_color="#a50044",
        team_name="FC Barcelona",
        min_passes=2
    )
    fig2.savefig("outputs/02_pass_network.png", dpi=150, bbox_inches='tight',
                 facecolor=fig2.get_facecolor())
    print("Saved: outputs/02_pass_network.png")
    
    # 3. Pass Sequence
    print("[3/11] Drawing pass sequence...")
    
    sequence = [2, 4, 8, 6, 19, 9]
    fig3, ax3 = pn.draw_sequence(
        sequence,
        title="SpaceAI FC - Build-Up Sequence",
        team_color="#a50044",
        team_name="FC Barcelona"
    )
    fig3.savefig("outputs/03_pass_sequence.png", dpi=150, bbox_inches='tight',
                 facecolor=fig3.get_facecolor())
    print("Saved: outputs/03_pass_sequence.png")
    
    # 4. Space Control (Voronoi)
    print("\n[4/11] Computing space control (Voronoi)...")
    
    sc = SpaceControl()
    sc.set_teams(barca, madrid)
    sc.set_ball(60, 40)
    
    fig4, ax4, stats4 = sc.draw_voronoi(
        title="SpaceAI FC - Space Control (Voronoi)",
        team_a_name="FC Barcelona", team_b_name="Real Madrid",
        team_a_color="#a50044", team_b_color="#ffffff"
    )
    sc.print_analysis(stats4, "FC Barcelona", "Real Madrid")
    fig4.savefig("outputs/04_space_voronoi.png", dpi=150, bbox_inches='tight',
                 facecolor=fig4.get_facecolor())
    print("Saved: outputs/04_space_voronoi.png")
    
    # 5. Space Control (Influence)
    print("[5/11] Computing space control (Influence)...")
    
    fig5, ax5, stats5 = sc.draw_influence(
        title="SpaceAI FC - Space Control (Influence)",
        team_a_name="FC Barcelona", team_b_name="Real Madrid",
        team_a_color="#a50044", team_b_color="#ffffff"
    )
    fig5.savefig("outputs/05_space_influence.png", dpi=150, bbox_inches='tight',
                 facecolor=fig5.get_facecolor())
    print("Saved: outputs/05_space_influence.png")
    
    # ════════════════════════════════════════════════════════════
    # PHASE 2 STEPS
    # ════════════════════════════════════════════════════════════
    
    # 6. Formation Detection
    print("\n[6/11] Detecting formations...")
    
    fd_barca = FormationDetector()
    fd_barca.set_team(barca, "FC Barcelona", "#a50044")
    result_barca = fd_barca.detect()
    fd_barca.print_analysis(result_barca)
    
    fig6, ax6 = fd_barca.draw(result_barca,
                               title="SpaceAI FC - Barcelona Formation Detection")
    fd_barca.save(fig6, "06_formation_barca.png")
    
    fd_madrid = FormationDetector()
    fd_madrid.set_team(madrid, "Real Madrid", "#ffffff")
    result_madrid = fd_madrid.detect()
    fd_madrid.print_analysis(result_madrid)
    
    fig6b, ax6b = fd_madrid.draw(result_madrid,
                                  title="SpaceAI FC - Real Madrid Formation Detection")
    fd_madrid.save(fig6b, "06_formation_madrid.png")
    
    # 7. Player Role Classification
    print("\n[7/11] Classifying player roles...")
    
    rc_barca = RoleClassifier()
    rc_barca.set_team(barca, "FC Barcelona", "#a50044")
    roles_barca = rc_barca.classify_all()
    rc_barca.print_analysis(roles_barca)
    
    fig7, ax7 = rc_barca.draw(roles_barca,
                               title="SpaceAI FC - Barcelona Player Roles")
    rc_barca.save(fig7, "07_roles_barca.png")
    
    rc_madrid = RoleClassifier()
    rc_madrid.set_team(madrid, "Real Madrid", "#ffffff")
    roles_madrid = rc_madrid.classify_all()
    rc_madrid.print_analysis(roles_madrid)
    
    fig7b, ax7b = rc_madrid.draw(roles_madrid,
                                  title="SpaceAI FC - Real Madrid Player Roles")
    rc_madrid.save(fig7b, "07_roles_madrid.png")
    
    # 8. Press Resistance
    print("\n[8/11] Analyzing press resistance...")
    
    # Generate synthetic pass events for demo
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
        
        if nearby >= 2:
            success = random.random() < 0.55
        elif nearby >= 1:
            success = random.random() < 0.75
        else:
            success = random.random() < 0.90
        
        pass_events.append({
            'passer': passer['number'], 'receiver': receiver['number'],
            'success': success, 'x': px, 'y': py,
            'end_x': end_x, 'end_y': end_y,
        })
    
    pr = PressResistance(pressure_radius=10.0, pressure_threshold=2)
    pr.set_teams(barca, madrid,
                 team_name="FC Barcelona", team_color="#a50044",
                 opponent_name="Real Madrid")
    pr.add_pass_events(pass_events)
    
    pr_result = pr.analyze()
    pr.print_analysis(pr_result)
    
    fig8, ax8 = pr.draw(pr_result,
                         title="SpaceAI FC - Barcelona Press Resistance")
    pr.save(fig8, "08_press_resistance.png")
    
    # 9. Tactical Pattern Detection
    print("\n[9/11] Detecting tactical patterns...")
    
    ptd = PatternDetector()
    ptd.set_teams(barca, madrid,
                  team_a_name="FC Barcelona", team_b_name="Real Madrid",
                  team_a_color="#a50044", team_b_color="#ffffff")
    
    ptd.print_analysis(team="a")
    fig9, ax9 = ptd.draw(team="a",
                          title="SpaceAI FC - Barcelona Tactical Patterns")
    ptd.save(fig9, "09_patterns_barca.png")
    
    ptd.print_analysis(team="b")
    fig9b, ax9b = ptd.draw(team="b",
                            title="SpaceAI FC - Real Madrid Tactical Patterns")
    ptd.save(fig9b, "09_patterns_madrid.png")
    
    # 10. Full Match Report Dashboard
    print("\n[10/11] Generating match report dashboard...")
    
    mr = MatchReport()
    mr.set_match_info(
        home_team="FC Barcelona",
        away_team="Real Madrid",
        score_home=2, score_away=1,
        minute=72, competition="La Liga",
        date="2026-03-22"
    )
    mr.set_team_a("FC Barcelona", "#a50044", barca)
    mr.set_team_b("Real Madrid", "#ffffff", madrid)
    mr.set_ball(60, 40)
    mr.set_pass_network(pn)
    mr.set_space_control(sc)
    
    # Phase 2 integrations
    mr.set_formation_detector(fd_barca, fd_madrid)
    mr.set_role_classifier(rc_barca, rc_madrid)
    mr.set_press_resistance(pr)
    mr.set_pattern_detector(ptd)
    
    mr.print_report()
    
    fig10 = mr.draw_dashboard()
    mr.save_dashboard(fig10, "10_match_dashboard.png")
    
    # 11. Export Word Document
    print("\n[11/11] Exporting match report document...")
    mr.export_document("el_clasico_report.docx")
    
    # Done
    print("\n" + "=" * 60)
    print("  All outputs saved to outputs/ folder")
    print("  SpaceAI FC Engine v2 - Phase 2 Complete!")
    print("=" * 60 + "\n")
    
    plt.close('all')


if __name__ == "__main__":
    main()
