"""
SpaceAI FC - Football Knowledge Graph
========================================
Graph-based store of tactical knowledge that the reasoning engine queries.
Contains formations, situations, strategies, and weaknesses linked by
tactical relationships.
"""

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


class TacticalKnowledgeGraph:
    """
    A directed graph encoding football tactical knowledge.
    
    Node types:
        - Formation: "4-3-3", "4-2-3-1", etc.
        - Situation: "low_block", "high_press", etc.
        - Strategy: "exploit_width", "play_vertical", etc.
        - Weakness: "exposed_flanks", "midfield_gap", etc.
    
    Edge types:
        - Formation → weak_against → Situation
        - Formation → strong_in → Situation
        - Situation → countered_by → Strategy
        - Weakness → exploited_by → Strategy
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_knowledge_base()
    
    # ── Knowledge base construction ─────────────────────────────
    
    def _build_knowledge_base(self):
        """Build the complete tactical knowledge graph."""
        
        # ── Formation nodes ─────────────────────────────────────
        formations = [
            ("4-3-3", "Balanced attacking formation with wide forwards"),
            ("4-2-3-1", "Solid midfield base with creative freedom in the 10 role"),
            ("3-5-2", "Midfield-dominant formation relying on wing-backs"),
            ("4-4-2", "Traditional balanced formation with two strikers"),
            ("5-4-1", "Ultra-defensive formation prioritising solidity"),
            ("5-3-2", "Defensive with three centre-backs and wing-back width"),
            ("4-1-4-1", "Single pivot with four across midfield"),
            ("3-4-3", "Aggressive formation with width from wing-backs"),
        ]
        for name, desc in formations:
            self.graph.add_node(name, type="formation", description=desc)
        
        # ── Situation nodes ─────────────────────────────────────
        situations = [
            ("low_block", "Opponent sitting deep with compact defensive shape"),
            ("high_press", "Opponent pressing high up the pitch"),
            ("counter_attack", "Opposition attacking on the break after turnover"),
            ("possession_play", "Team holding sustained possession"),
            ("midfield_overload", "Numerical advantage in central midfield"),
            ("wide_play", "Attacking primarily through wide areas"),
            ("park_the_bus", "Extreme defensive posture with all players behind ball"),
            ("high_line", "Defensive line pushed very high up the pitch"),
            ("transition_moment", "Ball just changed possession, both teams repositioning"),
            ("set_piece_threat", "Dangerous free kick or corner situation"),
        ]
        for name, desc in situations:
            self.graph.add_node(name, type="situation", description=desc)
        
        # ── Strategy nodes ──────────────────────────────────────
        strategies = [
            ("exploit_width", "Stretch the play wide to create space centrally"),
            ("play_vertical", "Direct vertical passes to bypass midfield lines"),
            ("switch_play", "Quickly move the ball from one flank to the other"),
            ("overload_halfspace", "Concentrate players in the half-space to create overloads"),
            ("target_fullback", "Direct attacks towards the weaker fullback"),
            ("press_high", "Push the pressing line high to win ball in opponent's half"),
            ("drop_deep", "Withdraw into a compact low block to absorb pressure"),
            ("use_long_balls", "Bypass the press with long balls over the top"),
            ("quick_transitions", "Attack rapidly after winning possession"),
            ("patient_buildup", "Slow, methodical possession to pull opponents out of shape"),
            ("exploit_channels", "Run into spaces between fullback and centre-back"),
            ("invert_wingers", "Wingers cut inside to create shooting angles"),
            ("overlap_fullbacks", "Fullbacks overlap wingers to provide width"),
            ("press_triggers", "Press only when opponent plays to specific players or zones"),
            ("sit_and_counter", "Absorb pressure then hit quickly on the break"),
        ]
        for name, desc in strategies:
            self.graph.add_node(name, type="strategy", description=desc)
        
        # ── Weakness nodes ──────────────────────────────────────
        weaknesses = [
            ("exposed_flanks", "Wide areas left unprotected, vulnerable to switches"),
            ("slow_defenders", "Centre-backs lack pace, vulnerable to balls behind"),
            ("weak_press_resistance", "Team struggles to play through opponent's press"),
            ("isolated_striker", "Lone striker receives no support, easily marked"),
            ("midfield_gap", "Space between midfield and defence is too large"),
            ("high_line_vulnerable", "High line exposed to long balls over the top"),
            ("single_buildup_route", "Build-up play is predictable, goes through one player"),
            ("weak_wide_defence", "Fullbacks caught out of position leaving space behind"),
        ]
        for name, desc in weaknesses:
            self.graph.add_node(name, type="weakness", description=desc)
        
        # ── Edges: Formation → weak_against → Situation ─────────
        weak_against = [
            ("4-3-3", "low_block"),
            ("4-3-3", "park_the_bus"),
            ("4-2-3-1", "high_press"),
            ("4-4-2", "midfield_overload"),
            ("3-5-2", "wide_play"),
            ("5-4-1", "possession_play"),
            ("4-1-4-1", "wide_play"),
            ("3-4-3", "counter_attack"),
        ]
        for f, s in weak_against:
            self.graph.add_edge(f, s, relation="weak_against")
        
        # ── Edges: Formation → strong_in → Situation ────────────
        strong_in = [
            ("4-3-3", "wide_play"),
            ("4-3-3", "high_press"),
            ("4-2-3-1", "possession_play"),
            ("4-2-3-1", "midfield_overload"),
            ("3-5-2", "midfield_overload"),
            ("3-5-2", "possession_play"),
            ("4-4-2", "counter_attack"),
            ("4-4-2", "high_press"),
            ("5-4-1", "low_block"),
            ("5-4-1", "counter_attack"),
            ("5-3-2", "low_block"),
            ("3-4-3", "high_press"),
            ("3-4-3", "wide_play"),
            ("4-1-4-1", "midfield_overload"),
        ]
        for f, s in strong_in:
            self.graph.add_edge(f, s, relation="strong_in")
        
        # ── Edges: Situation → countered_by → Strategy ──────────
        countered_by = [
            ("low_block", "exploit_width"),
            ("low_block", "switch_play"),
            ("low_block", "overload_halfspace"),
            ("low_block", "patient_buildup"),
            ("high_press", "use_long_balls"),
            ("high_press", "quick_transitions"),
            ("high_press", "play_vertical"),
            ("counter_attack", "drop_deep"),
            ("counter_attack", "press_high"),
            ("possession_play", "press_high"),
            ("possession_play", "press_triggers"),
            ("midfield_overload", "switch_play"),
            ("midfield_overload", "exploit_width"),
            ("wide_play", "drop_deep"),
            ("wide_play", "overload_halfspace"),
            ("park_the_bus", "exploit_width"),
            ("park_the_bus", "switch_play"),
            ("park_the_bus", "invert_wingers"),
            ("high_line", "use_long_balls"),
            ("high_line", "exploit_channels"),
            ("high_line", "quick_transitions"),
            ("transition_moment", "quick_transitions"),
            ("transition_moment", "press_high"),
        ]
        for s, st in countered_by:
            self.graph.add_edge(s, st, relation="countered_by")
        
        # ── Edges: Weakness → exploited_by → Strategy ───────────
        exploited_by = [
            ("exposed_flanks", "switch_play"),
            ("exposed_flanks", "exploit_width"),
            ("exposed_flanks", "overlap_fullbacks"),
            ("slow_defenders", "use_long_balls"),
            ("slow_defenders", "exploit_channels"),
            ("slow_defenders", "quick_transitions"),
            ("weak_press_resistance", "press_high"),
            ("weak_press_resistance", "press_triggers"),
            ("isolated_striker", "drop_deep"),
            ("isolated_striker", "overload_halfspace"),
            ("midfield_gap", "play_vertical"),
            ("midfield_gap", "exploit_channels"),
            ("high_line_vulnerable", "use_long_balls"),
            ("high_line_vulnerable", "exploit_channels"),
            ("single_buildup_route", "press_triggers"),
            ("single_buildup_route", "press_high"),
            ("weak_wide_defence", "exploit_width"),
            ("weak_wide_defence", "overlap_fullbacks"),
        ]
        for w, st in exploited_by:
            self.graph.add_edge(w, st, relation="exploited_by")
    
    # ── Query methods ───────────────────────────────────────────
    
    def get_counter_strategies(self, situation):
        """Get strategies that counter a given situation."""
        strategies = []
        if situation not in self.graph:
            return strategies
        for _, target, data in self.graph.out_edges(situation, data=True):
            if data.get('relation') == 'countered_by':
                desc = self.graph.nodes[target].get('description', '')
                strategies.append({'strategy': target, 'description': desc})
        return strategies
    
    def get_formation_weaknesses(self, formation):
        """Get situations where a formation is weak."""
        weaknesses = []
        if formation not in self.graph:
            return weaknesses
        for _, target, data in self.graph.out_edges(formation, data=True):
            if data.get('relation') == 'weak_against':
                desc = self.graph.nodes[target].get('description', '')
                weaknesses.append({'situation': target, 'description': desc})
        return weaknesses
    
    def get_formation_strengths(self, formation):
        """Get situations where a formation excels."""
        strengths = []
        if formation not in self.graph:
            return strengths
        for _, target, data in self.graph.out_edges(formation, data=True):
            if data.get('relation') == 'strong_in':
                desc = self.graph.nodes[target].get('description', '')
                strengths.append({'situation': target, 'description': desc})
        return strengths
    
    def get_exploitation_strategies(self, weakness):
        """Get strategies that exploit a given weakness."""
        strategies = []
        if weakness not in self.graph:
            return strategies
        for _, target, data in self.graph.out_edges(weakness, data=True):
            if data.get('relation') == 'exploited_by':
                desc = self.graph.nodes[target].get('description', '')
                strategies.append({'strategy': target, 'description': desc})
        return strategies
    
    def query(self, formation, situation):
        """
        Query the knowledge graph for insights about a formation facing a situation.
        
        Returns:
            dict with 'formation_weaknesses', 'formation_strengths',
                  'counter_strategies', 'is_weak_against', 'is_strong_in'
        """
        weaknesses = self.get_formation_weaknesses(formation)
        strengths = self.get_formation_strengths(formation)
        counters = self.get_counter_strategies(situation)
        
        weak_situations = [w['situation'] for w in weaknesses]
        strong_situations = [s['situation'] for s in strengths]
        
        return {
            'formation': formation,
            'situation': situation,
            'formation_weaknesses': weaknesses,
            'formation_strengths': strengths,
            'counter_strategies': counters,
            'is_weak_against': situation in weak_situations,
            'is_strong_in': situation in strong_situations,
        }
    
    def get_all_nodes(self, node_type=None):
        """Get all nodes, optionally filtered by type."""
        nodes = []
        for node, data in self.graph.nodes(data=True):
            if node_type is None or data.get('type') == node_type:
                nodes.append({'name': node, **data})
        return nodes
    
    def get_stats(self):
        """Get graph statistics."""
        types = {}
        for _, data in self.graph.nodes(data=True):
            t = data.get('type', 'unknown')
            types[t] = types.get(t, 0) + 1
        
        relations = {}
        for _, _, data in self.graph.edges(data=True):
            r = data.get('relation', 'unknown')
            relations[r] = relations.get(r, 0) + 1
        
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': types,
            'relation_types': relations,
        }
    
    # ── Visualization ───────────────────────────────────────────
    
    def draw(self, figsize=(16, 10), title=None):
        """
        Draw the knowledge graph with color-coded node types.
        
        Returns:
            fig, ax
        """
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        fig.patch.set_facecolor('#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        
        if title:
            fig.suptitle(title, color='white', fontsize=16,
                         fontweight='bold', y=0.98)
        
        # Node colors by type
        type_colors = {
            'formation': '#e74c3c',
            'situation': '#3498db',
            'strategy': '#2ecc71',
            'weakness': '#f39c12',
        }
        
        node_colors = []
        node_sizes = []
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('type', 'unknown')
            node_colors.append(type_colors.get(node_type, '#888888'))
            if node_type == 'formation':
                node_sizes.append(800)
            elif node_type == 'strategy':
                node_sizes.append(500)
            else:
                node_sizes.append(600)
        
        # Edge colors by relation
        edge_colors = []
        edge_styles = []
        for _, _, data in self.graph.edges(data=True):
            rel = data.get('relation', '')
            if rel == 'weak_against':
                edge_colors.append('#e74c3c')
            elif rel == 'strong_in':
                edge_colors.append('#2ecc71')
            elif rel == 'countered_by':
                edge_colors.append('#3498db')
            elif rel == 'exploited_by':
                edge_colors.append('#f39c12')
            else:
                edge_colors.append('#888888')
        
        # Layout
        pos = nx.spring_layout(self.graph, k=2.5, iterations=60, seed=42)
        
        # Draw edges
        nx.draw_networkx_edges(
            self.graph, pos, ax=ax,
            edge_color=edge_colors, alpha=0.4,
            arrows=True, arrowsize=12, arrowstyle='-|>',
            connectionstyle='arc3,rad=0.1', width=1.2
        )
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph, pos, ax=ax,
            node_color=node_colors, node_size=node_sizes,
            edgecolors='white', linewidths=1.2, alpha=0.9
        )
        
        # Labels
        labels = {}
        for node in self.graph.nodes():
            label = node.replace('_', '\n')
            labels[node] = label
        
        nx.draw_networkx_labels(
            self.graph, pos, labels, ax=ax,
            font_size=6, font_weight='bold', font_color='white'
        )
        
        # Legend
        legend_elements = [
            mpatches.Patch(facecolor=type_colors['formation'], label='Formation',
                           edgecolor='white', linewidth=0.5),
            mpatches.Patch(facecolor=type_colors['situation'], label='Situation',
                           edgecolor='white', linewidth=0.5),
            mpatches.Patch(facecolor=type_colors['strategy'], label='Strategy',
                           edgecolor='white', linewidth=0.5),
            mpatches.Patch(facecolor=type_colors['weakness'], label='Weakness',
                           edgecolor='white', linewidth=0.5),
        ]
        ax.legend(handles=legend_elements, loc='lower left',
                  fontsize=9, facecolor='#2a2a3e', edgecolor='#444444',
                  labelcolor='white', framealpha=0.9)
        
        ax.axis('off')
        
        return fig, ax
    
    # ── Text output ─────────────────────────────────────────────
    
    def print_knowledge_base(self):
        """Print the full knowledge base contents."""
        stats = self.get_stats()
        
        print("\n" + "=" * 60)
        print("  TACTICAL KNOWLEDGE GRAPH")
        print("=" * 60)
        
        print(f"\n  Nodes: {stats['total_nodes']}  |  Edges: {stats['total_edges']}")
        print(f"  Node types: {stats['node_types']}")
        print(f"  Relation types: {stats['relation_types']}")
        
        for ntype in ['formation', 'situation', 'strategy', 'weakness']:
            nodes = self.get_all_nodes(ntype)
            print(f"\n  --- {ntype.upper()}S ({len(nodes)}) ---")
            for n in nodes:
                print(f"    {n['name']}: {n.get('description', '')}")
        
        print(f"\n  --- RELATIONSHIPS ({stats['total_edges']}) ---")
        for src, tgt, data in self.graph.edges(data=True):
            rel = data.get('relation', '?')
            print(f"    {src} --[{rel}]--> {tgt}")
        
        print("\n" + "=" * 60)
    
    # ── Save ────────────────────────────────────────────────────
    
    def save(self, fig, filename):
        """Save figure to outputs folder."""
        fig.savefig(f"outputs/{filename}", dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved: outputs/{filename}")


# ═══════════════════════════════════════════════════════════════
# Quick test — Knowledge graph demo
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    
    import os
    os.makedirs("outputs", exist_ok=True)
    
    kg = TacticalKnowledgeGraph()
    
    # Print full knowledge base
    kg.print_knowledge_base()
    
    # Query examples
    print("\n" + "=" * 60)
    print("  QUERY EXAMPLES")
    print("=" * 60)
    
    # What counters a low block?
    counters = kg.get_counter_strategies("low_block")
    print(f"\n  Strategies to counter 'low_block':")
    for c in counters:
        print(f"    -> {c['strategy']}: {c['description']}")
    
    # 4-2-3-1 weaknesses
    weaknesses = kg.get_formation_weaknesses("4-2-3-1")
    print(f"\n  Weaknesses of 4-2-3-1:")
    for w in weaknesses:
        print(f"    -> {w['situation']}: {w['description']}")
    
    # 4-2-3-1 strengths
    strengths = kg.get_formation_strengths("4-2-3-1")
    print(f"\n  Strengths of 4-2-3-1:")
    for s in strengths:
        print(f"    -> {s['situation']}: {s['description']}")
    
    # Full query
    result = kg.query("4-2-3-1", "low_block")
    print(f"\n  Query: 4-2-3-1 facing low_block:")
    print(f"    Weak against this situation: {result['is_weak_against']}")
    print(f"    Strong in this situation: {result['is_strong_in']}")
    print(f"    Counter strategies: {[c['strategy'] for c in result['counter_strategies']]}")
    
    # Exploit a weakness
    exploits = kg.get_exploitation_strategies("exposed_flanks")
    print(f"\n  How to exploit 'exposed_flanks':")
    for e in exploits:
        print(f"    -> {e['strategy']}: {e['description']}")
    
    print("\n" + "=" * 60)
    
    # Visualize
    fig, ax = kg.draw(title="SpaceAI FC - Tactical Knowledge Graph")
    kg.save(fig, "knowledge_graph.png")
    
    plt.show()
    print("\nKnowledge graph complete!")
