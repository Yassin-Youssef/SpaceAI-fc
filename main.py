"""
SpaceAI FC - Main Demo
========================
Runs the complete Phase 1 analysis pipeline.
Demonstrates: pitch model, pass network, space control, and match report.
"""

import sys
import matplotlib.pyplot as plt

from engine.visualization.pitch import FootballPitch
from engine.analysis.pass_network import PassNetwork
from engine.analysis.space_control import SpaceControl
from engine.analysis.match_report import MatchReport


def main():
    print("\n" + "=" * 60)
    print("  SpaceAI FC - Tactical Analysis Engine v1")
    print("  Phase 1 Demo: El Clásico Analysis")
    print("=" * 60)
    
    # Define teams
    
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
    
    # 1. Pitch Model
    print("\n[1/5] Drawing pitch with player positions...")
    
    fp = FootballPitch()
    fig1, ax1, pitch1 = fp.draw(title="SpaceAI FC - El Clásico")
    fp.plot_players(ax1, pitch1, barca, madrid,
                    team_a_name="FC Barcelona", team_b_name="Real Madrid",
                    team_a_color="#a50044", team_b_color="#ffffff")
    fp.plot_ball(ax1, 60, 40)
    fp.save(fig1, "01_pitch.png")
    
    # 2. Pass Network
    print("[2/5] Analyzing pass network...")
    
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
    
    # Pass sequence
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
    
    # 3. Space Control
    print("\n[3/5] Computing space control...")
    
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
    
    fig5, ax5, stats5 = sc.draw_influence(
        title="SpaceAI FC - Space Control (Influence)",
        team_a_name="FC Barcelona", team_b_name="Real Madrid",
        team_a_color="#a50044", team_b_color="#ffffff"
    )
    fig5.savefig("outputs/05_space_influence.png", dpi=150, bbox_inches='tight',
                 facecolor=fig5.get_facecolor())
    print("Saved: outputs/05_space_influence.png")
    
    # 4. Full Match Report
    print("\n[4/5] Generating match report...")
    
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
    
    mr.print_report()
    
    fig6 = mr.draw_dashboard()
    mr.save_dashboard(fig6, "06_match_dashboard.png")
    
    # 5. Export Word Document
    print("\n[5/5] Exporting match report document...")
    mr.export_document("el_clasico_report.docx")
    
    # Done
    print("\n" + "=" * 60)
    print("  All outputs saved to outputs/ folder")
    print("  SpaceAI FC Engine v1 - Phase 1 Complete!")
    print("=" * 60 + "\n")
    
    plt.show()


if __name__ == "__main__":
    main()
