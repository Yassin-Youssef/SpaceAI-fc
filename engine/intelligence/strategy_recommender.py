"""
SpaceAI FC - Strategy Recommendation System  
=============================================
Takes reasoning output (SWOT) and knowledge graph to generate
specific, prioritized tactical recommendations.
"""

import matplotlib.pyplot as plt
import numpy as np


class StrategyRecommender:
    """
    Generates prioritized tactical recommendations from SWOT analysis.
    
    Recommendation categories:
        - Formation change
        - Pressing adjustment
        - Attacking strategy
        - Defensive adjustment
        - Player-specific instruction
    """
    
    def __init__(self, knowledge_graph=None):
        self.knowledge_graph = knowledge_graph
        self.swot_results = {}
        self.analysis_data = {}
        self.team_name = "Team"
        self.opponent_name = "Opponent"
    
    # ── Data input ──────────────────────────────────────────────
    
    def set_reasoning(self, swot_results, analysis_data=None,
                      team_name="Team", opponent_name="Opponent"):
        """
        Set SWOT results from TacticalReasoner and raw analysis data.
        
        Parameters:
            swot_results: output from TacticalReasoner.reason()
            analysis_data: original Phase 1+2 analysis dict (optional, for player-specific recs)
        """
        self.swot_results = swot_results
        self.analysis_data = analysis_data or {}
        self.team_name = team_name
        self.opponent_name = opponent_name
    
    # ── Recommendation generation ───────────────────────────────
    
    def recommend(self):
        """
        Generate prioritized tactical recommendations.
        
        Returns:
            list of recommendation dicts, sorted by priority, each with:
                'priority': 'high' / 'medium' / 'low'
                'category': str
                'description': str
                'reasoning': str (why this is suggested)
                'expected_impact': str
        """
        recs = []
        
        recs.extend(self._recommend_formation_changes())
        recs.extend(self._recommend_pressing_adjustments())
        recs.extend(self._recommend_attacking_strategy())
        recs.extend(self._recommend_defensive_adjustments())
        recs.extend(self._recommend_player_specific())
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recs.sort(key=lambda r: priority_order.get(r['priority'], 3))
        
        return recs
    
    def _recommend_formation_changes(self):
        """Generate formation change recommendations."""
        recs = []
        swot = self.swot_results
        situations = swot.get('situations', [])
        formation = self.analysis_data.get('formation_a', {}).get('formation', '')
        
        # If opponent is in a low block, suggest width
        if 'low_block' in situations or 'park_the_bus' in situations:
            recs.append({
                'priority': 'medium',
                'category': 'Formation Change',
                'description': f"Consider switching to a 3-4-3 or widening formation to stretch the block",
                'reasoning': f"{self.opponent_name} is in a compact/low block — narrow formations struggle to penetrate",
                'expected_impact': "Creates more width and angles to break down the defensive structure",
            })
        
        # If we're being pressed and formation is build-up heavy
        if 'high_press' in situations and formation in ('4-2-3-1', '4-3-3'):
            recs.append({
                'priority': 'medium',
                'category': 'Formation Change',
                'description': f"Add a midfielder (switch to 4-3-3 or triple pivot) to aid build-up under pressure",
                'reasoning': f"Under heavy press, {formation} can leave the midfield duo isolated",
                'expected_impact': "Extra passing option in build-up phase to escape the press",
            })
        
        # Knowledge graph formation suggestions
        if self.knowledge_graph and formation:
            weaknesses = self.knowledge_graph.get_formation_weaknesses(formation)
            active_weak_situations = [w['situation'] for w in weaknesses if w['situation'] in situations]
            if active_weak_situations:
                recs.append({
                    'priority': 'high',
                    'category': 'Formation Change',
                    'description': (f"{formation} is weak against {', '.join(s.replace('_', ' ') for s in active_weak_situations)} "
                                   f"— consider an alternative formation"),
                    'reasoning': f"Knowledge graph identifies {formation} as vulnerable in current tactical situation",
                    'expected_impact': "Reduces tactical mismatch and improves structural balance",
                })
        
        return recs
    
    def _recommend_pressing_adjustments(self):
        """Generate pressing adjustment recommendations."""
        recs = []
        swot = self.swot_results
        pr = self.analysis_data.get('press_resistance', {})
        score = pr.get('press_resistance_score', 50)
        
        # If our press resistance is low
        if score < 45:
            recs.append({
                'priority': 'high',
                'category': 'Pressing Adjustment',
                'description': "Use targeted press triggers instead of constant pressing — press only when ball goes to weak passers",
                'reasoning': f"Press resistance score is low ({score:.0f}/100), but pressing smarter can reduce turnovers",
                'expected_impact': "Reduces ball losses under pressure while maintaining defensive intensity",
            })
        
        # If vulnerable zones exist
        vulnerable = pr.get('vulnerable_zones', [])
        if vulnerable:
            worst = vulnerable[0]
            recs.append({
                'priority': 'medium',
                'category': 'Pressing Adjustment',
                'description': f"Avoid building through {worst['zone']} — success rate only {worst['success_rate']:.0%}",
                'reasoning': f"Opponent's press is most effective in {worst['zone']}",
                'expected_impact': "Reduces turnovers in dangerous areas",
            })
        
        # Suggest strategies from KG
        strategies = swot.get('suggested_strategies', [])
        for s in strategies:
            if s['strategy'] in ('press_high', 'press_triggers'):
                recs.append({
                    'priority': 'medium',
                    'category': 'Pressing Adjustment',
                    'description': s['description'],
                    'reasoning': f"Knowledge graph suggests '{s['strategy'].replace('_', ' ')}' for current situation",
                    'expected_impact': "Tactical adjustment based on opponent analysis",
                })
                break
        
        return recs
    
    def _recommend_attacking_strategy(self):
        """Generate attacking strategy recommendations."""
        recs = []
        swot = self.swot_results
        situations = swot.get('situations', [])
        strategies = swot.get('suggested_strategies', [])
        
        # Map KG strategies to recommendations
        attack_strategies = {
            'exploit_width': ('high', "Stretch the play wide to pull the opponent apart"),
            'switch_play': ('high', "Quickly switch play from one flank to the other to exploit open space"),
            'play_vertical': ('medium', "Play direct vertical passes to bypass midfield pressure"),
            'overload_halfspace': ('medium', "Overload the half-spaces with runners to create numerical advantage"),
            'invert_wingers': ('medium', "Wingers cut inside to create shooting opportunities"),
            'patient_buildup': ('low', "Slow, patient possession to gradually pull the opponent out of shape"),
            'quick_transitions': ('high', "Attack rapidly after winning the ball before opponent reorganises"),
            'use_long_balls': ('medium', "Use long balls to bypass the press and exploit space behind"),
        }
        
        added = set()
        for s in strategies:
            strat_name = s['strategy']
            if strat_name in attack_strategies and strat_name not in added:
                priority, impact = attack_strategies[strat_name]
                recs.append({
                    'priority': priority,
                    'category': 'Attacking Strategy',
                    'description': s['description'],
                    'reasoning': f"Counters detected situation: {', '.join(sit.replace('_', ' ') for sit in situations[:2])}",
                    'expected_impact': impact,
                })
                added.add(strat_name)
                if len(added) >= 3:
                    break
        
        # If we have strength in attack
        for s in swot.get('strengths', []):
            if 'overload' in s['description'].lower() or 'overlap' in s['description'].lower():
                recs.append({
                    'priority': 'medium',
                    'category': 'Attacking Strategy',
                    'description': f"Continue exploiting: {s['description']}",
                    'reasoning': "This is an identified strength — double down on what's working",
                    'expected_impact': "Maximises existing tactical advantage",
                })
                break
        
        return recs
    
    def _recommend_defensive_adjustments(self):
        """Generate defensive adjustment recommendations."""
        recs = []
        swot = self.swot_results
        
        for threat in swot.get('threats', []):
            desc = threat['description']
            
            if 'high line' in desc.lower() or 'counter' in desc.lower():
                recs.append({
                    'priority': 'high',
                    'category': 'Defensive Adjustment',
                    'description': "Drop the defensive line 5-10 yards to reduce space behind",
                    'reasoning': threat['description'],
                    'expected_impact': "Reduces vulnerability to through-balls and counter-attacks",
                })
            elif 'compact' in desc.lower() or 'low block' in desc.lower():
                recs.append({
                    'priority': 'medium',
                    'category': 'Defensive Adjustment',
                    'description': "Hold position and avoid being drawn out — maintain shape when attacking",
                    'reasoning': threat['description'],
                    'expected_impact': "Prevents counter-attack opportunities for the opponent",
                })
        
        # Opponent inverted winger threat
        for threat in swot.get('threats', []):
            if 'inverted winger' in threat['description'].lower():
                recs.append({
                    'priority': 'medium',
                    'category': 'Defensive Adjustment',
                    'description': threat['action'],
                    'reasoning': threat['description'],
                    'expected_impact': "Reduces opponent's cutting-inside threat",
                })
        
        return recs
    
    def _recommend_player_specific(self):
        """Generate player-specific tactical instructions."""
        recs = []
        roles_a = self.analysis_data.get('roles_a', [])
        roles_b = self.analysis_data.get('roles_b', [])
        patterns_a = self.analysis_data.get('patterns_a', [])
        
        # Fullback instructions based on patterns
        for p in patterns_a:
            if p.get('pattern') == 'Overlapping Run' and p.get('detected'):
                players = p.get('involved_players', [])
                if players:
                    recs.append({
                        'priority': 'medium',
                        'category': 'Player Instruction',
                        'description': f"{players[0]} should continue making overlapping runs to create 2v1 situations",
                        'reasoning': f"Overlap between {' and '.join(players)} is creating width effectively",
                        'expected_impact': "Continues generating chances from wide areas",
                    })
        
        # Key distributor protection
        ps = self.analysis_data.get('pass_summary', {})
        kp = ps.get('key_distributor', {})
        if kp.get('betweenness', 0) > 0.2:
            name = kp.get('name', 'Key player')
            recs.append({
                'priority': 'low',
                'category': 'Player Instruction',
                'description': f"{name} is critical for build-up — protect this player and provide passing options",
                'reasoning': f"High betweenness centrality ({kp['betweenness']:.2f}) means most attacks flow through {name}",
                'expected_impact': "Ensures build-up continuity if opponent targets this player",
            })
        
        # Weak link involvement
        weak_links = ps.get('weak_links', [])
        for wl in weak_links[:1]:
            recs.append({
                'priority': 'low',
                'category': 'Player Instruction',
                'description': f"Actively look for {wl['name']} — currently disconnected from the team",
                'reasoning': f"Only {wl['total_involvement']} pass involvements",
                'expected_impact': "Adds unpredictability by activating an underused player",
            })
        
        # Opponent danger men
        for r in roles_b:
            if r.get('role') in ('Inside Forward', 'Inverted Winger', 'Poacher', 'Shadow Striker'):
                recs.append({
                    'priority': 'medium',
                    'category': 'Player Instruction',
                    'description': f"Mark {r['name']} closely — operating as {r['role']}",
                    'reasoning': f"{r['name']} in the {r['role']} role is a key attacking threat",
                    'expected_impact': "Neutralises opponent's most dangerous attacker(s)",
                })
                break
        
        return recs
    
    # ── Visualization ───────────────────────────────────────────
    
    def draw(self, recommendations=None, figsize=(12, 8), title=None):
        """
        Draw top 5 recommendations as a clean panel.
        
        Returns:
            fig, ax
        """
        if recommendations is None:
            recommendations = self.recommend()
        
        top = recommendations[:6]
        
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        fig.patch.set_facecolor('#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        ax.axis('off')
        
        if title:
            fig.suptitle(title, color='white', fontsize=16,
                         fontweight='bold', y=0.98)
        
        priority_colors = {
            'high': '#e74c3c',
            'medium': '#f39c12',
            'low': '#3498db',
        }
        
        category_icons = {
            'Formation Change': '⚙',
            'Pressing Adjustment': '⬆',
            'Attacking Strategy': '⚡',
            'Defensive Adjustment': '🛡',
            'Player Instruction': '👤',
        }
        
        y = 0.88
        row_height = 0.14
        
        for i, rec in enumerate(top):
            priority = rec['priority']
            color = priority_colors.get(priority, '#888888')
            icon = category_icons.get(rec['category'], '•')
            
            # Priority badge
            badge_text = f"[{priority.upper()}]"
            ax.text(0.02, y, badge_text, transform=ax.transAxes,
                    fontsize=9, fontweight='bold', color=color, va='top',
                    fontfamily='monospace',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#2a2a3e',
                              edgecolor=color, linewidth=1.5))
            
            # Category
            ax.text(0.12, y, f"{rec['category']}", transform=ax.transAxes,
                    fontsize=9, fontweight='bold', color='white', va='top')
            
            # Description
            desc = rec['description']
            if len(desc) > 80:
                desc = desc[:77] + "..."
            ax.text(0.12, y - 0.035, desc, transform=ax.transAxes,
                    fontsize=8, color='#cccccc', va='top')
            
            # Impact
            impact = rec.get('expected_impact', '')
            if len(impact) > 85:
                impact = impact[:82] + "..."
            ax.text(0.12, y - 0.065, f"Impact: {impact}", transform=ax.transAxes,
                    fontsize=7, color='#888888', va='top', style='italic')
            
            # Divider line
            ax.plot([0.02, 0.98], [y - 0.09, y - 0.09],
                    color='#333333', linewidth=0.5, transform=ax.transAxes,
                    clip_on=False)
            
            y -= row_height
        
        # Count summary
        high = sum(1 for r in recommendations if r['priority'] == 'high')
        med = sum(1 for r in recommendations if r['priority'] == 'medium')
        low = sum(1 for r in recommendations if r['priority'] == 'low')
        
        summary = f"Total: {len(recommendations)} recommendations  |  HIGH: {high}  MEDIUM: {med}  LOW: {low}"
        ax.text(0.5, 0.02, summary, transform=ax.transAxes,
                ha='center', fontsize=9, color='white',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#2a2a3e',
                          edgecolor='#444444'))
        
        return fig, ax
    
    # ── Text output ─────────────────────────────────────────────
    
    def print_recommendations(self, recommendations=None):
        """Print formatted recommendations."""
        if recommendations is None:
            recommendations = self.recommend()
        
        print("\n" + "=" * 60)
        print("  STRATEGY RECOMMENDATIONS")
        print("=" * 60)
        print(f"\n  {self.team_name} vs {self.opponent_name}")
        print(f"  Total: {len(recommendations)} recommendations\n")
        
        for i, rec in enumerate(recommendations, 1):
            priority = rec['priority'].upper()
            badge = {'HIGH': '!!!', 'MEDIUM': ' !! ', 'LOW': '  ! '}
            print(f"  [{badge.get(priority, '?')}] [{priority:6s}] {rec['category']}")
            print(f"       {rec['description']}")
            print(f"       Reasoning: {rec['reasoning']}")
            print(f"       Impact: {rec['expected_impact']}")
            print()
        
        print("=" * 60)
    
    # ── Save ────────────────────────────────────────────────────
    
    def save(self, fig, filename):
        """Save figure to outputs folder."""
        fig.savefig(f"outputs/{filename}", dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved: outputs/{filename}")


# ═══════════════════════════════════════════════════════════════
# Quick test — Strategy recommendations from El Clásico analysis
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    
    import os, sys, random
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
    from engine.intelligence.tactical_reasoning import TacticalReasoner
    
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
    
    # Run analysis
    fd_b = FormationDetector(); fd_b.set_team(barca, "FC Barcelona", "#a50044")
    fd_m = FormationDetector(); fd_m.set_team(madrid, "Real Madrid", "#ffffff")
    pn = PassNetwork(); pn.add_players(barca); pn.add_passes(passes)
    sc = SpaceControl(); sc.set_teams(barca, madrid); sc.set_ball(60, 40)
    grid, stats = sc.compute_influence_control(); mid = sc.get_midfield_control(grid)
    rc_b = RoleClassifier(); rc_b.set_team(barca, "FC Barcelona", "#a50044")
    rc_m = RoleClassifier(); rc_m.set_team(madrid, "Real Madrid", "#ffffff")
    random.seed(42)
    events = []
    for _ in range(65):
        p = random.choice([x for x in barca if x['position']!='GK'])
        r = random.choice([x for x in barca if x['position']!='GK'])
        px = max(0,min(120,p['x']+random.gauss(0,3))); py = max(0,min(80,p['y']+random.gauss(0,3)))
        opp = np.array([[x['x'],x['y']] for x in madrid])
        d = np.linalg.norm(opp-np.array([px,py]),axis=1); n = np.sum(d<10)
        events.append({'passer':p['number'],'receiver':r['number'],'success':random.random()<(0.55 if n>=2 else 0.90),'x':px,'y':py,'end_x':r['x'],'end_y':r['y']})
    pr = PressResistance(); pr.set_teams(barca,madrid,"FC Barcelona","#a50044","Real Madrid"); pr.add_pass_events(events)
    ptd = PatternDetector(); ptd.set_teams(barca,madrid,"FC Barcelona","Real Madrid","#a50044","#ffffff")
    
    data = {
        'formation_a': fd_b.detect(), 'formation_b': fd_m.detect(),
        'space_control': {'team_a_control':stats['team_a_control'],'team_b_control':stats['team_b_control'],'zones':stats['zones'],'midfield':mid},
        'pass_summary': pn.get_summary(), 'press_resistance': pr.analyze(),
        'patterns_a': ptd.detect_all("a"), 'patterns_b': ptd.detect_all("b"),
        'roles_a': rc_b.classify_all(), 'roles_b': rc_m.classify_all(),
    }
    
    # Reasoning
    kg = TacticalKnowledgeGraph()
    reasoner = TacticalReasoner(knowledge_graph=kg)
    reasoner.set_analysis(data, "FC Barcelona", "Real Madrid")
    swot = reasoner.reason()
    
    # Recommendations
    sr = StrategyRecommender(knowledge_graph=kg)
    sr.set_reasoning(swot, data, "FC Barcelona", "Real Madrid")
    
    recs = sr.recommend()
    sr.print_recommendations(recs)
    
    fig, ax = sr.draw(recs, title="SpaceAI FC - Strategy Recommendations")
    sr.save(fig, "recommendations.png")
    
    plt.show()
    print("\nStrategy recommendations complete!")
