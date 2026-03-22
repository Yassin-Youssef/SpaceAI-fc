"""
SpaceAI FC - Match Summary Generator
======================================
Combines all analysis modules into one structured match report.
This is the central piece that ties the engine together.
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
from mplsoccer import Pitch
import numpy as np
from datetime import datetime


class MatchReport:
    """
    Generates a complete match analysis report by combining:
        - Player positions and formations
        - Pass network analysis
        - Space control analysis
    
    Outputs:
        - Structured text report
        - Visual dashboard combining all analyses
        - Word document report
    """
    
    def __init__(self):
        self.team_a = {'name': 'Team A', 'color': '#e74c3c', 'players': []}
        self.team_b = {'name': 'Team B', 'color': '#3498db', 'players': []}
        self.ball_pos = None
        self.pass_network = None
        self.space_control = None
        self.match_info = {}
    
    # Setup    
    def set_match_info(self, home_team, away_team, score_home=0, score_away=0,
                       minute=0, competition="Friendly", date=None):
        """Set general match information."""
        self.match_info = {
            'home_team': home_team,
            'away_team': away_team,
            'score_home': score_home,
            'score_away': score_away,
            'minute': minute,
            'competition': competition,
            'date': date or datetime.now().strftime("%Y-%m-%d"),
        }
    
    def set_team_a(self, name, color, players):
        """Set team A data."""
        self.team_a = {'name': name, 'color': color, 'players': players}
    
    def set_team_b(self, name, color, players):
        """Set team B data."""
        self.team_b = {'name': name, 'color': color, 'players': players}
    
    def set_ball(self, x, y):
        """Set ball position."""
        self.ball_pos = (x, y)
    
    def set_pass_network(self, pass_network):
        """Attach a computed PassNetwork object."""
        self.pass_network = pass_network
    
    def set_space_control(self, space_control):
        """Attach a computed SpaceControl object."""
        self.space_control = space_control
    
    # Analysis: detect formation from positions
    
    def _detect_formation_simple(self, players):
        """
        Simple formation detection by grouping players into lines
        based on x-coordinate clustering.
        
        Detects which side the team is on and reads defense-to-attack.
        This is a basic version — Phase 2 will have proper detection.
        """
        outfield = [p for p in players if p.get('position') != 'GK']
        
        if not outfield:
            return "Unknown"
        
        sorted_players = sorted(outfield, key=lambda p: p['x'])
        x_positions = [p['x'] for p in sorted_players]
        
        avg_x = sum(x_positions) / len(x_positions)
        
        gaps = []
        for i in range(1, len(x_positions)):
            gaps.append((x_positions[i] - x_positions[i-1], i))
        
        gaps.sort(reverse=True)
        
        for num_splits in [3, 2]:
            if len(gaps) >= num_splits:
                split_positions = sorted([idx for _, idx in gaps[:num_splits]])
                
                lines = []
                prev = 0
                for sp in split_positions:
                    lines.append(sp - prev)
                    prev = sp
                lines.append(len(x_positions) - prev)
                
                if all(1 <= l <= 5 for l in lines) and sum(lines) == 10:
                    if avg_x > 60:
                        lines.reverse()
                    return "-".join(str(l) for l in lines)
        
        if len(gaps) >= 2:
            split_positions = sorted([idx for _, idx in gaps[:2]])
            lines = []
            prev = 0
            for sp in split_positions:
                lines.append(sp - prev)
                prev = sp
            lines.append(len(x_positions) - prev)
            if avg_x > 60:
                lines.reverse()
            return "-".join(str(l) for l in lines)
        
        return "Unknown"
    
    # Generate full report data
    
    def generate_report(self):
        """
        Generate a complete structured report combining all analyses.
        
        Returns a dict with all findings.
        """
        report = {
            'match_info': self.match_info,
            'team_a': {
                'name': self.team_a['name'],
                'formation': self._detect_formation_simple(self.team_a['players']),
                'player_count': len(self.team_a['players']),
            },
            'team_b': {
                'name': self.team_b['name'],
                'formation': self._detect_formation_simple(self.team_b['players']),
                'player_count': len(self.team_b['players']),
            },
            'pass_analysis': None,
            'space_analysis': None,
            'insights': [],
            'recommendations': [],
        }
        
        # Pass network analysis
        if self.pass_network:
            summary = self.pass_network.get_summary()
            report['pass_analysis'] = summary
            
            kp = summary['key_distributor']
            report['insights'].append(
                f"{kp['name']} (#{kp['number']}) is the key distributor "
                f"with betweenness centrality of {kp['betweenness']}"
            )
            
            mi = summary['most_involved']
            report['insights'].append(
                f"{mi['name']} (#{mi['number']}) is the most involved player "
                f"with {mi['passes_made']} passes made and {mi['passes_received']} received"
            )
            
            if summary['top_connections']:
                top = summary['top_connections'][0]
                report['insights'].append(
                    f"Strongest connection: {top['from']} -> {top['to']} "
                    f"({top['passes']} passes)"
                )
            
            if summary['weak_links']:
                for wl in summary['weak_links']:
                    report['insights'].append(
                        f"Weak link: {wl['name']} (#{wl['number']}) with only "
                        f"{wl['total_involvement']} total pass involvements"
                    )
                    report['recommendations'].append(
                        f"Increase involvement of {wl['name']} in build-up play"
                    )
        
        # Space control analysis
        if self.space_control:
            control_grid, stats = self.space_control.compute_influence_control()
            midfield = self.space_control.get_midfield_control(control_grid)
            
            report['space_analysis'] = {
                'overall': stats,
                'midfield': midfield,
            }
            
            ta = self.team_a['name']
            tb = self.team_b['name']
            
            if stats['team_a_control'] > 55:
                report['insights'].append(f"{ta} is dominating territorial control ({stats['team_a_control']}%)")
            elif stats['team_b_control'] > 55:
                report['insights'].append(f"{tb} is dominating territorial control ({stats['team_b_control']}%)")
            else:
                report['insights'].append(f"Space control is balanced ({ta} {stats['team_a_control']}% vs {tb} {stats['team_b_control']}%)")
            
            if midfield['team_a'] > 55:
                report['insights'].append(f"{ta} controls midfield ({midfield['team_a']}%)")
            elif midfield['team_b'] > 55:
                report['insights'].append(f"{tb} controls midfield ({midfield['team_b']}%)")
                report['recommendations'].append(f"{ta} should add an extra midfielder or drop deeper to contest midfield")
            
            zones = stats['zones']
            if zones['attacking_third']['team_a'] < 20:
                report['recommendations'].append(
                    f"{ta} has very low presence in the attacking third — "
                    f"push forward or increase width"
                )
            if zones['middle_third']['team_b'] > 60:
                report['recommendations'].append(
                    f"{tb} is dominating the middle third — "
                    f"{ta} should press higher or switch play faster"
                )
        
        if not report['recommendations']:
            report['recommendations'].append("Maintain current tactical approach — balanced performance detected")
        
        return report
    
    # Text output
    
    def print_report(self):
        """Print a complete formatted match report."""
        report = self.generate_report()
        mi = report['match_info']
        
        print("\n")
        print("+" + "=" * 60 + "+")
        print("|" + " " * 10 + "SPACEAI FC - MATCH ANALYSIS REPORT" + " " * 16 + "|")
        print("+" + "=" * 60 + "+")
        
        print(f"\n  {mi.get('competition', 'Match')}")
        print(f"  {mi.get('home_team', 'Home')} {mi.get('score_home', 0)} - {mi.get('score_away', 0)} {mi.get('away_team', 'Away')}")
        print(f"  Date: {mi.get('date', 'N/A')}    Minute: {mi.get('minute', 0)}'")
        
        print(f"\n  --- FORMATIONS ---")
        print(f"  {report['team_a']['name']}: {report['team_a']['formation']}")
        print(f"  {report['team_b']['name']}: {report['team_b']['formation']}")
        
        if report['pass_analysis']:
            pa = report['pass_analysis']
            print(f"\n  --- PASS ANALYSIS ---")
            print(f"  Total Passes: {pa['total_passes']}")
            print(f"  Key Distributor: {pa['key_distributor']['name']} (#{pa['key_distributor']['number']})")
            print(f"  Most Involved: {pa['most_involved']['name']} (#{pa['most_involved']['number']})")
            print(f"  Top Connection: {pa['top_connections'][0]['from']} -> {pa['top_connections'][0]['to']} ({pa['top_connections'][0]['passes']} passes)")
        
        if report['space_analysis']:
            sa = report['space_analysis']
            overall = sa['overall']
            mid = sa['midfield']
            print(f"\n  --- SPACE CONTROL ---")
            print(f"  {report['team_a']['name']}: {overall['team_a_control']}%")
            print(f"  {report['team_b']['name']}: {overall['team_b_control']}%")
            print(f"  Midfield: {report['team_a']['name']} {mid['team_a']}% | {report['team_b']['name']} {mid['team_b']}%")
        
        print(f"\n  --- KEY INSIGHTS ---")
        for i, insight in enumerate(report['insights'], 1):
            print(f"  {i}. {insight}")
        
        print(f"\n  --- TACTICAL RECOMMENDATIONS ---")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("\n+" + "=" * 60 + "+")
        print("|" + " " * 18 + "End of Report" + " " * 29 + "|")
        print("+" + "=" * 60 + "+\n")
    
    # Visual dashboard
    
    def draw_dashboard(self, figsize=(20, 14)):
        """
        Generate a visual dashboard combining:
            - Top left: pitch with players
            - Top right: pass network
            - Bottom left: space control
            - Bottom right: stats and insights text
        """
        fig = plt.figure(figsize=figsize, facecolor='#1a1a2e')
        gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.2)
        
        report = self.generate_report()
        mi = report['match_info']
        
        title = f"SpaceAI FC Match Analysis: {mi.get('home_team', 'Home')} vs {mi.get('away_team', 'Away')}"
        fig.suptitle(title, color='white', fontsize=18, fontweight='bold', y=0.98)
        
        ax1 = fig.add_subplot(gs[0, 0])
        self._draw_pitch_panel(ax1)
        
        ax2 = fig.add_subplot(gs[0, 1])
        self._draw_pass_panel(ax2)
        
        ax3 = fig.add_subplot(gs[1, 0])
        self._draw_space_panel(ax3)
        
        ax4 = fig.add_subplot(gs[1, 1])
        self._draw_stats_panel(ax4, report)
        
        return fig
    
    def _draw_pitch_panel(self, ax):
        """Draw pitch with both teams."""
        pitch = Pitch(pitch_type='statsbomb', pitch_color='#1a1a2e',
                      line_color='#e0e0e0', linewidth=1, goal_type='box')
        pitch.draw(ax=ax)
        
        ax.set_title("Formation & Positions", color='white', fontsize=12,
                      fontweight='bold', pad=10)
        
        for p in self.team_a['players']:
            ax.scatter(p['x'], p['y'], c=self.team_a['color'], s=200,
                       edgecolors='white', linewidths=1.5, zorder=6)
            ax.annotate(str(p['number']), xy=(p['x'], p['y']),
                       ha='center', va='center', fontsize=7,
                       fontweight='bold', color='white', zorder=7)
        
        for p in self.team_b['players']:
            ax.scatter(p['x'], p['y'], c=self.team_b['color'], s=200,
                       edgecolors='white', linewidths=1.5, zorder=6)
            ax.annotate(str(p['number']), xy=(p['x'], p['y']),
                       ha='center', va='center', fontsize=7,
                       fontweight='bold', color='white', zorder=7)
        
        if self.ball_pos:
            ax.scatter(self.ball_pos[0], self.ball_pos[1], c='#f1c40f', s=80,
                       edgecolors='white', linewidths=1.5, zorder=8)
        
        form_a = self._detect_formation_simple(self.team_a['players'])
        form_b = self._detect_formation_simple(self.team_b['players'])
        ax.text(25, -3, f"{self.team_a['name']}: {form_a}", ha='center',
                color=self.team_a['color'], fontsize=9, fontweight='bold')
        ax.text(95, -3, f"{self.team_b['name']}: {form_b}", ha='center',
                color=self.team_b['color'], fontsize=9, fontweight='bold')
    
    def _draw_pass_panel(self, ax):
        """Draw pass network panel."""
        pitch = Pitch(pitch_type='statsbomb', pitch_color='#1a1a2e',
                      line_color='#e0e0e0', linewidth=1, goal_type='box')
        pitch.draw(ax=ax)
        
        ax.set_title("Pass Network", color='white', fontsize=12,
                      fontweight='bold', pad=10)
        
        if not self.pass_network:
            ax.text(60, 40, "No pass data", ha='center', va='center',
                    color='#888888', fontsize=14)
            return
        
        pn = self.pass_network
        counts = pn.get_pass_counts()
        max_weight = max((d['weight'] for _, _, d in pn.graph.edges(data=True)), default=1)
        max_inv = max((c['total_involvement'] for c in counts.values()), default=1)
        
        for passer, receiver, data in pn.graph.edges(data=True):
            if data['weight'] >= 2 and passer in pn.players and receiver in pn.players:
                x1 = pn.players[passer]['x']
                y1 = pn.players[passer]['y']
                x2 = pn.players[receiver]['x']
                y2 = pn.players[receiver]['y']
                
                w = data['weight']
                lw = 0.5 + (w / max_weight) * 4
                alpha = 0.3 + (w / max_weight) * 0.5
                
                ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=self.team_a['color'],
                                    lw=lw, alpha=alpha,
                                    connectionstyle="arc3,rad=0.15",
                                    mutation_scale=12), zorder=3)
        
        for pid, player in pn.players.items():
            inv = counts[pid]['total_involvement']
            size = 150 + (inv / max_inv) * 350
            ax.scatter(player['x'], player['y'], c=self.team_a['color'], s=size,
                       edgecolors='white', linewidths=1.5, zorder=6)
            ax.annotate(str(player['number']), xy=(player['x'], player['y']),
                       ha='center', va='center', fontsize=7,
                       fontweight='bold', color='white', zorder=7)
    
    def _draw_space_panel(self, ax):
        """Draw space control panel."""
        pitch = Pitch(pitch_type='statsbomb', pitch_color='#1a1a2e',
                      line_color='#e0e0e0', linewidth=1, goal_type='box')
        pitch.draw(ax=ax)
        
        ax.set_title("Space Control", color='white', fontsize=12,
                      fontweight='bold', pad=10)
        
        if not self.space_control:
            ax.text(60, 40, "No space data", ha='center', va='center',
                    color='#888888', fontsize=14)
            return
        
        from matplotlib.colors import LinearSegmentedColormap
        
        control_grid, stats = self.space_control.compute_influence_control()
        
        cmap = LinearSegmentedColormap.from_list('ctrl',
            [self.team_a['color'], '#1a1a2e', self.team_b['color']], N=256)
        
        extent = [0, 120, 0, 80]
        ax.imshow(control_grid, extent=extent, origin='lower',
                  cmap=cmap, alpha=0.5, aspect='auto', zorder=2,
                  vmin=-1, vmax=1)
        
        for p in self.team_a['players']:
            ax.scatter(p['x'], p['y'], c=self.team_a['color'], s=150,
                       edgecolors='white', linewidths=1.5, zorder=6)
        for p in self.team_b['players']:
            ax.scatter(p['x'], p['y'], c=self.team_b['color'], s=150,
                       edgecolors='white', linewidths=1.5, zorder=6)
        
        ax.text(60, -3,
                f"{self.team_a['name']}: {stats['team_a_control']}% | "
                f"{self.team_b['name']}: {stats['team_b_control']}%",
                ha='center', color='white', fontsize=9, fontweight='bold')
    
    def _draw_stats_panel(self, ax, report=None):
        """Draw stats and insights text panel."""
        if report is None:
            report = self.generate_report()
        
        ax.set_facecolor('#1a1a2e')
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        ax.set_title("Analysis Summary", color='white', fontsize=12,
                      fontweight='bold', pad=10)
        
        mi = report['match_info']
        
        y = 9.5
        line_height = 0.45
        
        score_text = f"{mi.get('home_team', 'Home')} {mi.get('score_home', 0)} - {mi.get('score_away', 0)} {mi.get('away_team', 'Away')}"
        ax.text(5, y, score_text, ha='center', va='top', fontsize=13,
                fontweight='bold', color='white')
        y -= line_height * 1.5
        
        ax.text(5, y, f"{mi.get('competition', '')}  |  {mi.get('minute', 0)}'",
                ha='center', va='top', fontsize=9, color='#aaaaaa')
        y -= line_height * 1.8
        
        ax.text(0.5, y, "FORMATIONS", va='top', fontsize=10,
                fontweight='bold', color='#f1c40f')
        y -= line_height
        ax.text(0.5, y, f"{report['team_a']['name']}: {report['team_a']['formation']}",
                va='top', fontsize=9, color='white')
        y -= line_height
        ax.text(0.5, y, f"{report['team_b']['name']}: {report['team_b']['formation']}",
                va='top', fontsize=9, color='white')
        y -= line_height * 1.5
        
        ax.text(0.5, y, "KEY INSIGHTS", va='top', fontsize=10,
                fontweight='bold', color='#f1c40f')
        y -= line_height
        
        for insight in report['insights'][:5]:
            if len(insight) > 55:
                ax.text(0.5, y, insight[:55] + "...", va='top',
                        fontsize=8, color='white')
            else:
                ax.text(0.5, y, insight, va='top', fontsize=8, color='white')
            y -= line_height
        
        y -= line_height * 0.5
        
        ax.text(0.5, y, "RECOMMENDATIONS", va='top', fontsize=10,
                fontweight='bold', color='#2ecc71')
        y -= line_height
        
        for rec in report['recommendations'][:4]:
            if len(rec) > 55:
                ax.text(0.5, y, "• " + rec[:55] + "...", va='top',
                        fontsize=8, color='white')
            else:
                ax.text(0.5, y, "• " + rec, va='top', fontsize=8, color='white')
            y -= line_height
    
    # Save
    
    def save_dashboard(self, fig, filename="match_report.png"):
        """Save the dashboard to outputs folder."""
        fig.savefig(f"outputs/{filename}", dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved: outputs/{filename}")
    
    # Word document export
    
    def export_document(self, filename="match_report.docx"):
        """Export the match report as a Word document."""
        from docx import Document as DocxDocument
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        import os
        
        doc = DocxDocument()
        
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Arial'
        font.size = Pt(11)
        
        report = self.generate_report()
        mi = report['match_info']
        
        # Title
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.add_run("SpaceAI FC - Match Analysis Report")
        run.bold = True
        run.font.size = Pt(24)
        run.font.color.rgb = RGBColor(0x1A, 0x35, 0x50)
        
        # Match Info
        subtitle = doc.add_paragraph()
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = subtitle.add_run(
            f"{mi.get('home_team', 'Home')} {mi.get('score_home', 0)} - "
            f"{mi.get('score_away', 0)} {mi.get('away_team', 'Away')}"
        )
        run.bold = True
        run.font.size = Pt(18)
        
        info = doc.add_paragraph()
        info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = info.add_run(
            f"{mi.get('competition', '')}  |  Minute: {mi.get('minute', 0)}'  |  {mi.get('date', '')}"
        )
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0x77, 0x77, 0x77)
        
        doc.add_paragraph("")
        
        # Formations
        h = doc.add_heading("Formations", level=1)
        h.runs[0].font.color.rgb = RGBColor(0x1A, 0x35, 0x50)
        
        doc.add_paragraph(f"{report['team_a']['name']}: {report['team_a']['formation']}")
        doc.add_paragraph(f"{report['team_b']['name']}: {report['team_b']['formation']}")
        
        # Pass Analysis
        if report['pass_analysis']:
            pa = report['pass_analysis']
            h = doc.add_heading("Pass Analysis", level=1)
            h.runs[0].font.color.rgb = RGBColor(0x1A, 0x35, 0x50)
            
            doc.add_paragraph(f"Total Passes: {pa['total_passes']}")
            doc.add_paragraph(
                f"Key Distributor: {pa['key_distributor']['name']} "
                f"(#{pa['key_distributor']['number']})"
            )
            doc.add_paragraph(
                f"Most Involved: {pa['most_involved']['name']} "
                f"(#{pa['most_involved']['number']}) - "
                f"{pa['most_involved']['passes_made']} made, "
                f"{pa['most_involved']['passes_received']} received"
            )
            
            h2 = doc.add_heading("Top Connections", level=2)
            h2.runs[0].font.color.rgb = RGBColor(0x29, 0x80, 0xB9)
            for conn in pa['top_connections']:
                doc.add_paragraph(
                    f"{conn['from']} \u2192 {conn['to']}: {conn['passes']} passes",
                    style='List Bullet'
                )
            
            if pa['weak_links']:
                h2 = doc.add_heading("Weak Links", level=2)
                h2.runs[0].font.color.rgb = RGBColor(0x29, 0x80, 0xB9)
                for wl in pa['weak_links']:
                    doc.add_paragraph(
                        f"{wl['name']} (#{wl['number']}): {wl['total_involvement']} total involvements",
                        style='List Bullet'
                    )
        
        # Space Control
        if report['space_analysis']:
            sa = report['space_analysis']
            overall = sa['overall']
            mid = sa['midfield']
            
            h = doc.add_heading("Space Control", level=1)
            h.runs[0].font.color.rgb = RGBColor(0x1A, 0x35, 0x50)
            
            doc.add_paragraph(
                f"Overall: {report['team_a']['name']} {overall['team_a_control']}% | "
                f"{report['team_b']['name']} {overall['team_b_control']}%"
            )
            doc.add_paragraph(
                f"Midfield Control: {report['team_a']['name']} {mid['team_a']}% | "
                f"{report['team_b']['name']} {mid['team_b']}%"
            )
            
            zones = overall['zones']
            h2 = doc.add_heading("Zone Breakdown", level=2)
            h2.runs[0].font.color.rgb = RGBColor(0x29, 0x80, 0xB9)
            doc.add_paragraph(
                f"Defensive Third: {report['team_a']['name']} {zones['defensive_third']['team_a']}% | "
                f"{report['team_b']['name']} {zones['defensive_third']['team_b']}%",
                style='List Bullet'
            )
            doc.add_paragraph(
                f"Middle Third: {report['team_a']['name']} {zones['middle_third']['team_a']}% | "
                f"{report['team_b']['name']} {zones['middle_third']['team_b']}%",
                style='List Bullet'
            )
            doc.add_paragraph(
                f"Attacking Third: {report['team_a']['name']} {zones['attacking_third']['team_a']}% | "
                f"{report['team_b']['name']} {zones['attacking_third']['team_b']}%",
                style='List Bullet'
            )
        
        # Visualizations
        h = doc.add_heading("Visualizations", level=1)
        h.runs[0].font.color.rgb = RGBColor(0x1A, 0x35, 0x50)
        
        image_files = [
            ("outputs/01_pitch.png", "Formation & Player Positions"),
            ("outputs/02_pass_network.png", "Pass Network"),
            ("outputs/03_pass_sequence.png", "Build-Up Sequence"),
            ("outputs/04_space_voronoi.png", "Space Control (Voronoi)"),
            ("outputs/05_space_influence.png", "Space Control (Influence)"),
            ("outputs/06_match_dashboard.png", "Full Match Dashboard"),
        ]
        
        for img_path, caption in image_files:
            if os.path.exists(img_path):
                h2 = doc.add_heading(caption, level=2)
                h2.runs[0].font.color.rgb = RGBColor(0x29, 0x80, 0xB9)
                doc.add_picture(img_path, width=Inches(6))
                last_paragraph = doc.paragraphs[-1]
                last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                doc.add_paragraph("")
        
        # Key Insights
        h = doc.add_heading("Key Insights", level=1)
        h.runs[0].font.color.rgb = RGBColor(0x1A, 0x35, 0x50)
        
        for i, insight in enumerate(report['insights'], 1):
            p = doc.add_paragraph()
            run = p.add_run(f"{i}. ")
            run.bold = True
            p.add_run(insight)
        
        # Recommendations
        h = doc.add_heading("Tactical Recommendations", level=1)
        h.runs[0].font.color.rgb = RGBColor(0x1A, 0x35, 0x50)
        
        for rec in report['recommendations']:
            doc.add_paragraph(rec, style='List Bullet')
        
        # Footer
        doc.add_paragraph("")
        footer = doc.add_paragraph()
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = footer.add_run("Generated by SpaceAI FC - Tactical Analysis Engine v1")
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0xAA, 0xAA, 0xAA)
        run.italic = True
        
        filepath = f"outputs/{filename}"
        doc.save(filepath)
        print(f"Saved: {filepath}")


# Quick test - Full El Clásico analysis

if __name__ == "__main__":
    
    import sys
    sys.path.insert(0, '.')
    from engine.analysis.pass_network import PassNetwork
    from engine.analysis.space_control import SpaceControl
    
    barca_players = [
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
    
    madrid_players = [
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
    
    pn = PassNetwork()
    pn.add_players(barca_players)
    
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
    pn.add_passes(passes)
    
    sc = SpaceControl()
    sc.set_teams(barca_players, madrid_players)
    sc.set_ball(60, 40)
    
    mr = MatchReport()
    
    mr.set_match_info(
        home_team="FC Barcelona",
        away_team="Real Madrid",
        score_home=2,
        score_away=1,
        minute=72,
        competition="La Liga",
        date="2026-03-22"
    )
    
    mr.set_team_a("FC Barcelona", "#a50044", barca_players)
    mr.set_team_b("Real Madrid", "#ffffff", madrid_players)
    mr.set_ball(60, 40)
    mr.set_pass_network(pn)
    mr.set_space_control(sc)
    
    mr.print_report()
    
    fig = mr.draw_dashboard()
    mr.save_dashboard(fig, "el_clasico_report.png")
    mr.export_document("el_clasico_report.docx")
    
    plt.show()
    print("\nMatch report complete!")