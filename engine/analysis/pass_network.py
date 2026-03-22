"""
SpaceAI FC - Pass Network Analysis
===================================
Builds passing graphs between players, calculates node importance,
edge weights, and identifies key distributors.
Includes both network overview and pass sequence visualization.
"""

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mplsoccer import Pitch


class PassNetwork:
    """
    Analyzes passing connections between players.
    
    Builds a directed graph where:
        - Nodes = players
        - Edges = passes between players
        - Edge weight = number of passes
    
    Two visualization modes:
        - draw(): overall network (who connects to whom)
        - draw_sequence(): step-by-step pass sequence (how the ball moved)
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.pass_data = []
        self.players = {}
    
    # Data input
    
    def add_players(self, players):
        """
        Register players with their positions.
        
        Parameters:
            players: list of dicts with keys:
                'name', 'number', 'x', 'y', 'position'
        """
        for player in players:
            player_id = player['number']
            self.players[player_id] = player
            self.graph.add_node(player_id, **player)
    
    def add_pass(self, passer_number, receiver_number, success=True):
        """
        Add a single pass event.
        
        Parameters:
            passer_number: shirt number of passer
            receiver_number: shirt number of receiver
            success: whether the pass was completed
        """
        self.pass_data.append({
            'passer': passer_number,
            'receiver': receiver_number,
            'success': success
        })
        
        if success:
            if self.graph.has_edge(passer_number, receiver_number):
                self.graph[passer_number][receiver_number]['weight'] += 1
            else:
                self.graph.add_edge(passer_number, receiver_number, weight=1)
    
    def add_passes(self, passes):
        """
        Add multiple pass events at once.
        
        Parameters:
            passes: list of tuples (passer_number, receiver_number, success)
                    or list of tuples (passer_number, receiver_number) — assumes success
        """
        for p in passes:
            if len(p) == 3:
                self.add_pass(p[0], p[1], p[2])
            else:
                self.add_pass(p[0], p[1], True)
    
    # Analysis
    
    def get_total_passes(self):
        """Total number of successful passes."""
        return sum(d['weight'] for _, _, d in self.graph.edges(data=True))
    
    def get_pass_counts(self):
        """Get passes made and received per player."""
        counts = {}
        for player_id in self.players:
            made = sum(d['weight'] for _, _, d in self.graph.out_edges(player_id, data=True))
            received = sum(d['weight'] for _, _, d in self.graph.in_edges(player_id, data=True))
            counts[player_id] = {
                'name': self.players[player_id]['name'],
                'number': player_id,
                'passes_made': made,
                'passes_received': received,
                'total_involvement': made + received
            }
        return counts
    
    def get_top_connections(self, n=5):
        """Get the strongest passing connections."""
        edges = [(u, v, d['weight']) for u, v, d in self.graph.edges(data=True)]
        edges.sort(key=lambda x: x[2], reverse=True)
        
        top = []
        for passer, receiver, count in edges[:n]:
            top.append({
                'from': self.players[passer]['name'],
                'from_number': passer,
                'to': self.players[receiver]['name'],
                'to_number': receiver,
                'passes': count
            })
        return top
    
    def get_centrality(self):
        """
        Calculate centrality metrics for each player.
        
        Returns dict per player with:
            - degree_centrality: how connected they are
            - betweenness_centrality: how much they bridge connections
            - eigenvector_centrality: influence based on connection quality
        """
        undirected = self.graph.to_undirected()
        
        degree = nx.degree_centrality(undirected)
        betweenness = nx.betweenness_centrality(undirected, weight='weight')
        
        try:
            eigenvector = nx.eigenvector_centrality(undirected, weight='weight', max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            eigenvector = {n: 0.0 for n in self.graph.nodes()}
        
        centrality = {}
        for player_id in self.players:
            centrality[player_id] = {
                'name': self.players[player_id]['name'],
                'number': player_id,
                'degree': round(degree.get(player_id, 0), 3),
                'betweenness': round(betweenness.get(player_id, 0), 3),
                'eigenvector': round(eigenvector.get(player_id, 0), 3),
            }
        return centrality
    
    def get_key_distributor(self):
        """Find the most influential passer based on betweenness centrality."""
        centrality = self.get_centrality()
        key_player = max(centrality.values(), key=lambda x: x['betweenness'])
        return key_player
    
    def get_weak_links(self, threshold=3):
        """Find players with very low pass involvement (excluding GK)."""
        weak = []
        counts = self.get_pass_counts()
        for player_id, data in counts.items():
            if data['total_involvement'] <= threshold and self.players[player_id]['position'] != 'GK':
                weak.append({
                    'name': data['name'],
                    'number': player_id,
                    'total_involvement': data['total_involvement']
                })
        return weak
    
    def get_summary(self):
        """Generate a complete pass network summary."""
        key_player = self.get_key_distributor()
        top_connections = self.get_top_connections(5)
        weak_links = self.get_weak_links()
        counts = self.get_pass_counts()
        
        most_involved = max(counts.values(), key=lambda x: x['total_involvement'])
        
        summary = {
            'total_passes': self.get_total_passes(),
            'key_distributor': key_player,
            'most_involved': most_involved,
            'top_connections': top_connections,
            'weak_links': weak_links,
        }
        return summary
    
    # Visualization 1: Pass Network (clean version)
    
    def draw(self, figsize=(12, 8), title=None, team_color="#e74c3c",
             team_name="Team", min_passes=2):
        """
        Draw the pass network on a football pitch.
        
        Only shows connections with min_passes or more.
        Uses curved lines to avoid overlap.
        Node size = total pass involvement.
        
        Parameters:
            min_passes: minimum passes between two players to show the connection
        """
        pitch = Pitch(
            pitch_type='statsbomb',
            pitch_color='#1a1a2e',
            line_color='#e0e0e0',
            linewidth=1.5,
            goal_type='box'
        )
        fig, ax = pitch.draw(figsize=figsize)
        fig.patch.set_facecolor('#1a1a2e')
        
        if title:
            fig.suptitle(title, color='white', fontsize=16, fontweight='bold', y=0.98)
        
        counts = self.get_pass_counts()
        
        # Filter edges by minimum passes
        strong_edges = [(u, v, d) for u, v, d in self.graph.edges(data=True) 
                        if d['weight'] >= min_passes]
        
        if not strong_edges:
            strong_edges = [(u, v, d) for u, v, d in self.graph.edges(data=True)]
        
        max_weight = max((d['weight'] for _, _, d in strong_edges), default=1)
        max_involvement = max((c['total_involvement'] for c in counts.values()), default=1)
        
        # Draw edges as curved arrows
        for passer, receiver, data in strong_edges:
            if passer in self.players and receiver in self.players:
                x1 = self.players[passer]['x']
                y1 = self.players[passer]['y']
                x2 = self.players[receiver]['x']
                y2 = self.players[receiver]['y']
                
                weight = data['weight']
                line_width = 1 + (weight / max_weight) * 5
                alpha = 0.3 + (weight / max_weight) * 0.6
                
                # Curved arrow
                ax.annotate("",
                    xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=team_color,
                        lw=line_width,
                        alpha=alpha,
                        connectionstyle="arc3,rad=0.15",
                        mutation_scale=15,
                    ),
                    zorder=3
                )
                
                # Pass count label at midpoint
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                # Offset the label slightly so it doesn't sit on the line
                offset_x = -(y2 - y1) * 0.04
                offset_y = (x2 - x1) * 0.04
                
                if weight >= min_passes + 1:
                    ax.annotate(str(weight),
                        xy=(mid_x + offset_x, mid_y + offset_y),
                        ha='center', va='center',
                        fontsize=7, fontweight='bold',
                        color='white', alpha=0.7, zorder=4,
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='#333333',
                                  edgecolor='none', alpha=0.6))
        
        # Draw nodes
        for player_id, player in self.players.items():
            x = player['x']
            y = player['y']
            
            involvement = counts[player_id]['total_involvement']
            node_size = 250 + (involvement / max_involvement) * 550
            
            ax.scatter(x, y, c=team_color, s=node_size, edgecolors='white',
                       linewidths=2, zorder=6, alpha=0.95)
            
            ax.annotate(str(player['number']), xy=(x, y),
                       ha='center', va='center', fontsize=8,
                       fontweight='bold', color='white', zorder=7)
            
            ax.annotate(player['name'], xy=(x, y + 3),
                       ha='center', va='bottom', fontsize=7,
                       color='white', zorder=7, alpha=0.85)
        
        # Legend
        ax.scatter([], [], c=team_color, s=100, edgecolors='white',
                   linewidths=1.5, label=team_name, zorder=5)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.02),
                  ncol=1, fontsize=10, facecolor='#1a1a2e',
                  edgecolor='#444444', labelcolor='white')
        
        return fig, ax
    
    # Visualization 2: Pass Sequence
    
    def draw_sequence(self, sequence, figsize=(12, 8), title=None,
                      team_color="#e74c3c", team_name="Team"):
        """
        Draw a specific pass sequence showing ball movement step by step.
        
        Parameters:
            sequence: list of player numbers in pass order
                      e.g. [4, 8, 6, 19, 9] means:
                      Araújo → Pedri → Gavi → Lamine → Lewandowski
        """
        pitch = Pitch(
            pitch_type='statsbomb',
            pitch_color='#1a1a2e',
            line_color='#e0e0e0',
            linewidth=1.5,
            goal_type='box'
        )
        fig, ax = pitch.draw(figsize=figsize)
        fig.patch.set_facecolor('#1a1a2e')
        
        if title:
            fig.suptitle(title, color='white', fontsize=16, fontweight='bold', y=0.98)
        
        # Color gradient from start to end of sequence
        n_passes = len(sequence) - 1
        cmap = plt.cm.plasma
        colors = [cmap(i / max(n_passes - 1, 1)) for i in range(n_passes)]
        
        # Draw all players faded in background
        for player_id, player in self.players.items():
            x = player['x']
            y = player['y']
            
            if player_id in sequence:
                # Players in the sequence get highlighted later
                continue
            
            ax.scatter(x, y, c='#444444', s=200, edgecolors='#666666',
                       linewidths=1.5, zorder=4, alpha=0.4)
            ax.annotate(str(player['number']), xy=(x, y),
                       ha='center', va='center', fontsize=7,
                       color='#888888', zorder=5)
        
        # Draw the pass arrows with step numbers
        for i in range(n_passes):
            passer = sequence[i]
            receiver = sequence[i + 1]
            
            if passer not in self.players or receiver not in self.players:
                continue
            
            x1 = self.players[passer]['x']
            y1 = self.players[passer]['y']
            x2 = self.players[receiver]['x']
            y2 = self.players[receiver]['y']
            
            arrow_color = colors[i]
            
            # Draw arrow
            ax.annotate("",
                xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=arrow_color,
                    lw=3,
                    alpha=0.9,
                    connectionstyle="arc3,rad=0.1",
                    mutation_scale=20,
                ),
                zorder=5
            )
            
            # Step number at midpoint
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            offset_x = -(y2 - y1) * 0.06
            offset_y = (x2 - x1) * 0.06
            
            ax.annotate(str(i + 1),
                xy=(mid_x + offset_x, mid_y + offset_y),
                ha='center', va='center',
                fontsize=9, fontweight='bold',
                color='white', zorder=8,
                bbox=dict(boxstyle='circle,pad=0.3',
                          facecolor=arrow_color, edgecolor='white',
                          linewidth=1.5, alpha=0.9))
        
        # Draw players in the sequence (highlighted)
        for i, player_id in enumerate(sequence):
            if player_id not in self.players:
                continue
            
            player = self.players[player_id]
            x = player['x']
            y = player['y']
            
            # First player gets a special start marker
            if i == 0:
                edge_color = '#2ecc71'  # green = start
            elif i == len(sequence) - 1:
                edge_color = '#f1c40f'  # yellow = end
            else:
                edge_color = 'white'
            
            ax.scatter(x, y, c=team_color, s=400, edgecolors=edge_color,
                       linewidths=3, zorder=9, alpha=0.95)
            
            ax.annotate(str(player['number']), xy=(x, y),
                       ha='center', va='center', fontsize=9,
                       fontweight='bold', color='white', zorder=10)
            
            ax.annotate(player['name'], xy=(x, y + 3.5),
                       ha='center', va='bottom', fontsize=8,
                       fontweight='bold', color='white', zorder=10)
        
        # Legend
        legend_elements = [
            plt.scatter([], [], c=team_color, s=100, edgecolors='#2ecc71',
                       linewidths=2, label='Start'),
            plt.scatter([], [], c=team_color, s=100, edgecolors='#f1c40f',
                       linewidths=2, label='End'),
        ]
        ax.legend(handles=legend_elements, loc='upper center',
                  bbox_to_anchor=(0.5, -0.02), ncol=2, fontsize=10,
                  facecolor='#1a1a2e', edgecolor='#444444', labelcolor='white')
        
        return fig, ax
    
    # Text output
    
    def print_summary(self):
        """Print a formatted text summary of the pass network."""
        summary = self.get_summary()
        
        print("\n" + "=" * 55)
        print("  PASS NETWORK ANALYSIS")
        print("=" * 55)
        
        print(f"\n  Total Passes: {summary['total_passes']}")
        
        kp = summary['key_distributor']
        print(f"\n  Key Distributor: {kp['name']} (#{kp['number']})")
        print(f"    Betweenness: {kp['betweenness']}")
        
        mi = summary['most_involved']
        print(f"\n  Most Involved: {mi['name']} (#{mi['number']})")
        print(f"    Passes Made: {mi['passes_made']}")
        print(f"    Passes Received: {mi['passes_received']}")
        
        print(f"\n  Top Connections:")
        for conn in summary['top_connections']:
            print(f"    {conn['from']} -> {conn['to']}: {conn['passes']} passes")
        
        if summary['weak_links']:
            print(f"\n  Weak Links (low involvement):")
            for wl in summary['weak_links']:
                print(f"    {wl['name']} (#{wl['number']}): {wl['total_involvement']} total passes")
        else:
            print(f"\n  No weak links detected.")
        
        print("\n" + "=" * 55)

# Quick test - Barcelona pass network + sequence

if __name__ == "__main__":
    
    # Create pass network
    pn = PassNetwork()
    
    # Barcelona 4-2-3-1 players
    players = [
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
    
    pn.add_players(players)
    
    # Simulated pass data
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
    
    # Print analysis
    pn.print_summary()
    
    # VISUALIZATION 1: Clean pass network
    fig1, ax1 = pn.draw(
        title="SpaceAI FC - Barcelona Pass Network",
        team_color="#a50044",
        team_name="FC Barcelona",
        min_passes=2
    )
    fig1.savefig("outputs/barca_pass_network.png", dpi=150, bbox_inches='tight',
                 facecolor=fig1.get_facecolor())
    print("\nSaved: outputs/barca_pass_network.png")
    
    # VISUALIZATION 2: Pass sequence
    # Example: Build-up play from the back to a goal chance
    # Cubarsí → Araújo → Pedri → Gavi → Lamine → Lewandowski
    sequence = [2, 4, 8, 6, 19, 9]
    
    fig2, ax2 = pn.draw_sequence(
        sequence,
        title="SpaceAI FC - Build-Up Sequence: Goal Chance",
        team_color="#a50044",
        team_name="FC Barcelona"
    )
    fig2.savefig("outputs/barca_pass_sequence.png", dpi=150, bbox_inches='tight',
                 facecolor=fig2.get_facecolor())
    print("Saved: outputs/barca_pass_sequence.png")
    
    plt.show()
    print("\nPass network analysis complete!")