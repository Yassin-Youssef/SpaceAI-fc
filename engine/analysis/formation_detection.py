"""
SpaceAI FC - Formation Detection
==================================
Detects team formations from player positions using clustering
and gap-based methods. Identifies defensive, midfield, and
attacking lines and outputs a formation string (e.g. "4-3-3").
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from mplsoccer import Pitch

try:
    from sklearn.cluster import KMeans, AgglomerativeClustering
    from sklearn.metrics import silhouette_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class FormationDetector:
    """
    Detects team formation from player positions.
    
    Two approaches:
        - Clustering: K-Means / Agglomerative on x-coordinates (preferred)
        - Gap-based: sort by x, detect natural gaps, count per line (fallback)
    
    Handles teams on either side of the pitch:
        - avg_x < 60: left-side team (defense reads left-to-right)
        - avg_x > 60: right-side team (reverse line order)
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
            players: list of dicts with 'name', 'number', 'x', 'y', 'position'
            team_name: display name
            team_color: hex color
        """
        self.players = players
        self.team_name = team_name
        self.team_color = team_color
    
    # ── Core detection ──────────────────────────────────────────
    
    def detect(self, method="auto"):
        """
        Detect formation.
        
        Parameters:
            method: "clustering", "gap", or "auto" (clustering if sklearn available)
        
        Returns:
            dict with:
                'formation': string like "4-3-3"
                'confidence': float 0-1
                'lines': list of lists (players grouped by line, defense first)
                'method': which method was used
        """
        if method == "auto":
            method = "clustering" if HAS_SKLEARN else "gap"
        
        if method == "clustering":
            return self._detect_clustering()
        else:
            return self._detect_gap()
    
    def _detect_clustering(self):
        """Formation detection using scikit-learn clustering."""
        outfield = [p for p in self.players if p.get('position') != 'GK']
        
        if len(outfield) < 3:
            return {'formation': 'Unknown', 'confidence': 0.0,
                    'lines': [], 'method': 'clustering'}
        
        x_values = np.array([p['x'] for p in outfield]).reshape(-1, 1)
        avg_x = np.mean(x_values)
        
        best_score = -1
        best_k = 3
        best_labels = None
        
        # Try k = 2, 3, 4 lines
        for k in [2, 3, 4]:
            if k >= len(outfield):
                continue
            
            # K-Means
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels_km = km.fit_predict(x_values)
            score_km = silhouette_score(x_values, labels_km) if k < len(outfield) else -1
            
            # Agglomerative
            ag = AgglomerativeClustering(n_clusters=k)
            labels_ag = ag.fit_predict(x_values)
            score_ag = silhouette_score(x_values, labels_ag) if k < len(outfield) else -1
            
            # Pick the better of the two for this k
            if score_km >= score_ag:
                score, labels = score_km, labels_km
            else:
                score, labels = score_ag, labels_ag
            
            if score > best_score:
                best_score = score
                best_k = k
                best_labels = labels
        
        # Group players by cluster, ordered by mean x of cluster
        cluster_groups = {}
        for i, player in enumerate(outfield):
            label = best_labels[i]
            if label not in cluster_groups:
                cluster_groups[label] = []
            cluster_groups[label].append(player)
        
        # Sort clusters by mean x position
        sorted_clusters = sorted(
            cluster_groups.values(),
            key=lambda group: np.mean([p['x'] for p in group])
        )
        
        # If right-side team, reverse so defense comes first
        if avg_x > 60:
            sorted_clusters = list(reversed(sorted_clusters))
        
        # Build formation string
        line_counts = [len(group) for group in sorted_clusters]
        
        # Validate: must sum to number of outfield players
        if sum(line_counts) != len(outfield):
            return self._detect_gap()  # fallback
        
        formation_str = "-".join(str(c) for c in line_counts)
        
        # Confidence based on silhouette score (0 to 1 range, but silhouette is -1 to 1)
        confidence = round(max(0.0, min(1.0, (best_score + 1) / 2)), 2)
        
        # Boost confidence for common formations
        common_formations = [
            "4-3-3", "4-4-2", "4-2-3-1", "3-5-2", "3-4-3",
            "4-1-4-1", "4-1-2-3", "5-3-2", "5-4-1", "4-5-1",
        ]
        if formation_str in common_formations:
            confidence = min(1.0, confidence + 0.15)
        
        return {
            'formation': formation_str,
            'confidence': round(confidence, 2),
            'lines': sorted_clusters,
            'method': 'clustering',
        }
    
    def _detect_gap(self):
        """Formation detection using gap-based splitting."""
        outfield = [p for p in self.players if p.get('position') != 'GK']
        
        if not outfield:
            return {'formation': 'Unknown', 'confidence': 0.0,
                    'lines': [], 'method': 'gap'}
        
        sorted_players = sorted(outfield, key=lambda p: p['x'])
        x_positions = [p['x'] for p in sorted_players]
        avg_x = sum(x_positions) / len(x_positions)
        
        # Compute gaps between consecutive players
        gaps = []
        for i in range(1, len(x_positions)):
            gaps.append((x_positions[i] - x_positions[i - 1], i))
        
        gaps.sort(reverse=True)
        
        # Try 3 splits (4 lines like 4-2-3-1), then 2 splits (3 lines like 4-3-3)
        for num_splits in [3, 2]:
            if len(gaps) >= num_splits:
                split_indices = sorted([idx for _, idx in gaps[:num_splits]])
                
                lines = []
                prev = 0
                for sp in split_indices:
                    lines.append(sorted_players[prev:sp])
                    prev = sp
                lines.append(sorted_players[prev:])
                
                line_counts = [len(line) for line in lines]
                
                if all(1 <= l <= 5 for l in line_counts) and sum(line_counts) == len(outfield):
                    if avg_x > 60:
                        lines.reverse()
                        line_counts.reverse()
                    
                    formation_str = "-".join(str(c) for c in line_counts)
                    confidence = 0.6  # gap-based has moderate confidence
                    
                    common = ["4-3-3", "4-4-2", "4-2-3-1", "3-5-2", "3-4-3",
                              "4-1-4-1", "5-3-2", "5-4-1"]
                    if formation_str in common:
                        confidence = 0.75
                    
                    return {
                        'formation': formation_str,
                        'confidence': confidence,
                        'lines': lines,
                        'method': 'gap',
                    }
        
        # Fallback: just try 2 splits
        if len(gaps) >= 2:
            split_indices = sorted([idx for _, idx in gaps[:2]])
            lines = []
            prev = 0
            for sp in split_indices:
                lines.append(sorted_players[prev:sp])
                prev = sp
            lines.append(sorted_players[prev:])
            
            line_counts = [len(line) for line in lines]
            if avg_x > 60:
                lines.reverse()
                line_counts.reverse()
            
            return {
                'formation': "-".join(str(c) for c in line_counts),
                'confidence': 0.4,
                'lines': lines,
                'method': 'gap',
            }
        
        return {'formation': 'Unknown', 'confidence': 0.0,
                'lines': [outfield], 'method': 'gap'}
    
    # ── Temporal analysis ───────────────────────────────────────
    
    def detect_changes(self, frames, method="auto"):
        """
        Detect formation changes over multiple frames.
        
        Parameters:
            frames: list of player lists (each frame is a list of player dicts)
            method: detection method to use
        
        Returns:
            list of dicts, one per frame, with formation info + 'changed' flag
        """
        results = []
        prev_formation = None
        
        for i, frame_players in enumerate(frames):
            self.players = frame_players
            result = self.detect(method=method)
            result['frame'] = i
            result['changed'] = (result['formation'] != prev_formation) if prev_formation else False
            results.append(result)
            prev_formation = result['formation']
        
        return results
    
    # ── Visualization ───────────────────────────────────────────
    
    def draw(self, result=None, figsize=(12, 8), title=None):
        """
        Draw the detected formation with line overlays.
        
        Parameters:
            result: output from detect(). If None, calls detect() internally.
            figsize: figure size
            title: optional title
        
        Returns:
            fig, ax
        """
        if result is None:
            result = self.detect()
        
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
        
        # Color palette for lines (defense, midfield, attack)
        line_colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c']
        
        lines = result.get('lines', [])
        
        for line_idx, line_players in enumerate(lines):
            if not line_players:
                continue
            
            color = line_colors[line_idx % len(line_colors)]
            rgba = to_rgba(color, alpha=0.15)
            
            # Draw a vertical band showing the line zone
            x_positions = [p['x'] for p in line_players]
            x_min = min(x_positions) - 5
            x_max = max(x_positions) + 5
            
            ax.axvspan(x_min, x_max, alpha=0.12, color=color, zorder=1)
            
            # Draw a vertical line at the mean x
            mean_x = np.mean(x_positions)
            ax.axvline(x=mean_x, color=color, linestyle='--',
                       alpha=0.5, linewidth=1.5, zorder=2)
            
            # Line label
            line_labels = ['DEF', 'MID', 'MID2', 'ATT']
            if len(lines) == 2:
                line_labels = ['DEF', 'ATT']
            elif len(lines) == 3:
                line_labels = ['DEF', 'MID', 'ATT']
            elif len(lines) == 4:
                line_labels = ['DEF', 'DM', 'AM', 'ATT']
            
            label = line_labels[line_idx] if line_idx < len(line_labels) else f'L{line_idx+1}'
            ax.text(mean_x, -3, label, ha='center', va='top',
                    color=color, fontsize=9, fontweight='bold', zorder=10)
            
            # Draw players in this line
            for p in line_players:
                ax.scatter(p['x'], p['y'], c=self.team_color, s=300,
                           edgecolors=color, linewidths=2.5, zorder=6, alpha=0.95)
                ax.annotate(str(p['number']), xy=(p['x'], p['y']),
                            ha='center', va='center', fontsize=8,
                            fontweight='bold', color='white', zorder=7)
                ax.annotate(p['name'], xy=(p['x'], p['y'] + 3),
                            ha='center', va='bottom', fontsize=7,
                            color='white', zorder=7, alpha=0.85)
        
        # Draw GK separately
        for p in self.players:
            if p.get('position') == 'GK':
                ax.scatter(p['x'], p['y'], c=self.team_color, s=300,
                           edgecolors='#888888', linewidths=2.5, zorder=6, alpha=0.95)
                ax.annotate(str(p['number']), xy=(p['x'], p['y']),
                            ha='center', va='center', fontsize=8,
                            fontweight='bold', color='white', zorder=7)
                ax.annotate(p['name'], xy=(p['x'], p['y'] + 3),
                            ha='center', va='bottom', fontsize=7,
                            color='white', zorder=7, alpha=0.85)
        
        # Formation label
        formation = result.get('formation', 'Unknown')
        confidence = result.get('confidence', 0)
        method = result.get('method', '')
        
        info_text = (f"{self.team_name}: {formation}  |  "
                     f"Confidence: {confidence:.0%}  |  Method: {method}")
        ax.text(60, 83, info_text, ha='center', va='bottom',
                color='white', fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#2a2a3e',
                          edgecolor='#444444', alpha=0.9), zorder=10)
        
        return fig, ax
    
    # ── Text output ─────────────────────────────────────────────
    
    def print_analysis(self, result=None):
        """Print formatted formation analysis."""
        if result is None:
            result = self.detect()
        
        print("\n" + "=" * 55)
        print("  FORMATION DETECTION")
        print("=" * 55)
        
        print(f"\n  Team: {self.team_name}")
        print(f"  Formation: {result['formation']}")
        print(f"  Confidence: {result['confidence']:.0%}")
        print(f"  Method: {result['method']}")
        
        lines = result.get('lines', [])
        line_labels = ['DEF', 'MID', 'MID2', 'ATT']
        if len(lines) == 2:
            line_labels = ['DEF', 'ATT']
        elif len(lines) == 3:
            line_labels = ['DEF', 'MID', 'ATT']
        elif len(lines) == 4:
            line_labels = ['DEF', 'DM', 'AM', 'ATT']
        
        for i, line_players in enumerate(lines):
            label = line_labels[i] if i < len(line_labels) else f'Line {i+1}'
            names = ", ".join(p['name'] for p in line_players)
            avg_x = np.mean([p['x'] for p in line_players])
            print(f"\n  {label} (avg x={avg_x:.0f}):")
            print(f"    {names}")
        
        print("\n" + "=" * 55)
    
    # ── Save ────────────────────────────────────────────────────
    
    def save(self, fig, filename):
        """Save figure to outputs folder."""
        fig.savefig(f"outputs/{filename}", dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved: outputs/{filename}")


# ═══════════════════════════════════════════════════════════════
# Quick test — El Clásico formation detection
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
    
    # Real Madrid 4-3-3
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
    fd_barca = FormationDetector()
    fd_barca.set_team(barca, "FC Barcelona", "#a50044")
    
    result_barca = fd_barca.detect()
    fd_barca.print_analysis(result_barca)
    
    fig1, ax1 = fd_barca.draw(
        result_barca,
        title="SpaceAI FC - Barcelona Formation Detection"
    )
    fd_barca.save(fig1, "formation_barca.png")
    
    # ── Real Madrid ──
    fd_madrid = FormationDetector()
    fd_madrid.set_team(madrid, "Real Madrid", "#ffffff")
    
    result_madrid = fd_madrid.detect()
    fd_madrid.print_analysis(result_madrid)
    
    fig2, ax2 = fd_madrid.draw(
        result_madrid,
        title="SpaceAI FC - Real Madrid Formation Detection"
    )
    fd_madrid.save(fig2, "formation_madrid.png")
    
    # ── Temporal test (simulated formation shift) ──
    print("\n" + "=" * 55)
    print("  FORMATION CHANGE DETECTION")
    print("=" * 55)
    
    # Frame 2: Barça pushes Pedri forward → becomes more like 4-1-3-2
    barca_frame2 = [p.copy() for p in barca]
    for p in barca_frame2:
        if p['name'] == 'Pedri':
            p['x'] = 62  # pushed forward
        if p['name'] == 'De Jong':
            p['x'] = 40  # drops deeper
    
    fd_barca_temporal = FormationDetector()
    fd_barca_temporal.set_team(barca, "FC Barcelona", "#a50044")
    
    changes = fd_barca_temporal.detect_changes([barca, barca_frame2])
    for c in changes:
        changed = "⚠ CHANGED" if c['changed'] else "same"
        print(f"  Frame {c['frame']}: {c['formation']} (conf: {c['confidence']:.0%}) [{changed}]")
    
    print("\n" + "=" * 55)
    
    plt.show()
    print("\nFormation detection complete!")
