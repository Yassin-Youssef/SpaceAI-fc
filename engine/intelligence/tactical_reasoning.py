"""
SpaceAI FC - Tactical Reasoning Engine
=========================================
Takes all analysis results from Phase 1 and 2 and reasons about
what's happening tactically using if/then rules and the knowledge graph.
Produces SWOT-style categorized insights.
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np


class TacticalReasoner:
    """
    Rule-based reasoning engine that analyses Phase 1+2 results and
    produces SWOT-categorised tactical insights.
    
    SWOT:
        - Strengths: what the team does well
        - Weaknesses: vulnerabilities and problems
        - Opportunities: things to exploit about the opponent
        - Threats: dangers from the opponent
    """
    
    def __init__(self, knowledge_graph=None):
        """
        Parameters:
            knowledge_graph: TacticalKnowledgeGraph instance (optional but recommended)
        """
        self.knowledge_graph = knowledge_graph
        self.analysis_data = {}
        self.team_name = "Team"
        self.opponent_name = "Opponent"
    
    # ── Data input ──────────────────────────────────────────────
    
    def set_analysis(self, data, team_name="Team", opponent_name="Opponent"):
        """
        Set analysis data from Phase 1+2 modules.
        
        Parameters:
            data: dict with keys:
                'formation_a': dict from FormationDetector (our team)
                'formation_b': dict from FormationDetector (opponent)
                'space_control': dict with 'team_a_control', 'team_b_control', 'zones', 'midfield'
                'pass_summary': dict from PassNetwork.get_summary()
                'press_resistance': dict from PressResistance.analyze()
                'patterns_a': list from PatternDetector (our team)
                'patterns_b': list from PatternDetector (opponent)
                'roles_a': list from RoleClassifier (our team)
                'roles_b': list from RoleClassifier (opponent)
        """
        self.analysis_data = data
        self.team_name = team_name
        self.opponent_name = opponent_name
    
    # ── Reasoning ───────────────────────────────────────────────
    
    def reason(self):
        """
        Apply all rules to the analysis data and produce SWOT insights.
        
        Returns:
            dict with 'strengths', 'weaknesses', 'opportunities', 'threats',
                  'situations', 'suggested_strategies'
        """
        insights = {
            'strengths': [],
            'weaknesses': [],
            'opportunities': [],
            'threats': [],
            'situations': [],
            'suggested_strategies': [],
        }
        
        d = self.analysis_data
        
        # Apply all rules
        self._rule_space_dominance(d, insights)
        self._rule_midfield_control(d, insights)
        self._rule_press_resistance(d, insights)
        self._rule_key_distributor_overreliance(d, insights)
        self._rule_weak_links(d, insights)
        self._rule_formation_matchup(d, insights)
        self._rule_high_line_risk(d, insights)
        self._rule_low_block_situation(d, insights)
        self._rule_compact_block_opponent(d, insights)
        self._rule_overlapping_runs(d, insights)
        self._rule_wide_overload(d, insights)
        self._rule_attacking_third_presence(d, insights)
        self._rule_build_up_route(d, insights)
        self._rule_false_nine_usage(d, insights)
        self._rule_inverted_winger_threat(d, insights)
        self._rule_press_resistance_low_combined(d, insights)
        
        # Query knowledge graph for counter-strategies
        if self.knowledge_graph and insights['situations']:
            formation = d.get('formation_a', {}).get('formation', '')
            for situation in insights['situations']:
                counters = self.knowledge_graph.get_counter_strategies(situation)
                for c in counters:
                    if c not in insights['suggested_strategies']:
                        insights['suggested_strategies'].append(c)
                
                result = self.knowledge_graph.query(formation, situation)
                if result['is_weak_against']:
                    insights['threats'].append({
                        'category': 'threat',
                        'description': f"{self.team_name}'s {formation} is weak against {situation.replace('_', ' ')}",
                        'confidence': 0.7,
                        'action': f"Consider formation adjustment — {formation} struggles in this scenario",
                    })
        
        return insights
    
    # ── Rules ───────────────────────────────────────────────────
    
    def _rule_space_dominance(self, d, insights):
        """Rule 1: Space control dominance."""
        sc = d.get('space_control', {})
        ctrl_a = sc.get('team_a_control', 50)
        ctrl_b = sc.get('team_b_control', 50)
        
        if ctrl_a > 55:
            insights['strengths'].append({
                'category': 'strength',
                'description': f"{self.team_name} dominates territorial control ({ctrl_a}%)",
                'confidence': 0.8,
                'action': "Maintain possession dominance and territorial pressure",
            })
        elif ctrl_b > 55:
            insights['weaknesses'].append({
                'category': 'weakness',
                'description': f"{self.opponent_name} controls more territory ({ctrl_b}%)",
                'confidence': 0.8,
                'action': "Push forward and contest territorial control",
            })
    
    def _rule_midfield_control(self, d, insights):
        """Rule 2: Midfield control."""
        sc = d.get('space_control', {})
        mid = sc.get('midfield', {})
        mid_a = mid.get('team_a', 50)
        mid_b = mid.get('team_b', 50)
        
        if mid_a > 55:
            insights['strengths'].append({
                'category': 'strength',
                'description': f"{self.team_name} controls the midfield zone ({mid_a}%)",
                'confidence': 0.75,
                'action': "Use midfield control to dictate tempo",
            })
        elif mid_b > 55:
            insights['weaknesses'].append({
                'category': 'weakness',
                'description': f"{self.opponent_name} dominates midfield ({mid_b}%)",
                'confidence': 0.75,
                'action': "Add a midfielder or switch to a more compact shape",
            })
            insights['situations'].append('midfield_overload')
    
    def _rule_press_resistance(self, d, insights):
        """Rule 3: Press resistance assessment."""
        pr = d.get('press_resistance', {})
        score = pr.get('press_resistance_score', 50)
        
        if score >= 70:
            insights['strengths'].append({
                'category': 'strength',
                'description': f"Strong press resistance (score: {score:.0f}/100)",
                'confidence': 0.8,
                'action': "Continue playing through opponent's press confidently",
            })
        elif score < 45:
            insights['weaknesses'].append({
                'category': 'weakness',
                'description': f"Vulnerable under pressure (score: {score:.0f}/100)",
                'confidence': 0.85,
                'action': "Vary build-up routes, go long when pressed",
            })
            insights['situations'].append('high_press')
    
    def _rule_key_distributor_overreliance(self, d, insights):
        """Rule 4: Over-reliance on one player in build-up."""
        ps = d.get('pass_summary', {})
        kp = ps.get('key_distributor', {})
        betweenness = kp.get('betweenness', 0)
        
        if betweenness > 0.3:
            name = kp.get('name', 'Unknown')
            insights['weaknesses'].append({
                'category': 'weakness',
                'description': (f"Over-reliance on {name} in build-up "
                               f"(betweenness: {betweenness:.2f})"),
                'confidence': 0.7,
                'action': f"Develop alternative build-up routes bypassing {name}",
            })
            insights['situations'].append('single_buildup_route')
    
    def _rule_weak_links(self, d, insights):
        """Rule 5: Players with low involvement."""
        ps = d.get('pass_summary', {})
        weak_links = ps.get('weak_links', [])
        
        for wl in weak_links:
            insights['weaknesses'].append({
                'category': 'weakness',
                'description': (f"{wl['name']} (#{wl['number']}) is disconnected "
                               f"({wl['total_involvement']} involvements)"),
                'confidence': 0.65,
                'action': f"Actively involve {wl['name']} in build-up play",
            })
    
    def _rule_formation_matchup(self, d, insights):
        """Rule 6: Formation versus formation analysis."""
        fa = d.get('formation_a', {}).get('formation', '')
        fb = d.get('formation_b', {}).get('formation', '')
        
        if not fa or not fb:
            return
        
        if self.knowledge_graph:
            # Check strengths and weaknesses of our formation
            strengths = self.knowledge_graph.get_formation_strengths(fa)
            for s in strengths:
                insights['strengths'].append({
                    'category': 'strength',
                    'description': f"{fa} excels in {s['situation'].replace('_', ' ')}",
                    'confidence': 0.6,
                    'action': f"Leverage the natural strength of {fa} in this area",
                })
    
    def _rule_high_line_risk(self, d, insights):
        """Rule 7: High defensive line risk."""
        patterns_a = d.get('patterns_a', [])
        patterns_b = d.get('patterns_b', [])
        
        # Our high line
        for p in patterns_a:
            if p.get('pattern') == 'High Line' and p.get('detected'):
                # Check if opponent has fast forwards
                insights['threats'].append({
                    'category': 'threat',
                    'description': f"{self.team_name} playing a high line — vulnerable to counter-attacks",
                    'confidence': p.get('confidence', 0.5),
                    'action': "Ensure cover behind the line, track runners carefully",
                })
                insights['situations'].append('high_line')
        
        # Opponent high line = opportunity
        for p in patterns_b:
            if p.get('pattern') == 'High Line' and p.get('detected'):
                insights['opportunities'].append({
                    'category': 'opportunity',
                    'description': f"{self.opponent_name} playing high line — space behind to exploit",
                    'confidence': p.get('confidence', 0.5),
                    'action': "Use long balls and through-balls behind their defensive line",
                })
    
    def _rule_low_block_situation(self, d, insights):
        """Rule 8: Low block detection."""
        patterns_b = d.get('patterns_b', [])
        
        for p in patterns_b:
            if p.get('pattern') == 'Low Block' and p.get('detected'):
                insights['threats'].append({
                    'category': 'threat',
                    'description': f"{self.opponent_name} is in a low block — difficult to break down",
                    'confidence': p.get('confidence', 0.5),
                    'action': "Patient build-up, exploit width, use crosses and set pieces",
                })
                insights['situations'].append('low_block')
    
    def _rule_compact_block_opponent(self, d, insights):
        """Rule 9: Opponent compact block."""
        patterns_b = d.get('patterns_b', [])
        
        for p in patterns_b:
            if p.get('pattern') == 'Compact Block' and p.get('detected'):
                insights['threats'].append({
                    'category': 'threat',
                    'description': f"{self.opponent_name} in compact shape — hard to play through",
                    'confidence': p.get('confidence', 0.5),
                    'action': "Switch play quickly to stretch the compact block",
                })
                insights['situations'].append('park_the_bus')
    
    def _rule_overlapping_runs(self, d, insights):
        """Rule 10: Overlapping runs detected."""
        patterns_a = d.get('patterns_a', [])
        
        for p in patterns_a:
            if p.get('pattern') == 'Overlapping Run' and p.get('detected'):
                players = p.get('involved_players', [])
                insights['strengths'].append({
                    'category': 'strength',
                    'description': f"Overlapping run detected ({', '.join(players)})",
                    'confidence': p.get('confidence', 0.5),
                    'action': "Continue using overlaps to create 2v1 situations in wide areas",
                })
    
    def _rule_wide_overload(self, d, insights):
        """Rule 11: Wide overload detected."""
        patterns_a = d.get('patterns_a', [])
        
        for p in patterns_a:
            if 'Wide Overload' in p.get('pattern', '') and p.get('detected'):
                insights['strengths'].append({
                    'category': 'strength',
                    'description': f"{p['pattern']} — numerical advantage in wide area",
                    'confidence': p.get('confidence', 0.5),
                    'action': "Exploit the overloaded flank with quick combinations",
                })
    
    def _rule_attacking_third_presence(self, d, insights):
        """Rule 12: Attacking third control."""
        sc = d.get('space_control', {})
        zones = sc.get('zones', {})
        att = zones.get('attacking_third', {})
        
        att_a = att.get('team_a', 50)
        if att_a < 25:
            insights['weaknesses'].append({
                'category': 'weakness',
                'description': f"Low presence in attacking third ({att_a}%)",
                'confidence': 0.7,
                'action': "Push forward, increase width, commit more players to attack",
            })
        elif att_a > 45:
            insights['strengths'].append({
                'category': 'strength',
                'description': f"Strong attacking third presence ({att_a}%)",
                'confidence': 0.7,
                'action': "Maintain attacking pressure and look for openings",
            })
    
    def _rule_build_up_route(self, d, insights):
        """Rule 13: Build-up predictability."""
        ps = d.get('pass_summary', {})
        top = ps.get('top_connections', [])
        total = ps.get('total_passes', 1)
        
        if top and total > 0:
            top_passes = top[0].get('passes', 0)
            ratio = top_passes / total
            if ratio > 0.12:
                insights['weaknesses'].append({
                    'category': 'weakness',
                    'description': (f"Build-up overly reliant on {top[0]['from']} → {top[0]['to']} "
                                   f"axis ({top_passes}/{total} passes)"),
                    'confidence': 0.6,
                    'action': "Diversify passing lanes to reduce predictability",
                })
    
    def _rule_false_nine_usage(self, d, insights):
        """Rule 14: False nine creating space."""
        roles = d.get('roles_a', [])
        for r in roles:
            if r.get('role') == 'False Nine':
                insights['strengths'].append({
                    'category': 'strength',
                    'description': f"{r['name']} operating as False Nine — creating space for runners",
                    'confidence': r.get('confidence', 0.5),
                    'action': "Ensure midfielders exploit the space created by the False Nine",
                })
    
    def _rule_inverted_winger_threat(self, d, insights):
        """Rule 15: Inverted winger cutting inside."""
        roles = d.get('roles_a', [])
        for r in roles:
            if r.get('role') == 'Inverted Winger':
                insights['strengths'].append({
                    'category': 'strength',
                    'description': f"{r['name']} cutting inside as Inverted Winger",
                    'confidence': r.get('confidence', 0.5),
                    'action': "Use inverted runs to create shooting opportunities from the half-space",
                })
        
        # Opponent's inverted wingers = threat
        roles_b = d.get('roles_b', [])
        for r in roles_b:
            if r.get('role') == 'Inverted Winger':
                insights['threats'].append({
                    'category': 'threat',
                    'description': f"{r['name']} is an Inverted Winger threat — cuts inside",
                    'confidence': r.get('confidence', 0.5),
                    'action': f"Fullback must stay goalside of {r['name']} and deny inside runs",
                })
    
    def _rule_press_resistance_low_combined(self, d, insights):
        """Rule 16: Low press resistance combined with midfield weakness."""
        pr = d.get('press_resistance', {})
        score = pr.get('press_resistance_score', 50)
        sc = d.get('space_control', {})
        mid = sc.get('midfield', {})
        mid_b = mid.get('team_b', 50)
        
        if score < 50 and mid_b > 55:
            insights['weaknesses'].append({
                'category': 'weakness',
                'description': (f"Critical: midfield progression difficulty — "
                               f"low press resistance ({score:.0f}/100) combined with "
                               f"opponent midfield control ({mid_b}%)"),
                'confidence': 0.9,
                'action': "Drop an attacker deeper to create a passing option, or go long",
            })
    
    # ── Visualization ───────────────────────────────────────────
    
    def draw(self, results=None, figsize=(14, 8), title=None):
        """
        Draw SWOT analysis panel.
        
        Returns:
            fig, axes
        """
        if results is None:
            results = self.reason()
        
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.patch.set_facecolor('#1a1a2e')
        
        if title:
            fig.suptitle(title, color='white', fontsize=16,
                         fontweight='bold', y=0.98)
        
        swot = [
            ('STRENGTHS', results['strengths'], '#2ecc71', axes[0, 0]),
            ('WEAKNESSES', results['weaknesses'], '#e74c3c', axes[0, 1]),
            ('OPPORTUNITIES', results['opportunities'], '#3498db', axes[1, 0]),
            ('THREATS', results['threats'], '#f39c12', axes[1, 1]),
        ]
        
        for label, items, color, ax in swot:
            ax.set_facecolor('#1a1a2e')
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 10)
            ax.axis('off')
            
            # Header
            ax.text(5, 9.5, label, ha='center', va='top', fontsize=14,
                    fontweight='bold', color=color,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#2a2a3e',
                              edgecolor=color, linewidth=2))
            
            y = 8.5
            if items:
                for item in items[:4]:
                    desc = item['description']
                    if len(desc) > 60:
                        desc = desc[:57] + "..."
                    conf = item.get('confidence', 0)
                    ax.text(0.5, y, f"• {desc}", va='top', fontsize=7,
                            color='white', wrap=True)
                    y -= 1.2
                    
                    action = item.get('action', '')
                    if action and len(action) > 55:
                        action = action[:52] + "..."
                    if action:
                        ax.text(1.0, y, f"→ {action}", va='top', fontsize=6,
                                color='#aaaaaa', style='italic')
                        y -= 1.0
            else:
                ax.text(5, 5, "None detected", ha='center', va='center',
                        fontsize=10, color='#555555')
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        return fig, axes
    
    # ── Text output ─────────────────────────────────────────────
    
    def print_analysis(self, results=None):
        """Print formatted SWOT analysis."""
        if results is None:
            results = self.reason()
        
        print("\n" + "=" * 60)
        print("  TACTICAL REASONING — SWOT ANALYSIS")
        print("=" * 60)
        print(f"\n  Team: {self.team_name}  vs  {self.opponent_name}")
        
        for category, label, color_code in [
            ('strengths', 'STRENGTHS', '+'),
            ('weaknesses', 'WEAKNESSES', '-'),
            ('opportunities', 'OPPORTUNITIES', '*'),
            ('threats', 'THREATS', '!'),
        ]:
            items = results[category]
            print(f"\n  --- {label} ({len(items)}) ---")
            if items:
                for item in items:
                    print(f"  [{color_code}] {item['description']} (conf: {item['confidence']:.0%})")
                    print(f"      Action: {item['action']}")
            else:
                print(f"  (none detected)")
        
        if results['situations']:
            print(f"\n  --- DETECTED SITUATIONS ---")
            for s in set(results['situations']):
                print(f"    • {s.replace('_', ' ')}")
        
        if results['suggested_strategies']:
            print(f"\n  --- SUGGESTED STRATEGIES (from Knowledge Graph) ---")
            for s in results['suggested_strategies']:
                print(f"    → {s['strategy'].replace('_', ' ')}: {s['description']}")
        
        print("\n" + "=" * 60)
    
    # ── Save ────────────────────────────────────────────────────
    
    def save(self, fig, filename):
        """Save figure to outputs folder."""
        fig.savefig(f"outputs/{filename}", dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved: outputs/{filename}")


# ═══════════════════════════════════════════════════════════════
# Quick test — Reasoning from Phase 1+2 data
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    
    import os
    import sys
    import random
    sys.path.insert(0, '.')
    os.makedirs("outputs", exist_ok=True)
    
    import matplotlib
    matplotlib.use('Agg')
    
    import numpy as np
    from engine.analysis.formation_detection import FormationDetector
    from engine.analysis.role_classifier import RoleClassifier
    from engine.analysis.press_resistance import PressResistance
    from engine.analysis.pattern_detection import PatternDetector
    from engine.analysis.pass_network import PassNetwork
    from engine.analysis.space_control import SpaceControl
    from engine.intelligence.knowledge_graph import TacticalKnowledgeGraph
    
    # ── Team data ───────────────────────────────────────────────
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
        (1, 4), (1, 2), (1, 4), (4, 8), (4, 21), (4, 8), (4, 23), (4, 2),
        (2, 21), (2, 3), (2, 8), (2, 21), (2, 4), (23, 19), (23, 8), (23, 19), (23, 4),
        (3, 11), (3, 21), (3, 11), (3, 2), (8, 6), (8, 19), (8, 23), (8, 21), (8, 9),
        (8, 6), (8, 19), (8, 4), (8, 9), (8, 11), (8, 6), (8, 21), (8, 23),
        (21, 8), (21, 2), (21, 3), (21, 6), (21, 11), (21, 8), (21, 4), (21, 6),
        (6, 9), (6, 19), (6, 8), (6, 11), (6, 9), (6, 8), (6, 19), (6, 21),
        (19, 9), (19, 23), (19, 6), (19, 8), (19, 9), (19, 6),
        (11, 9), (11, 3), (11, 6), (11, 21), (11, 9), (11, 6),
        (9, 6), (9, 19), (9, 8), (9, 11), (6, 8), (19, 8), (9, 6), (11, 21),
    ]
    
    # ── Run Phase 1+2 analysis ──────────────────────────────────
    
    # Formation
    fd_b = FormationDetector()
    fd_b.set_team(barca, "FC Barcelona", "#a50044")
    form_b = fd_b.detect()
    
    fd_m = FormationDetector()
    fd_m.set_team(madrid, "Real Madrid", "#ffffff")
    form_m = fd_m.detect()
    
    # Pass network
    pn = PassNetwork()
    pn.add_players(barca)
    pn.add_passes(passes)
    pass_summary = pn.get_summary()
    
    # Space control
    sc = SpaceControl()
    sc.set_teams(barca, madrid)
    sc.set_ball(60, 40)
    _, stats = sc.compute_influence_control()
    midfield = sc.get_midfield_control(_)
    
    # Roles
    rc_b = RoleClassifier()
    rc_b.set_team(barca, "FC Barcelona", "#a50044")
    roles_b = rc_b.classify_all()
    
    rc_m = RoleClassifier()
    rc_m.set_team(madrid, "Real Madrid", "#ffffff")
    roles_m = rc_m.classify_all()
    
    # Press resistance
    random.seed(42)
    events = []
    outfield = [p for p in barca if p['position'] != 'GK']
    for _ in range(65):
        passer = random.choice(outfield)
        receiver = random.choice(outfield)
        px = max(0, min(120, passer['x'] + random.gauss(0, 3)))
        py = max(0, min(80, passer['y'] + random.gauss(0, 3)))
        opp_pos = np.array([[p['x'], p['y']] for p in madrid])
        dist = np.linalg.norm(opp_pos - np.array([px, py]), axis=1)
        nearby = np.sum(dist < 10)
        success = random.random() < (0.55 if nearby >= 2 else 0.90)
        events.append({'passer': passer['number'], 'receiver': receiver['number'],
                       'success': success, 'x': px, 'y': py,
                       'end_x': receiver['x'], 'end_y': receiver['y']})
    
    pr = PressResistance()
    pr.set_teams(barca, madrid, "FC Barcelona", "#a50044", "Real Madrid")
    pr.add_pass_events(events)
    pr_result = pr.analyze()
    
    # Patterns
    ptd = PatternDetector()
    ptd.set_teams(barca, madrid, "FC Barcelona", "Real Madrid", "#a50044", "#ffffff")
    patterns_a = ptd.detect_all(team="a")
    patterns_b = ptd.detect_all(team="b")
    
    # ── Build analysis data dict ────────────────────────────────
    
    analysis_data = {
        'formation_a': form_b,
        'formation_b': form_m,
        'space_control': {
            'team_a_control': stats['team_a_control'],
            'team_b_control': stats['team_b_control'],
            'zones': stats['zones'],
            'midfield': midfield,
        },
        'pass_summary': pass_summary,
        'press_resistance': pr_result,
        'patterns_a': patterns_a,
        'patterns_b': patterns_b,
        'roles_a': roles_b,
        'roles_b': roles_m,
    }
    
    # ── Run reasoning ───────────────────────────────────────────
    
    kg = TacticalKnowledgeGraph()
    reasoner = TacticalReasoner(knowledge_graph=kg)
    reasoner.set_analysis(analysis_data, "FC Barcelona", "Real Madrid")
    
    results = reasoner.reason()
    reasoner.print_analysis(results)
    
    fig, axes = reasoner.draw(results,
                               title="SpaceAI FC - Tactical SWOT Analysis")
    reasoner.save(fig, "swot_analysis.png")
    
    plt.show()
    print("\nTactical reasoning complete!")
