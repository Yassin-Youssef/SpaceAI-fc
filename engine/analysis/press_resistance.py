"""
SpaceAI FC - Press Resistance Analyzer
========================================
Measures how well a team handles being pressed.
Calculates pressure zones, pass success under pressure,
escape rates, and identifies vulnerable areas.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mplsoccer import Pitch


class PressResistance:
    """
    Analyzes a team's ability to play through opponent pressure.
    
    Metrics:
        - Press resistance score (0-100)
        - Pass success rate under pressure
        - Escape rate (forward progression under pressure)
        - Vulnerable zones (worst areas on the pitch)
    """
    
    def __init__(self, pressure_radius=10.0, pressure_threshold=2):
        """
        Parameters:
            pressure_radius: distance within which an opponent is considered pressing
            pressure_threshold: minimum nearby opponents to consider a pass "under pressure"
        """
        self.pressure_radius = pressure_radius
        self.pressure_threshold = pressure_threshold
        
        self.team_positions = []
        self.opponent_positions = []
        self.pass_events = []
        self.team_name = "Team"
        self.team_color = "#e74c3c"
        self.opponent_name = "Opponent"
    
    # ── Data input ──────────────────────────────────────────────
    
    def set_teams(self, team_positions, opponent_positions,
                  team_name="Team", team_color="#e74c3c",
                  opponent_name="Opponent"):
        """
        Set team and opponent positions.
        
        Parameters:
            team_positions: list of player dicts for the team being analyzed
            opponent_positions: list of player dicts for the pressing team
        """
        self.team_positions = team_positions
        self.opponent_positions = opponent_positions
        self.team_name = team_name
        self.team_color = team_color
        self.opponent_name = opponent_name
    
    def add_pass_events(self, events):
        """
        Add pass events for analysis.
        
        Parameters:
            events: list of dicts with:
                'passer': shirt number
                'receiver': shirt number
                'success': bool
                'x': pass origin x
                'y': pass origin y
                'end_x': pass destination x (optional, for escape rate)
                'end_y': pass destination y (optional)
        """
        self.pass_events = events
    
    # ── Analysis ────────────────────────────────────────────────
    
    def analyze(self):
        """
        Run full press resistance analysis.
        
        Returns:
            dict with:
                'press_resistance_score': 0-100
                'total_passes': int
                'passes_under_pressure': int
                'pass_success_overall': float (0-1)
                'pass_success_under_pressure': float (0-1)
                'escape_rate': float (0-1)
                'vulnerable_zones': list of zone dicts
                'zone_grid': 2D array of resistance values for visualization
        """
        if not self.pass_events:
            return self._empty_result()
        
        # Get opponent positions as numpy array for distance calc
        opp_positions = np.array([[p['x'], p['y']] for p in self.opponent_positions])
        
        # Determine team side
        avg_team_x = np.mean([p['x'] for p in self.team_positions])
        is_left_side = avg_team_x < 60
        
        # Classify each pass
        total = len(self.pass_events)
        successful = 0
        under_pressure = 0
        success_under_pressure = 0
        escapes = 0
        escapes_attempted = 0
        
        # Zone tracking: divide pitch into 3x2 grid (6 zones)
        zone_passes = {}
        zone_success = {}
        for zx in range(3):
            for zy in range(2):
                key = (zx, zy)
                zone_passes[key] = 0
                zone_success[key] = 0
        
        for event in self.pass_events:
            px, py = event['x'], event['y']
            success = event.get('success', True)
            
            if success:
                successful += 1
            
            # Count nearby opponents
            pass_pos = np.array([px, py])
            distances = np.linalg.norm(opp_positions - pass_pos, axis=1)
            nearby = np.sum(distances < self.pressure_radius)
            
            is_pressed = nearby >= self.pressure_threshold
            
            if is_pressed:
                under_pressure += 1
                if success:
                    success_under_pressure += 1
                
                # Check escape (forward progression)
                end_x = event.get('end_x', None)
                if end_x is not None:
                    escapes_attempted += 1
                    if is_left_side:
                        if end_x > px + 5 and success:
                            escapes += 1
                    else:
                        if end_x < px - 5 and success:
                            escapes += 1
            
            # Zone assignment
            zx = min(int(px / 40), 2)
            zy = min(int(py / 40), 1)
            zone_passes[(zx, zy)] += 1
            if success:
                zone_success[(zx, zy)] += 1
        
        # Compute metrics
        pass_success_overall = successful / total if total > 0 else 0
        pass_success_pressure = (success_under_pressure / under_pressure
                                  if under_pressure > 0 else 1.0)
        escape_rate = escapes / escapes_attempted if escapes_attempted > 0 else 0.5
        
        # Press resistance score (0-100)
        # Weighted: 40% pass success under pressure, 30% escape rate, 30% overall
        score = (
            pass_success_pressure * 40 +
            escape_rate * 30 +
            pass_success_overall * 30
        )
        score = round(min(100, max(0, score)), 1)
        
        # Vulnerable zones
        vulnerable_zones = []
        zone_grid = np.zeros((2, 3))
        
        zone_labels = {
            (0, 0): "Own Third - Left",
            (0, 1): "Own Third - Right",
            (1, 0): "Middle Third - Left",
            (1, 1): "Middle Third - Right",
            (2, 0): "Final Third - Left",
            (2, 1): "Final Third - Right",
        }
        
        for (zx, zy), total_zone_passes in zone_passes.items():
            if total_zone_passes > 0:
                rate = zone_success[(zx, zy)] / total_zone_passes
                zone_grid[zy, zx] = rate
                
                if rate < 0.6:
                    vulnerable_zones.append({
                        'zone': zone_labels.get((zx, zy), f"Zone ({zx},{zy})"),
                        'success_rate': round(rate, 2),
                        'total_passes': total_zone_passes,
                        'x_range': (zx * 40, (zx + 1) * 40),
                        'y_range': (zy * 40, (zy + 1) * 40),
                    })
            else:
                zone_grid[zy, zx] = 0.5  # neutral if no data
        
        vulnerable_zones.sort(key=lambda z: z['success_rate'])
        
        return {
            'press_resistance_score': score,
            'total_passes': total,
            'passes_under_pressure': under_pressure,
            'pass_success_overall': round(pass_success_overall, 2),
            'pass_success_under_pressure': round(pass_success_pressure, 2),
            'escape_rate': round(escape_rate, 2),
            'vulnerable_zones': vulnerable_zones,
            'zone_grid': zone_grid,
        }
    
    def _empty_result(self):
        """Return empty result when no data available."""
        return {
            'press_resistance_score': 50.0,
            'total_passes': 0,
            'passes_under_pressure': 0,
            'pass_success_overall': 0,
            'pass_success_under_pressure': 0,
            'escape_rate': 0,
            'vulnerable_zones': [],
            'zone_grid': np.ones((2, 3)) * 0.5,
        }
    
    # ── Visualization ───────────────────────────────────────────
    
    def draw(self, result=None, figsize=(12, 8), title=None):
        """
        Draw press resistance heatmap on the pitch.
        
        Green = good resistance, Red = vulnerable.
        
        Parameters:
            result: output from analyze(). If None, calls analyze() internally.
            figsize: figure size
            title: optional title
        
        Returns:
            fig, ax
        """
        if result is None:
            result = self.analyze()
        
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
            fig.suptitle(title, color='white', fontsize=16,
                         fontweight='bold', y=0.98)
        
        # Create heatmap from zone grid
        zone_grid = result['zone_grid']
        
        # Upsample zone grid for smoother visualization
        from scipy.ndimage import zoom
        smooth_grid = zoom(zone_grid, (40, 40), order=1)
        
        # Custom colormap: red (vulnerable) → yellow → green (resistant)
        cmap = LinearSegmentedColormap.from_list('resistance',
            ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71'], N=256)
        
        extent = [0, 120, 0, 80]
        ax.imshow(smooth_grid, extent=extent, origin='lower',
                  cmap=cmap, alpha=0.45, aspect='auto', zorder=2,
                  vmin=0, vmax=1)
        
        # Draw zone boundaries
        for zx in range(1, 3):
            ax.axvline(x=zx * 40, color='white', linestyle=':', alpha=0.3, zorder=3)
        ax.axhline(y=40, color='white', linestyle=':', alpha=0.3, zorder=3)
        
        # Zone labels with success rates
        zone_labels_pos = {
            (0, 0): (20, 20),
            (0, 1): (20, 60),
            (1, 0): (60, 20),
            (1, 1): (60, 60),
            (2, 0): (100, 20),
            (2, 1): (100, 60),
        }
        
        for (zx, zy), (lx, ly) in zone_labels_pos.items():
            rate = zone_grid[zy, zx]
            color = '#2ecc71' if rate >= 0.7 else '#f39c12' if rate >= 0.5 else '#e74c3c'
            ax.text(lx, ly, f"{rate:.0%}", ha='center', va='center',
                    fontsize=14, fontweight='bold', color=color, zorder=8,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#1a1a2e',
                              edgecolor=color, alpha=0.9, linewidth=1.5))
        
        # Draw team players
        for p in self.team_positions:
            ax.scatter(p['x'], p['y'], c=self.team_color, s=200,
                       edgecolors='white', linewidths=1.5, zorder=6)
            ax.annotate(str(p['number']), xy=(p['x'], p['y']),
                        ha='center', va='center', fontsize=7,
                        fontweight='bold', color='white', zorder=7)
        
        # Draw opponent players (faded)
        for p in self.opponent_positions:
            ax.scatter(p['x'], p['y'], c='#cccccc', s=150,
                       edgecolors='#888888', linewidths=1, zorder=5, alpha=0.5)
        
        # Stats box
        score = result['press_resistance_score']
        score_color = '#2ecc71' if score >= 65 else '#f39c12' if score >= 45 else '#e74c3c'
        
        stats_text = (
            f"Press Resistance: {score:.0f}/100  |  "
            f"Under Pressure: {result['passes_under_pressure']}/{result['total_passes']}  |  "
            f"Success: {result['pass_success_under_pressure']:.0%}  |  "
            f"Escape: {result['escape_rate']:.0%}"
        )
        
        ax.text(60, -5, stats_text, ha='center', va='top', fontsize=9,
                color='white', fontweight='bold', zorder=10,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#2a2a3e',
                          edgecolor=score_color, alpha=0.9, linewidth=2))
        
        return fig, ax
    
    # ── Text output ─────────────────────────────────────────────
    
    def print_analysis(self, result=None):
        """Print formatted press resistance analysis."""
        if result is None:
            result = self.analyze()
        
        print("\n" + "=" * 60)
        print("  PRESS RESISTANCE ANALYSIS")
        print("=" * 60)
        
        print(f"\n  Team: {self.team_name}")
        print(f"  Opponent: {self.opponent_name}")
        
        score = result['press_resistance_score']
        rating = "Excellent" if score >= 75 else "Good" if score >= 60 else "Average" if score >= 45 else "Poor"
        
        print(f"\n  Press Resistance Score: {score:.0f}/100 ({rating})")
        print(f"  Total Passes: {result['total_passes']}")
        print(f"  Passes Under Pressure: {result['passes_under_pressure']}")
        print(f"  Overall Pass Success: {result['pass_success_overall']:.0%}")
        print(f"  Pass Success Under Pressure: {result['pass_success_under_pressure']:.0%}")
        print(f"  Escape Rate: {result['escape_rate']:.0%}")
        
        if result['vulnerable_zones']:
            print(f"\n  Vulnerable Zones:")
            for vz in result['vulnerable_zones']:
                print(f"    {vz['zone']}: {vz['success_rate']:.0%} success "
                      f"({vz['total_passes']} passes)")
        else:
            print(f"\n  No vulnerable zones detected.")
        
        # Tactical assessment
        print(f"\n  Tactical Assessment:")
        if score >= 75:
            print(f"    {self.team_name} shows excellent press resistance.")
            print(f"    The team comfortably plays through opponent pressure.")
        elif score >= 60:
            print(f"    {self.team_name} handles pressure well overall.")
            print(f"    Some zones could improve — focus on vulnerable areas.")
        elif score >= 45:
            print(f"    {self.team_name} struggles under sustained pressure.")
            print(f"    Consider going long or switching play to relieve pressure.")
        else:
            print(f"    {self.team_name} is highly vulnerable to pressing.")
            print(f"    Recommend adjusting build-up play to avoid press traps.")
        
        print("\n" + "=" * 60)
    
    # ── Save ────────────────────────────────────────────────────
    
    def save(self, fig, filename):
        """Save figure to outputs folder."""
        fig.savefig(f"outputs/{filename}", dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved: outputs/{filename}")


# ═══════════════════════════════════════════════════════════════
# Quick test — El Clásico press resistance
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    
    import os
    import random
    os.makedirs("outputs", exist_ok=True)
    
    # Barcelona 4-2-3-1
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
    
    # Generate synthetic pass events for Barcelona
    random.seed(42)
    pass_events = []
    
    barca_outfield = [p for p in barca if p['position'] != 'GK']
    
    for _ in range(65):
        passer = random.choice(barca_outfield)
        receiver = random.choice(barca_outfield)
        
        # Passes near opponents are more likely to fail
        px, py = passer['x'] + random.gauss(0, 3), passer['y'] + random.gauss(0, 3)
        px = max(0, min(120, px))
        py = max(0, min(80, py))
        
        end_x = receiver['x'] + random.gauss(0, 3)
        end_y = receiver['y'] + random.gauss(0, 3)
        
        # Check pressure to determine success probability
        opp_pos = np.array([[p['x'], p['y']] for p in madrid])
        dist = np.linalg.norm(opp_pos - np.array([px, py]), axis=1)
        nearby = np.sum(dist < 10)
        
        # Higher failure rate under pressure
        if nearby >= 2:
            success = random.random() < 0.55  # 55% under heavy pressure
        elif nearby >= 1:
            success = random.random() < 0.75  # 75% under light pressure
        else:
            success = random.random() < 0.90  # 90% when free
        
        pass_events.append({
            'passer': passer['number'],
            'receiver': receiver['number'],
            'success': success,
            'x': px,
            'y': py,
            'end_x': end_x,
            'end_y': end_y,
        })
    
    # Analyze
    pr = PressResistance(pressure_radius=10.0, pressure_threshold=2)
    pr.set_teams(barca, madrid,
                 team_name="FC Barcelona", team_color="#a50044",
                 opponent_name="Real Madrid")
    pr.add_pass_events(pass_events)
    
    result = pr.analyze()
    pr.print_analysis(result)
    
    fig, ax = pr.draw(result,
                       title="SpaceAI FC - Barcelona Press Resistance")
    pr.save(fig, "press_resistance_barca.png")
    
    plt.show()
    print("\nPress resistance analysis complete!")
