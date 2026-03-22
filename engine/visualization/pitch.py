"""
SpaceAI FC the Pitch Model
Foundation module for all football visualizations.
Draws a standard football pitch and plots players on it.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from mplsoccer import Pitch


class FootballPitch:
    """
    2D football pitch model.
    Supports both custom matplotlib drawing and mplsoccer integration.
    
    Coordinate system: 
        x: 0 to 120 (length, left to right)
        y: 0 to 80 (width, bottom to top)
    """
    
    def __init__(self, length=120, width=80):
        self.length = length
        self.width = width
    
        # Core pitch drawing
    
    def draw(self, figsize=(12, 8), title=None):
        """
        Draw a football pitch using mplsoccer.
        Returns fig and ax for adding more elements on top.
        """
        pitch = Pitch(
            pitch_type='statsbomb',
            pitch_color='#1a1a2e',
            line_color='#e0e0e0',
            linewidth=1.5,
            goal_type='box'
        )
        fig, ax = pitch.draw(figsize=figsize)
        
        if title:
            fig.suptitle(title, color='white', fontsize=16, fontweight='bold', y=0.98)
        
        fig.patch.set_facecolor('#1a1a2e')
        
        return fig, ax, pitch
    
    # Player plotting
    
    def plot_players(self, ax, pitch, team_a_positions, team_b_positions,
                     team_a_name="Team A", team_b_name="Team B",
                     team_a_color="#e74c3c", team_b_color="#3498db",
                     show_names=True, show_numbers=True):
        """
        Plot players from both teams on the pitch.
        
        Parameters:
            ax: matplotlib axes from draw()
            pitch: mplsoccer Pitch object from draw()
            team_a_positions: list of dicts with keys: 
                'name', 'number', 'x', 'y', 'position'
            team_b_positions: same format as team_a
            team_a_name: display name for team A
            team_b_name: display name for team B
            team_a_color: color for team A markers
            team_b_color: color for team B markers
            show_names: whether to show player names
            show_numbers: whether to show shirt numbers
        """
        # Plot team A
        self._plot_team(ax, team_a_positions, team_a_color, show_names, show_numbers)
        
        # Plot team B
        self._plot_team(ax, team_b_positions, team_b_color, show_names, show_numbers)
        
        # Add legend
        ax.scatter([], [], c=team_a_color, s=100, edgecolors='white', 
                   linewidths=1.5, label=team_a_name, zorder=5)
        ax.scatter([], [], c=team_b_color, s=100, edgecolors='white', 
                   linewidths=1.5, label=team_b_name, zorder=5)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.02), 
                  ncol=2, fontsize=10, facecolor='#1a1a2e', 
                  edgecolor='#444444', labelcolor='white')
    
    def _plot_team(self, ax, players, color, show_names, show_numbers):
        """Plot a single team's players."""
        for player in players:
            x = player['x']
            y = player['y']
            
            # Player dot
            ax.scatter(x, y, c=color, s=300, edgecolors='white', 
                       linewidths=2, zorder=6, alpha=0.95)
            
            # Shirt number inside the dot
            if show_numbers and 'number' in player:
                ax.annotate(str(player['number']), xy=(x, y),
                           ha='center', va='center', fontsize=8,
                           fontweight='bold', color='white', zorder=7)
            
            # Player name above the dot
            if show_names and 'name' in player:
                ax.annotate(player['name'], xy=(x, y + 3),
                           ha='center', va='bottom', fontsize=7,
                           color='white', zorder=7, alpha=0.85)
    
    # Ball plotting
    
    def plot_ball(self, ax, x, y):
        """Plot the ball position on the pitch."""
        ax.scatter(x, y, c='#f1c40f', s=120, edgecolors='white',
                   linewidths=2, zorder=8, marker='o')
    
    # Save output
    
    def save(self, fig, filename, dpi=150):
        """Save the figure to the outputs folder."""
        fig.savefig(f"outputs/{filename}", dpi=dpi, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved: outputs/{filename}")


# Quick test  run this file directly to see it work

if __name__ == "__main__":
    
    # Create pitch
    fp = FootballPitch()
    fig, ax, pitch = fp.draw(title="SpaceAI FC - Pitch Model Test")
    
    # Barcelona 4-2-3-1
    team_a = [
        {'name': 'Garcia',      'number': 13,  'x': 5,  'y': 40, 'position': 'GK'},
        {'name': 'Koundé',      'number': 23, 'x': 30, 'y': 70, 'position': 'RB'},
        {'name': 'Araújo',      'number': 4,  'x': 25, 'y': 52, 'position': 'CB'},
        {'name': 'Cubarsí',     'number': 2,  'x': 25, 'y': 28, 'position': 'CB'},
        {'name': 'Baldé',       'number': 3,  'x': 30, 'y': 10, 'position': 'LB'},
        {'name': 'Pedri',       'number': 8,  'x': 45, 'y': 48, 'position': 'CM'},
        {'name': 'De Jong',     'number': 21, 'x': 45, 'y': 32, 'position': 'CM'},
        {'name': 'Lamine',      'number': 19, 'x': 65, 'y': 68, 'position': 'RW'},
        {'name': 'Fermin',      'number': 16,  'x': 70, 'y': 40, 'position': 'CAM'},
        {'name': 'Raphinha',    'number': 11, 'x': 65, 'y': 12, 'position': 'LW'},
        {'name': 'Lewandowski', 'number': 9,  'x': 80, 'y': 40, 'position': 'ST'},
    ]
    
    # Real Madrid 4-3-3
    team_b = [
        {'name': 'Courtois',    'number': 1,  'x': 115, 'y': 40, 'position': 'GK'},
        {'name': 'Carvajal',    'number': 2,  'x': 90,  'y': 70, 'position': 'RB'},
        {'name': 'Rüdiger',     'number': 22, 'x': 93,  'y': 52, 'position': 'CB'},
        {'name': 'Militão',     'number': 3,  'x': 93,  'y': 28, 'position': 'CB'},
        {'name': 'Mendy',       'number': 23, 'x': 90,  'y': 10, 'position': 'LB'},
        {'name': 'Tchouaméni',  'number': 14, 'x': 78,  'y': 40, 'position': 'CDM'},
        {'name': 'Valverde',    'number': 15, 'x': 70,  'y': 55, 'position': 'CM'},
        {'name': 'Bellingham',  'number': 5,  'x': 70,  'y': 25, 'position': 'CM'},
        {'name': 'Rodrygo',     'number': 11, 'x': 55,  'y': 65, 'position': 'RW'},
        {'name': 'Mbappé',      'number': 7,  'x': 50,  'y': 40, 'position': 'ST'},
        {'name': 'Vinícius',    'number': 20, 'x': 55,  'y': 15, 'position': 'LW'},
    ]
    
    # Plot everything
    fp.plot_players(ax, pitch, team_a, team_b,
                    team_a_name="FC Barcelona", team_b_name="Real Madrid",
                    team_a_color="#a50044", team_b_color="#ffffff")
    fp.plot_ball(ax, 60, 40)
    
    # Save
    fp.save(fig, "el_clasico.png")
    
    # Show
    plt.show()
    print("\nEl Clásico pitch model working!")