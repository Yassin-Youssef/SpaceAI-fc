"""
SpaceAI FC - Space Control Analysis
====================================
Computes territorial dominance using Voronoi tessellation
and influence-based models. Shows which team controls which
areas of the pitch.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial import Voronoi
from mplsoccer import Pitch


class SpaceControl:
    """
    Analyzes spatial dominance between two teams.
    
    Two methods:
        - Voronoi: divides pitch into zones closest to each player
        - Influence: each player exerts decaying influence over surrounding space
    
    Coordinate system:
        x: 0 to 120 (length)
        y: 0 to 80 (width)
    """
    
    def __init__(self, pitch_length=120, pitch_width=80):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.team_a = []
        self.team_b = []
        self.ball_pos = None
    
    # Data input
    
    def set_teams(self, team_a, team_b):
        """
        Set player positions for both teams.
        
        Parameters:
            team_a: list of dicts with 'name', 'number', 'x', 'y', 'position'
            team_b: same format
        """
        self.team_a = team_a
        self.team_b = team_b
    
    def set_ball(self, x, y):
        """Set the ball position."""
        self.ball_pos = (x, y)
    
    # Voronoi space control
    
    def compute_voronoi_control(self, resolution=200):
        """
        Compute space control using nearest-player assignment.
        
        Each point on the pitch is assigned to the closest player.
        Then we check which team that player belongs to.
        
        Parameters:
            resolution: grid resolution (higher = smoother but slower)
        
        Returns:
            control_grid: 2D array where 1 = team A, -1 = team B
            stats: dict with control percentages
        """
        # Create pitch grid
        x_grid = np.linspace(0, self.pitch_length, resolution)
        y_grid = np.linspace(0, self.pitch_width, resolution)
        xx, yy = np.meshgrid(x_grid, y_grid)
        
        # All player positions
        team_a_pos = np.array([[p['x'], p['y']] for p in self.team_a])
        team_b_pos = np.array([[p['x'], p['y']] for p in self.team_b])
        
        # For each grid point, find closest player from each team
        grid_points = np.stack([xx.ravel(), yy.ravel()], axis=1)
        
        # Distance to nearest team A player
        dist_a = np.min(np.linalg.norm(
            grid_points[:, np.newaxis, :] - team_a_pos[np.newaxis, :, :], axis=2
        ), axis=1)
        
        # Distance to nearest team B player
        dist_b = np.min(np.linalg.norm(
            grid_points[:, np.newaxis, :] - team_b_pos[np.newaxis, :, :], axis=2
        ), axis=1)
        
        # Control: positive = team A, negative = team B
        control = np.where(dist_a < dist_b, 1.0, -1.0)
        control_grid = control.reshape(xx.shape)
        
        # Calculate percentages
        team_a_pct = round(np.sum(control_grid > 0) / control_grid.size * 100, 1)
        team_b_pct = round(100 - team_a_pct, 1)
        
        # Zone breakdown (defensive third, middle, attacking third)
        third = resolution // 3
        zones = self._compute_zones(control_grid, third)
        
        stats = {
            'team_a_control': team_a_pct,
            'team_b_control': team_b_pct,
            'zones': zones,
        }
        
        return control_grid, stats
    
    # Influence-based space control
    
    def compute_influence_control(self, resolution=200, sigma=15.0):
        """
        Compute space control using Gaussian influence model.
        
        Each player exerts influence that decays with distance.
        The influence is stronger near the ball.
        
        Parameters:
            resolution: grid resolution
            sigma: influence radius (higher = wider influence per player)
        
        Returns:
            control_grid: 2D array, positive = team A, negative = team B
            stats: dict with control percentages
        """
        x_grid = np.linspace(0, self.pitch_length, resolution)
        y_grid = np.linspace(0, self.pitch_width, resolution)
        xx, yy = np.meshgrid(x_grid, y_grid)
        
        grid_points = np.stack([xx.ravel(), yy.ravel()], axis=1)
        
        # Compute influence for each team
        influence_a = self._compute_team_influence(grid_points, self.team_a, sigma)
        influence_b = self._compute_team_influence(grid_points, self.team_b, sigma)
        
        # Net control: positive = team A dominant, negative = team B dominant
        net_influence = influence_a - influence_b
        
        # Normalize to -1 to 1 range
        max_val = np.max(np.abs(net_influence))
        if max_val > 0:
            net_influence = net_influence / max_val
        
        control_grid = net_influence.reshape(xx.shape)
        
        # Calculate percentages
        team_a_pct = round(np.sum(control_grid > 0) / control_grid.size * 100, 1)
        team_b_pct = round(100 - team_a_pct, 1)
        
        third = resolution // 3
        zones = self._compute_zones(control_grid, third)
        
        stats = {
            'team_a_control': team_a_pct,
            'team_b_control': team_b_pct,
            'zones': zones,
        }
        
        return control_grid, stats
    
    def _compute_team_influence(self, grid_points, team, sigma):
        """Compute combined Gaussian influence of all players on a team."""
        influence = np.zeros(grid_points.shape[0])
        
        for player in team:
            px, py = player['x'], player['y']
            pos = np.array([px, py])
            
            # Distance from this player to every grid point
            dist = np.linalg.norm(grid_points - pos, axis=1)
            
            # Gaussian influence
            player_influence = np.exp(-dist**2 / (2 * sigma**2))
            
            # GK has less outfield influence
            if player.get('position') == 'GK':
                player_influence *= 0.5
            
            influence += player_influence
        
        return influence
    
    # Zone analysis
    
    def _compute_zones(self, control_grid, third):
        """Compute control percentages for each third of the pitch."""
        # Left third (team A defensive)
        left = control_grid[:, :third]
        # Middle third
        middle = control_grid[:, third:2*third]
        # Right third (team A attacking)
        right = control_grid[:, 2*third:]
        
        zones = {
            'defensive_third': {
                'team_a': round(np.sum(left > 0) / left.size * 100, 1),
                'team_b': round(np.sum(left <= 0) / left.size * 100, 1),
            },
            'middle_third': {
                'team_a': round(np.sum(middle > 0) / middle.size * 100, 1),
                'team_b': round(np.sum(middle <= 0) / middle.size * 100, 1),
            },
            'attacking_third': {
                'team_a': round(np.sum(right > 0) / right.size * 100, 1),
                'team_b': round(np.sum(right <= 0) / right.size * 100, 1),
            },
        }
        return zones
    
    def get_midfield_control(self, control_grid):
        """Check which team controls the central midfield area."""
        h, w = control_grid.shape
        # Central band: middle 40% of width, middle 40% of length
        x_start = int(w * 0.3)
        x_end = int(w * 0.7)
        y_start = int(h * 0.3)
        y_end = int(h * 0.7)
        
        center = control_grid[y_start:y_end, x_start:x_end]
        team_a_pct = round(np.sum(center > 0) / center.size * 100, 1)
        team_b_pct = round(100 - team_a_pct, 1)
        
        return {'team_a': team_a_pct, 'team_b': team_b_pct}
    
    # Visualization
    
    def draw_voronoi(self, figsize=(12, 8), title=None,
                     team_a_name="Team A", team_b_name="Team B",
                     team_a_color="#e74c3c", team_b_color="#3498db"):
        """Draw Voronoi-based space control map."""
        control_grid, stats = self.compute_voronoi_control()
        return self._draw_control(control_grid, stats, figsize, title,
                                  team_a_name, team_b_name,
                                  team_a_color, team_b_color, mode="voronoi")
    
    def draw_influence(self, figsize=(12, 8), title=None,
                       team_a_name="Team A", team_b_name="Team B",
                       team_a_color="#e74c3c", team_b_color="#3498db",
                       sigma=15.0):
        """Draw influence-based space control map."""
        control_grid, stats = self.compute_influence_control(sigma=sigma)
        return self._draw_control(control_grid, stats, figsize, title,
                                  team_a_name, team_b_name,
                                  team_a_color, team_b_color, mode="influence")
    
    def _draw_control(self, control_grid, stats, figsize, title,
                      team_a_name, team_b_name,
                      team_a_color, team_b_color, mode="influence"):
        """Core drawing method for both control types."""
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
        
        # Custom colormap: team_a_color <-> white <-> team_b_color
        cmap = LinearSegmentedColormap.from_list('control',
            [team_a_color, '#1a1a2e', team_b_color], N=256)
        
        # Draw control heatmap
        extent = [0, self.pitch_length, 0, self.pitch_width]
        ax.imshow(control_grid, extent=extent, origin='lower',
                  cmap=cmap, alpha=0.55, aspect='auto', zorder=2,
                  vmin=-1, vmax=1)
        
        # Draw players - Team A
        for player in self.team_a:
            ax.scatter(player['x'], player['y'], c=team_a_color, s=300,
                       edgecolors='white', linewidths=2, zorder=6, alpha=0.95)
            ax.annotate(str(player['number']), xy=(player['x'], player['y']),
                       ha='center', va='center', fontsize=8,
                       fontweight='bold', color='white', zorder=7)
            ax.annotate(player['name'], xy=(player['x'], player['y'] + 3),
                       ha='center', va='bottom', fontsize=7,
                       color='white', zorder=7, alpha=0.85)
        
        # Draw players - Team B
        for player in self.team_b:
            ax.scatter(player['x'], player['y'], c=team_b_color, s=300,
                       edgecolors='white', linewidths=2, zorder=6, alpha=0.95)
            ax.annotate(str(player['number']), xy=(player['x'], player['y']),
                       ha='center', va='center', fontsize=8,
                       fontweight='bold', color='white', zorder=7)
            ax.annotate(player['name'], xy=(player['x'], player['y'] + 3),
                       ha='center', va='bottom', fontsize=7,
                       color='white', zorder=7, alpha=0.85)
        
        # Draw ball
        if self.ball_pos:
            ax.scatter(self.ball_pos[0], self.ball_pos[1], c='#f1c40f', s=120,
                       edgecolors='white', linewidths=2, zorder=8, marker='o')
        
        # Stats box
        midfield = self.get_midfield_control(control_grid)
        stats_text = (
            f"{team_a_name}: {stats['team_a_control']}%    "
            f"{team_b_name}: {stats['team_b_control']}%\n"
            f"Midfield: {team_a_name} {midfield['team_a']}% | "
            f"{team_b_name} {midfield['team_b']}%"
        )
        
        ax.text(60, -5, stats_text, ha='center', va='top', fontsize=10,
                color='white', fontweight='bold', zorder=10,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#2a2a3e',
                          edgecolor='#444444', alpha=0.9))
        
        # Legend
        ax.scatter([], [], c=team_a_color, s=100, edgecolors='white',
                   linewidths=1.5, label=team_a_name)
        ax.scatter([], [], c=team_b_color, s=100, edgecolors='white',
                   linewidths=1.5, label=team_b_name)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.06),
                  ncol=2, fontsize=10, facecolor='#1a1a2e',
                  edgecolor='#444444', labelcolor='white')
        
        return fig, ax, stats
    
    # Text output
    
    def print_analysis(self, stats, team_a_name="Team A", team_b_name="Team B"):
        """Print formatted space control analysis."""
        print("\n" + "=" * 55)
        print("  SPACE CONTROL ANALYSIS")
        print("=" * 55)
        
        print(f"\n  Overall Control:")
        print(f"    {team_a_name}: {stats['team_a_control']}%")
        print(f"    {team_b_name}: {stats['team_b_control']}%")
        
        zones = stats['zones']
        print(f"\n  Zone Breakdown:")
        print(f"    Defensive Third:  {team_a_name} {zones['defensive_third']['team_a']}% | {team_b_name} {zones['defensive_third']['team_b']}%")
        print(f"    Middle Third:     {team_a_name} {zones['middle_third']['team_a']}% | {team_b_name} {zones['middle_third']['team_b']}%")
        print(f"    Attacking Third:  {team_a_name} {zones['attacking_third']['team_a']}% | {team_b_name} {zones['attacking_third']['team_b']}%")
        
        # Determine dominant team
        if stats['team_a_control'] > 55:
            print(f"\n  Verdict: {team_a_name} dominating space")
        elif stats['team_b_control'] > 55:
            print(f"\n  Verdict: {team_b_name} dominating space")
        else:
            print(f"\n  Verdict: Balanced space control")
        
        print("\n" + "=" * 55)


# Quick test - El Clásico space control

if __name__ == "__main__":
    
    sc = SpaceControl()
    
    # Barcelona 4-2-3-1
    team_a = [
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
    
    sc.set_teams(team_a, team_b)
    sc.set_ball(60, 40)
    
    # VISUALIZATION 1: Voronoi control
    print("\n--- Voronoi Space Control ---")
    fig1, ax1, stats1 = sc.draw_voronoi(
        title="SpaceAI FC - Space Control (Voronoi)",
        team_a_name="FC Barcelona",
        team_b_name="Real Madrid",
        team_a_color="#a50044",
        team_b_color="#ffffff"
    )
    sc.print_analysis(stats1, "FC Barcelona", "Real Madrid")
    fig1.savefig("outputs/space_control_voronoi.png", dpi=150, bbox_inches='tight',
                 facecolor=fig1.get_facecolor())
    print("Saved: outputs/space_control_voronoi.png")
    
    # VISUALIZATION 2: Influence control
    print("\n--- Influence Space Control ---")
    fig2, ax2, stats2 = sc.draw_influence(
        title="SpaceAI FC - Space Control (Influence Model)",
        team_a_name="FC Barcelona",
        team_b_name="Real Madrid",
        team_a_color="#a50044",
        team_b_color="#ffffff",
        sigma=15.0
    )
    sc.print_analysis(stats2, "FC Barcelona", "Real Madrid")
    fig2.savefig("outputs/space_control_influence.png", dpi=150, bbox_inches='tight',
                 facecolor=fig2.get_facecolor())
    print("Saved: outputs/space_control_influence.png")
    
    plt.show()
    print("\nSpace control analysis complete!")