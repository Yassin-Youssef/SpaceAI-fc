"""
SpaceAI FC - Tactical Pattern Detection
==========================================
Detects specific tactical patterns from player positions.
Identifies overlapping runs, compact blocks, wide overloads,
high defensive lines, and low blocks.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon
from mplsoccer import Pitch


class PatternDetector:
    """
    Detects tactical patterns from player positions.
    
    Patterns:
        - Overlapping runs: FB ahead of winger on same flank
        - Compact block: team compactness via convex hull / inter-player distance
        - Wide overload: numerical superiority in wide zones
        - High line: defensive line pushed high
        - Low block: team sitting very deep
    """
    
    def __init__(self):
        self.team_a = []
        self.team_b = []
        self.team_a_name = "Team A"
        self.team_b_name = "Team B"
        self.team_a_color = "#e74c3c"
        self.team_b_color = "#3498db"
    
    # ── Data input ──────────────────────────────────────────────
    
    def set_teams(self, team_a, team_b,
                  team_a_name="Team A", team_b_name="Team B",
                  team_a_color="#e74c3c", team_b_color="#3498db"):
        self.team_a = team_a
        self.team_b = team_b
        self.team_a_name = team_a_name
        self.team_b_name = team_b_name
        self.team_a_color = team_a_color
        self.team_b_color = team_b_color
    
    # ── Detection ───────────────────────────────────────────────
    
    def detect_all(self, team="a"):
        players = self.team_a if team == "a" else self.team_b
        opponent = self.team_b if team == "a" else self.team_a
        team_name = self.team_a_name if team == "a" else self.team_b_name
        
        patterns = []
        patterns.append(self._detect_overlapping_runs(players, team_name))
        patterns.append(self._detect_compact_block(players, team_name))
        patterns.extend(self._detect_wide_overload(players, opponent, team_name))
        patterns.append(self._detect_high_line(players, team_name))
        patterns.append(self._detect_low_block(players, team_name))
        
        return patterns
    
    def _get_team_side(self, players):
        avg_x = np.mean([p['x'] for p in players])
        return "left" if avg_x < 60 else "right"
    
    def _get_depth(self, x, side):
        return x if side == "left" else 120 - x
    
    def _detect_overlapping_runs(self, players, team_name):
        side = self._get_team_side(players)
        
        fullbacks = [p for p in players if p.get('position') in ('RB', 'LB', 'RWB', 'LWB')]
        wingers = [p for p in players if p.get('position') in ('RW', 'LW', 'RM', 'LM')]
        
        overlaps = []
        
        for fb in fullbacks:
            fb_side = "right" if fb['position'] in ('RB', 'RWB') else "left"
            fb_depth = self._get_depth(fb['x'], side)
            
            for w in wingers:
                w_side = "right" if w['position'] in ('RW', 'RM') else "left"
                w_depth = self._get_depth(w['x'], side)
                
                if fb_side != w_side:
                    continue
                
                # Check y-coordinates are on same side of pitch
                if fb_side == "right" and not (fb['y'] > 35 and w['y'] > 35):
                    continue
                if fb_side == "left" and not (fb['y'] < 45 and w['y'] < 45):
                    continue
                
                # Overlap: fullback at or ahead of winger in attacking depth
                depth_diff = fb_depth - w_depth
                if depth_diff > -5:  # FB within 5 units behind or ahead
                    overlaps.append((fb, w, fb_side, depth_diff))
        
        if overlaps:
            best = max(overlaps, key=lambda x: x[3])
            fb, w, flank, gap = best
            confidence = min(1.0, 0.4 + max(0, gap) / 15)
            
            if gap > 0:
                desc = (f"{fb['name']} ({fb['position']}) is positioned {gap:.0f} units "
                        f"ahead of {w['name']} ({w['position']}) on the {flank} flank — "
                        f"classic overlapping run creating width and a 2v1 opportunity")
            else:
                desc = (f"{fb['name']} ({fb['position']}) is pushing up alongside "
                        f"{w['name']} ({w['position']}) on the {flank} flank — "
                        f"creating overload potential on the wing")
            
            return {
                'pattern': 'Overlapping Run',
                'detected': True,
                'confidence': round(confidence, 2),
                'involved_players': [fb['name'], w['name']],
                'description': desc,
                '_flank': flank,
                '_fb': fb,
                '_winger': w,
            }
        
        return {
            'pattern': 'Overlapping Run',
            'detected': False,
            'confidence': 0.0,
            'involved_players': [],
            'description': f"No overlapping runs detected for {team_name}",
        }
    
    def _detect_compact_block(self, players, team_name):
        outfield = [p for p in players if p.get('position') != 'GK']
        
        if len(outfield) < 3:
            return {
                'pattern': 'Compact Block',
                'detected': False,
                'confidence': 0.0,
                'involved_players': [],
                'description': "Not enough players to assess compactness",
            }
        
        positions = np.array([[p['x'], p['y']] for p in outfield])
        
        from scipy.spatial.distance import pdist
        distances = pdist(positions)
        avg_dist = np.mean(distances)
        
        try:
            from scipy.spatial import ConvexHull
            hull = ConvexHull(positions)
            hull_area = hull.volume
        except Exception:
            hull_area = 999999
        
        # Relaxed thresholds
        compact_by_hull = hull_area < 2800
        compact_by_dist = avg_dist < 32
        
        detected = compact_by_hull or compact_by_dist
        
        if detected:
            confidence = 0.0
            if compact_by_hull:
                confidence += 0.5 * max(0, 1 - hull_area / 2800)
            if compact_by_dist:
                confidence += 0.5 * max(0, 1 - avg_dist / 32)
            confidence = min(1.0, confidence + 0.3)
            
            return {
                'pattern': 'Compact Block',
                'detected': True,
                'confidence': round(confidence, 2),
                'involved_players': [p['name'] for p in outfield],
                'description': (
                    f"{team_name} is in a compact shape — "
                    f"hull area: {hull_area:.0f} sq units, "
                    f"avg inter-player distance: {avg_dist:.1f} units. "
                    f"This makes it difficult for opponents to play through"
                ),
                '_hull_area': hull_area,
                '_avg_dist': avg_dist,
                '_positions': positions,
            }
        
        return {
            'pattern': 'Compact Block',
            'detected': False,
            'confidence': round(max(0, 1 - avg_dist / 40) * 0.3, 2),
            'involved_players': [],
            'description': (
                f"{team_name} is spread out — hull area: {hull_area:.0f}, "
                f"avg distance: {avg_dist:.1f}"
            ),
            '_hull_area': hull_area,
            '_avg_dist': avg_dist,
        }
    
    def _detect_wide_overload(self, players, opponent, team_name):
        results = []
        
        outfield = [p for p in players if p.get('position') != 'GK']
        opp_outfield = [p for p in opponent if p.get('position') != 'GK']
        
        zones = {
            'Left Wing': (0, 28),
            'Right Wing': (52, 80),
        }
        
        for zone_name, (y_min, y_max) in zones.items():
            team_count = sum(1 for p in outfield if y_min <= p['y'] <= y_max)
            opp_count = sum(1 for p in opp_outfield if y_min <= p['y'] <= y_max)
            
            advantage = team_count - opp_count
            
            # Relaxed: advantage >= 1 instead of 2
            if advantage >= 1 and team_count >= 2:
                involved = [p['name'] for p in outfield if y_min <= p['y'] <= y_max]
                confidence = min(1.0, 0.4 + advantage * 0.2)
                
                results.append({
                    'pattern': f'Wide Overload ({zone_name})',
                    'detected': True,
                    'confidence': round(confidence, 2),
                    'involved_players': involved,
                    'description': (
                        f"{team_name} has a {team_count}v{opp_count} advantage on the {zone_name} — "
                        f"creates numerical superiority for combinations"
                    ),
                    '_zone': zone_name,
                    '_team_count': team_count,
                    '_opp_count': opp_count,
                    '_y_range': (y_min, y_max),
                })
            else:
                results.append({
                    'pattern': f'Wide Overload ({zone_name})',
                    'detected': False,
                    'confidence': 0.0,
                    'involved_players': [],
                    'description': (
                        f"No overload on {zone_name}: {team_count} vs {opp_count}"
                    ),
                })
        
        return results
    
    def _detect_high_line(self, players, team_name):
        side = self._get_team_side(players)
        
        defenders = [p for p in players
                     if p.get('position') in ('CB', 'RB', 'LB', 'RWB', 'LWB')]
        
        if not defenders:
            return {
                'pattern': 'High Line',
                'detected': False,
                'confidence': 0.0,
                'involved_players': [],
                'description': "No defenders found",
            }
        
        depths = [self._get_depth(p['x'], side) for p in defenders]
        avg_depth = np.mean(depths)
        
        # High line: average defender depth > 25
        detected = avg_depth > 25
        
        if detected:
            confidence = min(1.0, 0.4 + (avg_depth - 25) / 25)
            return {
                'pattern': 'High Line',
                'detected': True,
                'confidence': round(confidence, 2),
                'involved_players': [p['name'] for p in defenders],
                'description': (
                    f"{team_name} is playing a high defensive line — "
                    f"avg defender depth: {avg_depth:.0f}. "
                    f"Pushes play into opponent's territory but vulnerable to balls over the top"
                ),
                '_avg_depth': avg_depth,
            }
        
        return {
            'pattern': 'High Line',
            'detected': False,
            'confidence': round(max(0, avg_depth / 25) * 0.3, 2),
            'involved_players': [],
            'description': (
                f"{team_name} defensive line at normal depth (avg: {avg_depth:.0f})"
            ),
            '_avg_depth': avg_depth,
        }
    
    def _detect_low_block(self, players, team_name):
        side = self._get_team_side(players)
        
        outfield = [p for p in players if p.get('position') != 'GK']
        
        if not outfield:
            return {
                'pattern': 'Low Block',
                'detected': False,
                'confidence': 0.0,
                'involved_players': [],
                'description': "No outfield players found",
            }
        
        depths = [self._get_depth(p['x'], side) for p in outfield]
        avg_depth = np.mean(depths)
        max_depth = max(depths)
        
        # Low block: avg outfield depth < 45 and max < 70
        detected = avg_depth < 45 and max_depth < 70
        
        if detected:
            confidence = min(1.0, 0.5 + (45 - avg_depth) / 25)
            return {
                'pattern': 'Low Block',
                'detected': True,
                'confidence': round(confidence, 2),
                'involved_players': [p['name'] for p in outfield],
                'description': (
                    f"{team_name} is sitting in a deep low block — "
                    f"avg outfield depth: {avg_depth:.0f}, deepest player at {max_depth:.0f}. "
                    f"Prioritising defensive solidity over attacking ambition"
                ),
                '_avg_depth': avg_depth,
            }
        
        return {
            'pattern': 'Low Block',
            'detected': False,
            'confidence': 0.0,
            'involved_players': [],
            'description': (
                f"{team_name} is not in a low block (avg depth: {avg_depth:.0f})"
            ),
        }
    
    # ── Summary ─────────────────────────────────────────────────
    
    def get_summary(self, team="a"):
        patterns = self.detect_all(team)
        team_name = self.team_a_name if team == "a" else self.team_b_name
        
        detected = [p for p in patterns if p['detected']]
        
        return {
            'team_name': team_name,
            'detected_patterns': detected,
            'all_patterns': patterns,
        }
    
    # ── Visualization ───────────────────────────────────────────
    
    def draw(self, team="a", figsize=(12, 8), title=None):
        players = self.team_a if team == "a" else self.team_b
        opponent = self.team_b if team == "a" else self.team_a
        team_name = self.team_a_name if team == "a" else self.team_b_name
        team_color = self.team_a_color if team == "a" else self.team_b_color
        
        patterns = self.detect_all(team)
        
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
        
        # Draw pattern highlights
        for pattern in patterns:
            if not pattern['detected']:
                continue
            
            pname = pattern['pattern']
            
            if pname == 'Overlapping Run' and '_fb' in pattern:
                fb = pattern['_fb']
                w = pattern['_winger']
                ax.annotate("",
                    xy=(fb['x'], fb['y']), xytext=(w['x'], w['y']),
                    arrowprops=dict(arrowstyle="-|>", color='#f1c40f',
                                   lw=3, alpha=0.8,
                                   connectionstyle="arc3,rad=0.3",
                                   mutation_scale=18),
                    zorder=8)
                ax.text((fb['x'] + w['x']) / 2,
                        (fb['y'] + w['y']) / 2 + 5,
                        "OVERLAP", ha='center', fontsize=7,
                        fontweight='bold', color='#f1c40f', zorder=9,
                        bbox=dict(boxstyle='round,pad=0.2',
                                  facecolor='#1a1a2e', alpha=0.8))
            
            elif pname == 'Compact Block' and '_positions' in pattern:
                try:
                    from scipy.spatial import ConvexHull
                    positions = pattern['_positions']
                    hull = ConvexHull(positions)
                    hull_pts = positions[hull.vertices]
                    hull_pts = np.vstack([hull_pts, hull_pts[0]])
                    ax.fill(hull_pts[:, 0], hull_pts[:, 1],
                            color='#3498db', alpha=0.12, zorder=1)
                    ax.plot(hull_pts[:, 0], hull_pts[:, 1],
                            color='#3498db', alpha=0.5, linestyle='--',
                            linewidth=1.5, zorder=2)
                    cx = np.mean(positions[:, 0])
                    cy = np.mean(positions[:, 1])
                    ax.text(cx, cy - 8, "COMPACT", ha='center',
                            fontsize=7, fontweight='bold', color='#3498db',
                            zorder=9, bbox=dict(boxstyle='round,pad=0.2',
                                                facecolor='#1a1a2e', alpha=0.8))
                except Exception:
                    pass
            
            elif 'Wide Overload' in pname and '_y_range' in pattern:
                y_min, y_max = pattern['_y_range']
                ax.axhspan(y_min, y_max, color='#e67e22', alpha=0.08, zorder=1)
                ax.text(60, (y_min + y_max) / 2,
                        f"OVERLOAD ({pattern['_team_count']}v{pattern['_opp_count']})",
                        ha='center', va='center', fontsize=8,
                        fontweight='bold', color='#e67e22', zorder=9,
                        bbox=dict(boxstyle='round,pad=0.2',
                                  facecolor='#1a1a2e', alpha=0.8))
            
            elif pname == 'High Line' and '_avg_depth' in pattern:
                side = self._get_team_side(players)
                if side == "left":
                    line_x = pattern['_avg_depth']
                else:
                    line_x = 120 - pattern['_avg_depth']
                ax.axvline(x=line_x, color='#e74c3c', linestyle='-.',
                           alpha=0.6, linewidth=2, zorder=3)
                ax.text(line_x, 83, "HIGH LINE", ha='center',
                        fontsize=7, fontweight='bold', color='#e74c3c',
                        zorder=9, bbox=dict(boxstyle='round,pad=0.2',
                                            facecolor='#1a1a2e', alpha=0.8))
            
            elif pname == 'Low Block' and '_avg_depth' in pattern:
                side = self._get_team_side(players)
                if side == "left":
                    block_x = pattern['_avg_depth']
                    ax.axvspan(0, block_x + 10, color='#9b59b6', alpha=0.08, zorder=1)
                else:
                    block_x = 120 - pattern['_avg_depth']
                    ax.axvspan(block_x - 10, 120, color='#9b59b6', alpha=0.08, zorder=1)
                ax.text(block_x if side == "left" else block_x,
                        -3, "LOW BLOCK", ha='center',
                        fontsize=7, fontweight='bold', color='#9b59b6',
                        zorder=9, bbox=dict(boxstyle='round,pad=0.2',
                                            facecolor='#1a1a2e', alpha=0.8))
        
        # Draw team players
        for p in players:
            ax.scatter(p['x'], p['y'], c=team_color, s=300,
                       edgecolors='white', linewidths=2, zorder=6, alpha=0.95)
            ax.annotate(str(p['number']), xy=(p['x'], p['y']),
                        ha='center', va='center', fontsize=8,
                        fontweight='bold', color='white', zorder=7)
            ax.annotate(p['name'], xy=(p['x'], p['y'] + 3),
                        ha='center', va='bottom', fontsize=7,
                        color='white', zorder=7, alpha=0.85)
        
        # Draw opponent (faded)
        opp_color = self.team_b_color if team == "a" else self.team_a_color
        for p in opponent:
            ax.scatter(p['x'], p['y'], c=opp_color, s=150,
                       edgecolors='#888888', linewidths=1, zorder=4, alpha=0.35)
            ax.annotate(str(p['number']), xy=(p['x'], p['y']),
                        ha='center', va='center', fontsize=6,
                        color='#888888', zorder=5)
        
        # Pattern count label
        detected = [p for p in patterns if p['detected']]
        info = f"{team_name}: {len(detected)} pattern(s) detected"
        ax.text(60, -5, info, ha='center', va='top', fontsize=10,
                color='white', fontweight='bold', zorder=10,
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#2a2a3e',
                          edgecolor='#444444', alpha=0.9))
        
        return fig, ax
    
    # ── Text output ─────────────────────────────────────────────
    
    def print_analysis(self, team="a"):
        summary = self.get_summary(team)
        
        print("\n" + "=" * 60)
        print("  TACTICAL PATTERN DETECTION")
        print("=" * 60)
        print(f"\n  Team: {summary['team_name']}")
        
        for p in summary['all_patterns']:
            status = "DETECTED" if p['detected'] else "not detected"
            emoji = "+" if p['detected'] else "-"
            print(f"\n  [{emoji}] {p['pattern']} — {status}")
            if p['detected']:
                print(f"      Confidence: {p['confidence']:.0%}")
                if p['involved_players']:
                    print(f"      Players: {', '.join(p['involved_players'][:5])}")
                print(f"      {p['description']}")
        
        detected = summary['detected_patterns']
        print(f"\n  Summary: {len(detected)} pattern(s) detected")
        print("=" * 60)
    
    # ── Save ────────────────────────────────────────────────────
    
    def save(self, fig, filename):
        fig.savefig(f"outputs/{filename}", dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved: outputs/{filename}")


# ═══════════════════════════════════════════════════════════════
# Quick test — El Clásico tactical patterns
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    
    import os
    os.makedirs("outputs", exist_ok=True)
    
    # Barcelona 4-2-3-1 — Koundé pushed high into overlap
    barca = [
        {'name': 'ter Stegen',  'number': 1,  'x': 5,  'y': 40, 'position': 'GK'},
        {'name': 'Koundé',      'number': 23, 'x': 68, 'y': 72, 'position': 'RB'},
        {'name': 'Araújo',      'number': 4,  'x': 35, 'y': 52, 'position': 'CB'},
        {'name': 'Cubarsí',     'number': 2,  'x': 35, 'y': 28, 'position': 'CB'},
        {'name': 'Baldé',       'number': 3,  'x': 30, 'y': 10, 'position': 'LB'},
        {'name': 'Pedri',       'number': 8,  'x': 50, 'y': 48, 'position': 'CM'},
        {'name': 'De Jong',     'number': 21, 'x': 48, 'y': 32, 'position': 'CM'},
        {'name': 'Lamine',      'number': 19, 'x': 65, 'y': 68, 'position': 'RW'},
        {'name': 'Gavi',        'number': 6,  'x': 62, 'y': 40, 'position': 'CAM'},
        {'name': 'Raphinha',    'number': 11, 'x': 65, 'y': 12, 'position': 'LW'},
        {'name': 'Lewandowski', 'number': 9,  'x': 78, 'y': 40, 'position': 'ST'},
    ]
    
    # Real Madrid — compact defensive shape
    madrid = [
        {'name': 'Courtois',    'number': 1,  'x': 115, 'y': 40, 'position': 'GK'},
        {'name': 'Carvajal',    'number': 2,  'x': 88,  'y': 65, 'position': 'RB'},
        {'name': 'Rüdiger',     'number': 22, 'x': 90,  'y': 48, 'position': 'CB'},
        {'name': 'Militão',     'number': 3,  'x': 90,  'y': 32, 'position': 'CB'},
        {'name': 'Mendy',       'number': 23, 'x': 88,  'y': 15, 'position': 'LB'},
        {'name': 'Tchouaméni',  'number': 14, 'x': 80,  'y': 40, 'position': 'CDM'},
        {'name': 'Valverde',    'number': 15, 'x': 78,  'y': 55, 'position': 'CM'},
        {'name': 'Bellingham',  'number': 5,  'x': 78,  'y': 25, 'position': 'CM'},
        {'name': 'Rodrygo',     'number': 11, 'x': 72,  'y': 60, 'position': 'RW'},
        {'name': 'Mbappé',      'number': 7,  'x': 70,  'y': 40, 'position': 'ST'},
        {'name': 'Vinícius',    'number': 20, 'x': 72,  'y': 20, 'position': 'LW'},
    ]
    
    pd = PatternDetector()
    pd.set_teams(barca, madrid,
                 team_a_name="FC Barcelona", team_b_name="Real Madrid",
                 team_a_color="#a50044", team_b_color="#ffffff")
    
    # Barcelona patterns
    pd.print_analysis(team="a")
    fig1, ax1 = pd.draw(team="a",
                         title="SpaceAI FC - Barcelona Tactical Patterns")
    pd.save(fig1, "patterns_barca.png")
    
    # Real Madrid patterns
    pd.print_analysis(team="b")
    fig2, ax2 = pd.draw(team="b",
                         title="SpaceAI FC - Real Madrid Tactical Patterns")
    pd.save(fig2, "patterns_madrid.png")
    
    plt.show()
    print("\nTactical pattern detection complete!")