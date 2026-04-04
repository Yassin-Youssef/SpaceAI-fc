"""
SpaceAI FC - Player Role Classification
==========================================
Classifies players into tactical sub-roles beyond basic position.
Rule-based engine maps position, coordinates, and optional stats
into roles like "False Nine", "Inverted Winger", "Deep-Lying Playmaker", etc.
"""

import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import Pitch


class RoleClassifier:
    """
    Classifies each player into a tactical sub-role.
    
    Rule-based approach using:
        - Base position tag (GK, CB, RB, LB, CM, CDM, CAM, LW, RW, ST)
        - x/y coordinates (depth and width)
        - Optional performance stats (passes_made, defensive_actions, etc.)
    
    Output per player:
        - role: tactical sub-role label
        - confidence: 0-1
        - reasoning: text explanation
    """
    
    def __init__(self):
        self.players = []
        self.team_name = "Team"
        self.team_color = "#e74c3c"
    
    # ── Data input ──────────────────────────────────────────────
    
    def set_team(self, players, team_name="Team", team_color="#e74c3c"):
        """
        Set team data.
        
        Parameters:
            players: list of dicts with at minimum:
                'name', 'number', 'x', 'y', 'position'
            Optionally:
                'passes_made', 'passes_received', 'defensive_actions',
                'touches_in_box', 'average_position_x', 'average_position_y'
        """
        self.players = players
        self.team_name = team_name
        self.team_color = team_color
    
    # ── Classification ──────────────────────────────────────────
    
    def classify_all(self):
        """
        Classify every player in the team.
        
        Returns:
            list of dicts, one per player, each with:
                'name', 'number', 'position', 'role', 'confidence', 'reasoning'
        """
        results = []
        for player in self.players:
            result = self._classify_player(player)
            results.append(result)
        return results
    
    def _classify_player(self, player):
        """Classify a single player based on position and context."""
        pos = player.get('position', '').upper()
        x = player.get('x', 60)
        y = player.get('y', 40)
        name = player.get('name', 'Unknown')
        number = player.get('number', 0)
        
        # Determine team side (left or right)
        avg_team_x = np.mean([p['x'] for p in self.players])
        is_left_side = avg_team_x < 60
        
        # Normalize x to "attacking depth" (0 = own goal, 120 = opponent goal)
        depth = x if is_left_side else (120 - x)
        
        # Normalize y to width context (0 = bottom touchline, 80 = top touchline)
        # Distance from nearest touchline
        touchline_dist = min(y, 80 - y)
        
        # Optional stats
        passes_made = player.get('passes_made', None)
        passes_received = player.get('passes_received', None)
        defensive_actions = player.get('defensive_actions', None)
        touches_in_box = player.get('touches_in_box', None)
        
        # Classification by position group
        if pos == 'GK':
            return self._classify_gk(player, depth)
        elif pos in ('CB',):
            return self._classify_cb(player, depth, touchline_dist)
        elif pos in ('RB', 'LB', 'RWB', 'LWB'):
            return self._classify_fb(player, pos, depth, touchline_dist, y)
        elif pos in ('CDM', 'DM'):
            return self._classify_dm(player, depth)
        elif pos in ('CM',):
            return self._classify_cm(player, depth, touchline_dist)
        elif pos in ('CAM', 'AM'):
            return self._classify_am(player, depth)
        elif pos in ('LW', 'RW', 'LM', 'RM'):
            return self._classify_winger(player, pos, depth, touchline_dist, y)
        elif pos in ('ST', 'CF', 'FW'):
            return self._classify_striker(player, depth, touchline_dist)
        else:
            return self._build_result(player, "Utility Player", 0.4,
                                       f"Position '{pos}' does not map to a specific tactical role")
    
    def _classify_gk(self, player, depth):
        """Classify goalkeeper."""
        if depth > 12:
            return self._build_result(player, "Sweeper Keeper", 0.80,
                f"Positioned high (depth={depth:.0f}) — plays as a sweeper keeper, "
                f"actively involved in build-up play outside the box")
        else:
            return self._build_result(player, "Traditional GK", 0.85,
                f"Positioned deep (depth={depth:.0f}) — traditional shot-stopper, "
                f"stays close to the goal line")
    
    def _classify_cb(self, player, depth, touchline_dist):
        """Classify centre-back."""
        passes = player.get('passes_made', None)
        
        if depth > 35:
            return self._build_result(player, "Sweeper", 0.70,
                f"Positioned unusually high for a CB (depth={depth:.0f}) — "
                f"acts as a sweeper, covering space behind the defensive line")
        
        if passes is not None and passes > 40:
            return self._build_result(player, "Ball-Playing CB", 0.75,
                f"High passing volume ({passes} passes) — ball-playing centre-back "
                f"who initiates build-up from deep")
        
        # Default: standard CB
        return self._build_result(player, "Centre-Back", 0.80,
            f"Standard defensive positioning (depth={depth:.0f}) — "
            f"primary role is defensive solidity")
    
    def _classify_fb(self, player, pos, depth, touchline_dist, y):
        """Classify fullback."""
        side = "right" if pos in ('RB', 'RWB') else "left"
        
        # Overlapping: positioned high and wide
        if depth > 40 and touchline_dist < 20:
            return self._build_result(player, f"Overlapping {side.title()}back", 0.80,
                f"Positioned high (depth={depth:.0f}) and wide (touchline dist={touchline_dist:.0f}) — "
                f"overlapping fullback providing width in attack")
        
        # Inverted: positioned inside, narrower than expected
        if touchline_dist > 25:
            return self._build_result(player, f"Inverted Fullback", 0.70,
                f"Positioned narrow (touchline dist={touchline_dist:.0f}) instead of wide — "
                f"inverted fullback who tucks into midfield")
        
        # Wing-back (high + wide, typically in 3-at-back)
        if depth > 45:
            return self._build_result(player, f"Wing-Back", 0.75,
                f"Very high positioning (depth={depth:.0f}) — operating as a wing-back, "
                f"providing both defensive and attacking width")
        
        return self._build_result(player, f"Fullback", 0.80,
            f"Standard fullback positioning (depth={depth:.0f}, "
            f"touchline dist={touchline_dist:.0f})")
    
    def _classify_dm(self, player, depth):
        """Classify defensive midfielder."""
        passes = player.get('passes_made', None)
        
        if passes is not None and passes > 35:
            return self._build_result(player, "Deep-Lying Playmaker", 0.80,
                f"High passing volume ({passes} passes) from deep — "
                f"deep-lying playmaker dictating tempo from in front of the defence")
        
        if depth < 35:
            return self._build_result(player, "Anchor Man", 0.75,
                f"Positioned very deep (depth={depth:.0f}) — "
                f"sits as an anchor in front of the backline, prioritising defensive screening")
        
        return self._build_result(player, "Defensive Midfielder", 0.80,
            f"Standard CDM positioning (depth={depth:.0f}) — "
            f"shields the defence and recycles possession")
    
    def _classify_cm(self, player, depth, touchline_dist):
        """Classify central midfielder."""
        passes = player.get('passes_made', None)
        defensive_actions = player.get('defensive_actions', None)
        
        # Deep position → deep-lying playmaker
        if depth < 38:
            if passes is not None and passes > 30:
                return self._build_result(player, "Deep-Lying Playmaker", 0.75,
                    f"Central midfielder sitting deep (depth={depth:.0f}) with high "
                    f"passing ({passes}) — deep-lying playmaker role")
            return self._build_result(player, "Defensive Midfielder", 0.65,
                f"Central midfielder sitting deep (depth={depth:.0f}) — "
                f"functions as a de facto defensive midfielder")
        
        # Advanced position → attacking midfielder
        if depth > 55:
            return self._build_result(player, "Attacking Midfielder", 0.70,
                f"Central midfielder pushed forward (depth={depth:.0f}) — "
                f"operating in the half-spaces as an attacking midfielder")
        
        # Balanced depth → box-to-box
        return self._build_result(player, "Box-to-Box", 0.80,
            f"Balanced positioning (depth={depth:.0f}) — "
            f"box-to-box midfielder covering both defensive and attacking phases")
    
    def _classify_am(self, player, depth):
        """Classify attacking midfielder / number 10."""
        touches_box = player.get('touches_in_box', None)
        
        if depth > 65:
            return self._build_result(player, "Shadow Striker", 0.70,
                f"Positioned very high for a CAM (depth={depth:.0f}) — "
                f"operates as a shadow striker, making runs beyond the main striker")
        
        if depth < 50:
            return self._build_result(player, "Advanced Playmaker", 0.70,
                f"Deeper than a typical CAM (depth={depth:.0f}) — "
                f"drops to collect the ball and orchestrate attacks")
        
        return self._build_result(player, "Classic No. 10", 0.80,
            f"Standard attacking midfielder position (depth={depth:.0f}) — "
            f"classic number 10, linking midfield and attack")
    
    def _classify_winger(self, player, pos, depth, touchline_dist, y):
        """Classify winger / wide midfielder."""
        side = "right" if pos in ('RW', 'RM') else "left"
        
        # Expected touchline: RW near y=80, LW near y=0
        # "Inverted" if they are on the opposite side of center
        if side == "right" and y < 45:
            return self._build_result(player, "Inverted Winger", 0.70,
                f"Right-sided winger positioned in left half-space (y={y:.0f}) — "
                f"cuts inside onto stronger foot")
        if side == "left" and y > 35:
            return self._build_result(player, "Inverted Winger", 0.70,
                f"Left-sided winger positioned in right half-space (y={y:.0f}) — "
                f"cuts inside onto stronger foot")
        
        # Very advanced → inside forward
        if depth > 65:
            return self._build_result(player, "Inside Forward", 0.75,
                f"Positioned very high (depth={depth:.0f}) — "
                f"inside forward who drives into the box from wide areas")
        
        # Wide and not too advanced → traditional winger
        if touchline_dist < 18:
            return self._build_result(player, f"Traditional Winger", 0.80,
                f"Positioned wide (touchline dist={touchline_dist:.0f}) — "
                f"traditional {side} winger who hugs the touchline and delivers crosses")
        
        return self._build_result(player, f"Wide Forward", 0.70,
            f"{side.title()} winger with balanced positioning "
            f"(depth={depth:.0f}, touchline dist={touchline_dist:.0f})")
    
    def _classify_striker(self, player, depth, touchline_dist):
        """Classify striker."""
        touches_box = player.get('touches_in_box', None)
        passes = player.get('passes_made', None)
        
        # Deep-dropping striker → false nine
        if depth < 65:
            return self._build_result(player, "False Nine", 0.75,
                f"Positioned deep for a striker (depth={depth:.0f}) — "
                f"false nine who drops into midfield to create space and link play")
        
        # Very central and high → poacher
        if depth > 75 and touchline_dist > 20:
            if touches_box is not None and touches_box > 5:
                return self._build_result(player, "Poacher", 0.80,
                    f"High central position (depth={depth:.0f}) with box presence — "
                    f"poacher who lives in and around the penalty area")
            return self._build_result(player, "Poacher", 0.70,
                f"Very advanced central position (depth={depth:.0f}) — "
                f"goal-poacher waiting for chances in the box")
        
        # High, physical presence → target man
        if depth > 70:
            return self._build_result(player, "Target Man", 0.65,
                f"Advanced position (depth={depth:.0f}) — "
                f"target man providing a focal point in attack")
        
        return self._build_result(player, "Striker", 0.75,
            f"Standard striker positioning (depth={depth:.0f})")
    
    def _build_result(self, player, role, confidence, reasoning):
        """Build a classification result dict."""
        return {
            'name': player.get('name', 'Unknown'),
            'number': player.get('number', 0),
            'position': player.get('position', ''),
            'x': player.get('x', 0),
            'y': player.get('y', 0),
            'role': role,
            'confidence': round(confidence, 2),
            'reasoning': reasoning,
        }
    
    # ── Visualization ───────────────────────────────────────────
    
    def draw(self, results=None, figsize=(12, 8), title=None):
        """
        Draw pitch with role labels next to each player.
        
        Parameters:
            results: output from classify_all(). If None, calls it internally.
            figsize: figure size
            title: optional title
        
        Returns:
            fig, ax
        """
        if results is None:
            results = self.classify_all()
        
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
        
        # Role color map
        role_colors = {
            'GK': '#888888',
            'DEF': '#3498db',
            'MID': '#2ecc71',
            'ATT': '#e74c3c',
        }
        
        for r in results:
            x, y = r['x'], r['y']
            pos = r['position'].upper()
            
            # Determine role color group
            if pos == 'GK':
                role_color = role_colors['GK']
            elif pos in ('CB', 'RB', 'LB', 'RWB', 'LWB'):
                role_color = role_colors['DEF']
            elif pos in ('CDM', 'DM', 'CM', 'CAM', 'AM'):
                role_color = role_colors['MID']
            else:
                role_color = role_colors['ATT']
            
            # Player dot
            ax.scatter(x, y, c=self.team_color, s=300,
                       edgecolors='white', linewidths=2, zorder=6, alpha=0.95)
            
            # Number inside dot
            ax.annotate(str(r['number']), xy=(x, y),
                        ha='center', va='center', fontsize=8,
                        fontweight='bold', color='white', zorder=7)
            
            # Role label above (instead of player name)
            role_label = r['role']
            conf = r['confidence']
            ax.annotate(role_label, xy=(x, y + 3.5),
                        ha='center', va='bottom', fontsize=7,
                        fontweight='bold', color=role_color, zorder=7,
                        bbox=dict(boxstyle='round,pad=0.15',
                                  facecolor='#1a1a2e', edgecolor=role_color,
                                  alpha=0.8, linewidth=0.8))
            
            # Player name below
            ax.annotate(r['name'], xy=(x, y - 4),
                        ha='center', va='top', fontsize=6,
                        color='#aaaaaa', zorder=7, alpha=0.8)
        
        # Legend
        ax.scatter([], [], c=self.team_color, s=100, edgecolors='white',
                   linewidths=1.5, label=self.team_name)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.02),
                  ncol=1, fontsize=10, facecolor='#1a1a2e',
                  edgecolor='#444444', labelcolor='white')
        
        return fig, ax
    
    # ── Text output ─────────────────────────────────────────────
    
    def print_analysis(self, results=None):
        """Print formatted role classification."""
        if results is None:
            results = self.classify_all()
        
        print("\n" + "=" * 60)
        print("  PLAYER ROLE CLASSIFICATION")
        print("=" * 60)
        print(f"\n  Team: {self.team_name}")
        
        for r in results:
            print(f"\n  #{r['number']} {r['name']} ({r['position']})")
            print(f"    Role: {r['role']}  |  Confidence: {r['confidence']:.0%}")
            print(f"    Reasoning: {r['reasoning']}")
        
        print("\n" + "=" * 60)
    
    # ── Save ────────────────────────────────────────────────────
    
    def save(self, fig, filename):
        """Save figure to outputs folder."""
        fig.savefig(f"outputs/{filename}", dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved: outputs/{filename}")


# ═══════════════════════════════════════════════════════════════
# Quick test — El Clásico role classification
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    
    import os
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
    
    # Real Madrid
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
    
    # ── Barcelona ──
    rc_barca = RoleClassifier()
    rc_barca.set_team(barca, "FC Barcelona", "#a50044")
    
    results_barca = rc_barca.classify_all()
    rc_barca.print_analysis(results_barca)
    
    fig1, ax1 = rc_barca.draw(results_barca,
                               title="SpaceAI FC - Barcelona Player Roles")
    rc_barca.save(fig1, "roles_barca.png")
    
    # ── Real Madrid ──
    rc_madrid = RoleClassifier()
    rc_madrid.set_team(madrid, "Real Madrid", "#ffffff")
    
    results_madrid = rc_madrid.classify_all()
    rc_madrid.print_analysis(results_madrid)
    
    fig2, ax2 = rc_madrid.draw(results_madrid,
                                title="SpaceAI FC - Real Madrid Player Roles")
    rc_madrid.save(fig2, "roles_madrid.png")
    
    plt.show()
    print("\nRole classification complete!")
