"""
SpaceAI FC - Multi-Agent Tactical Simulation
==============================================
Phase 4 Module 3: Simulate tactical scenarios with player agents.

Supports 5v5 or 7v7 simplified pitch simulations with rule-based
player agents. Compare different tactical presets and visualize results.

Dependencies: matplotlib only (already installed).
"""

import os
import sys
import math
import random
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import FancyBboxPatch, Circle

try:
    from mplsoccer import Pitch
    HAS_MPLSOCCER = True
except ImportError:
    HAS_MPLSOCCER = False


# ════════════════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════════════════

TACTICAL_PRESETS = {
    'high_press': {
        'name': 'High Press',
        'def_line': 0.55, 'press_intensity': 0.9, 'width': 0.7,
        'tempo': 0.8, 'directness': 0.7, 'compactness': 0.6,
    },
    'low_block': {
        'name': 'Low Block',
        'def_line': 0.25, 'press_intensity': 0.3, 'width': 0.5,
        'tempo': 0.4, 'directness': 0.3, 'compactness': 0.9,
    },
    'wide_play': {
        'name': 'Wide Play',
        'def_line': 0.40, 'press_intensity': 0.5, 'width': 0.95,
        'tempo': 0.6, 'directness': 0.5, 'compactness': 0.4,
    },
    'narrow_play': {
        'name': 'Narrow Play',
        'def_line': 0.40, 'press_intensity': 0.6, 'width': 0.35,
        'tempo': 0.5, 'directness': 0.4, 'compactness': 0.85,
    },
    'counter_attack': {
        'name': 'Counter-Attack',
        'def_line': 0.30, 'press_intensity': 0.4, 'width': 0.6,
        'tempo': 0.9, 'directness': 0.9, 'compactness': 0.7,
    },
    'possession': {
        'name': 'Possession',
        'def_line': 0.45, 'press_intensity': 0.6, 'width': 0.7,
        'tempo': 0.3, 'directness': 0.2, 'compactness': 0.5,
    },
}


# ════════════════════════════════════════════════════════════════
# Player Agent
# ════════════════════════════════════════════════════════════════

class PlayerAgent:
    """A single player agent with position, role, and movement logic."""

    def __init__(self, pid, x, y, role, team, speed=1.0):
        self.pid = pid
        self.x = x
        self.y = y
        self.home_x = x
        self.home_y = y
        self.role = role   # 'GK', 'DEF', 'MID', 'ATT'
        self.team = team   # 'A' or 'B'
        self.speed = speed
        self.has_ball = False
        self.vx = 0.0
        self.vy = 0.0

    def update(self, ball, teammates, opponents, tactic, pitch_w, pitch_h, rng):
        """Move toward tactical objective based on role and tactic."""
        goal_x = pitch_w if self.team == 'A' else 0
        own_goal_x = 0 if self.team == 'A' else pitch_w
        attack_dir = 1 if self.team == 'A' else -1

        target_x, target_y = self.x, self.y

        if self.role == 'GK':
            target_x = own_goal_x + attack_dir * 3
            target_y = pitch_h / 2 + (ball.y - pitch_h / 2) * 0.3
        elif self.role == 'DEF':
            line_x = own_goal_x + attack_dir * tactic['def_line'] * pitch_w
            target_x = line_x + rng.normal(0, 1)
            opp_near = self._nearest(opponents)
            if opp_near and abs(opp_near.x - self.x) < pitch_w * 0.2:
                target_y = opp_near.y + (self.home_y - opp_near.y) * 0.3
            else:
                target_y = self.home_y + (ball.y - self.home_y) * 0.2
        elif self.role == 'MID':
            mid_x = own_goal_x + attack_dir * (tactic['def_line'] + 0.2) * pitch_w
            target_x = mid_x + attack_dir * tactic['tempo'] * 3
            spread = tactic['width'] * pitch_h * 0.4
            target_y = self.home_y + (ball.y - self.home_y) * 0.35
            target_y += rng.normal(0, spread * 0.1)
        elif self.role == 'ATT':
            att_x = own_goal_x + attack_dir * max(tactic['def_line'] + 0.3, 0.6) * pitch_w
            target_x = att_x + attack_dir * tactic['directness'] * 5
            target_y = self.home_y + (ball.y - self.home_y) * 0.4
            spread = tactic['width'] * pitch_h * 0.3
            target_y += rng.normal(0, spread * 0.15)

        # Move toward target
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx**2 + dy**2) + 1e-6
        move_speed = self.speed * (0.5 + tactic['tempo'] * 0.5) * 0.6

        self.vx = dx / dist * min(move_speed, dist) + rng.normal(0, 0.15)
        self.vy = dy / dist * min(move_speed, dist) + rng.normal(0, 0.15)
        self.x = max(0.5, min(pitch_w - 0.5, self.x + self.vx))
        self.y = max(0.5, min(pitch_h - 0.5, self.y + self.vy))

    def _nearest(self, others):
        best, best_d = None, float('inf')
        for o in others:
            d = math.sqrt((o.x - self.x)**2 + (o.y - self.y)**2)
            if d < best_d:
                best, best_d = o, d
        return best

    def dist_to(self, ox, oy):
        return math.sqrt((self.x - ox)**2 + (self.y - oy)**2)


# ════════════════════════════════════════════════════════════════
# Ball
# ════════════════════════════════════════════════════════════════

class Ball:
    """Simple ball with possession and passing logic."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.possessor = None  # PlayerAgent or None

    def update(self, team_a, team_b, pitch_w, pitch_h, rng):
        if self.possessor:
            p = self.possessor
            self.x, self.y = p.x, p.y

            # Decision: pass, shoot, or dribble
            if self._should_shoot(p, pitch_w):
                self._shoot(p, team_a, team_b, pitch_w, pitch_h, rng)
            elif rng.random() < 0.15:
                self._pass(p, team_a if p.team == 'A' else team_b, rng, pitch_w, pitch_h)
            # else dribble (ball follows possessor)
        else:
            # Loose ball — nearest player wins
            all_p = team_a + team_b
            nearest = min(all_p, key=lambda p: p.dist_to(self.x, self.y))
            if nearest.dist_to(self.x, self.y) < 2.0:
                self.possessor = nearest

    def _should_shoot(self, player, pitch_w):
        goal_x = pitch_w if player.team == 'A' else 0
        return abs(player.x - goal_x) < pitch_w * 0.2 and player.role in ('ATT', 'MID')

    def _shoot(self, player, team_a, team_b, pitch_w, pitch_h, rng):
        goal_x = pitch_w if player.team == 'A' else 0
        dist = abs(player.x - goal_x)
        prob = max(0.02, 0.15 - dist / pitch_w * 0.2)

        if rng.random() < prob:
            self.possessor = None
            self.x = goal_x
            self.y = pitch_h / 2
            return 'goal'
        else:
            # Saved / missed — give to defending GK
            defenders = team_b if player.team == 'A' else team_a
            gk = next((p for p in defenders if p.role == 'GK'), defenders[0])
            self.possessor = gk
            return 'save'

    def _pass(self, passer, teammates, rng, pitch_w, pitch_h):
        others = [t for t in teammates if t.pid != passer.pid]
        if not others:
            return
        target = rng.choice(others)
        success = rng.random() < 0.75
        if success:
            self.possessor = target
            self.x, self.y = target.x, target.y
        else:
            self.possessor = None
            self.x += rng.normal(0, 3)
            self.y += rng.normal(0, 3)
            self.x = max(0, min(pitch_w, self.x))
            self.y = max(0, min(pitch_h, self.y))


# ════════════════════════════════════════════════════════════════
# Tactical Simulation
# ════════════════════════════════════════════════════════════════

class TacticalSimulation:
    """
    Simulate a tactical scenario with player agents.
    Supports 5v5 or 7v7 on a simplified pitch.
    """

    def __init__(self, team_size=5, max_steps=1000, seed=42):
        self.team_size = team_size
        self.max_steps = max_steps
        self.rng = np.random.RandomState(seed)

        if team_size <= 5:
            self.pitch_w, self.pitch_h = 60, 40
        else:
            self.pitch_w, self.pitch_h = 80, 50

        self.team_a = []
        self.team_b = []
        self.ball = None
        self.tactic_a = TACTICAL_PRESETS['possession']
        self.tactic_b = TACTICAL_PRESETS['low_block']
        self.history = []
        self.events = []
        self.goals_a = 0
        self.goals_b = 0

    def _create_team(self, team_id, side):
        """Create players in a balanced formation."""
        pw, ph = self.pitch_w, self.pitch_h
        players = []
        if self.team_size == 5:
            # 1-2-1-1 (GK, 2 DEF, 1 MID, 1 ATT)
            roles = ['GK', 'DEF', 'DEF', 'MID', 'ATT']
            if side == 'A':
                positions = [(2, ph/2), (pw*0.2, ph*0.3), (pw*0.2, ph*0.7),
                             (pw*0.4, ph/2), (pw*0.6, ph/2)]
            else:
                positions = [(pw-2, ph/2), (pw*0.8, ph*0.3), (pw*0.8, ph*0.7),
                             (pw*0.6, ph/2), (pw*0.4, ph/2)]
        else:
            # 1-2-2-2 for 7v7
            roles = ['GK', 'DEF', 'DEF', 'MID', 'MID', 'ATT', 'ATT']
            if side == 'A':
                positions = [(2, ph/2), (pw*0.2, ph*0.3), (pw*0.2, ph*0.7),
                             (pw*0.4, ph*0.35), (pw*0.4, ph*0.65),
                             (pw*0.6, ph*0.3), (pw*0.6, ph*0.7)]
            else:
                positions = [(pw-2, ph/2), (pw*0.8, ph*0.3), (pw*0.8, ph*0.7),
                             (pw*0.6, ph*0.35), (pw*0.6, ph*0.65),
                             (pw*0.4, ph*0.3), (pw*0.4, ph*0.7)]

        for i, (role, (x, y)) in enumerate(zip(roles, positions)):
            pid = i if side == 'A' else self.team_size + i
            speed = 0.8 if role == 'GK' else (1.0 if role == 'DEF' else 1.1 if role == 'MID' else 1.2)
            players.append(PlayerAgent(pid, x, y, role, side, speed))
        return players

    def set_tactics(self, tactic_a_key, tactic_b_key):
        """Set tactical presets by key name."""
        self.tactic_a = TACTICAL_PRESETS.get(tactic_a_key, TACTICAL_PRESETS['possession'])
        self.tactic_b = TACTICAL_PRESETS.get(tactic_b_key, TACTICAL_PRESETS['low_block'])

    def reset(self):
        """Reset simulation to initial state."""
        self.team_a = self._create_team('A', 'A')
        self.team_b = self._create_team('B', 'B')
        self.ball = Ball(self.pitch_w / 2, self.pitch_h / 2)
        self.ball.possessor = self.rng.choice(self.team_a[1:])
        self.history = []
        self.events = []
        self.goals_a = 0
        self.goals_b = 0

    def run(self, n_steps=300):
        """Run simulation for n_steps."""
        n_steps = min(n_steps, self.max_steps)
        self.reset()

        for step in range(n_steps):
            # Update players
            for p in self.team_a:
                p.update(self.ball, self.team_a, self.team_b,
                         self.tactic_a, self.pitch_w, self.pitch_h, self.rng)
            for p in self.team_b:
                p.update(self.ball, self.team_b, self.team_a,
                         self.tactic_b, self.pitch_w, self.pitch_h, self.rng)

            # Update ball
            prev_x = self.ball.x
            self.ball.update(self.team_a, self.team_b,
                             self.pitch_w, self.pitch_h, self.rng)

            # Check for goals
            if self.ball.x >= self.pitch_w - 0.5 and prev_x < self.pitch_w - 0.5:
                if abs(self.ball.y - self.pitch_h / 2) < self.pitch_h * 0.2:
                    self.goals_a += 1
                    self.events.append({'step': step, 'type': 'goal', 'team': 'A'})
                    self._reset_positions()
            elif self.ball.x <= 0.5 and prev_x > 0.5:
                if abs(self.ball.y - self.pitch_h / 2) < self.pitch_h * 0.2:
                    self.goals_b += 1
                    self.events.append({'step': step, 'type': 'goal', 'team': 'B'})
                    self._reset_positions()

            # Record state
            self.history.append({
                'step': step,
                'team_a': [{'pid': p.pid, 'x': p.x, 'y': p.y, 'role': p.role} for p in self.team_a],
                'team_b': [{'pid': p.pid, 'x': p.x, 'y': p.y, 'role': p.role} for p in self.team_b],
                'ball': {'x': self.ball.x, 'y': self.ball.y},
                'possession': self.ball.possessor.team if self.ball.possessor else None,
            })

        return self.get_stats()

    def _reset_positions(self):
        """Reset to kick-off after a goal."""
        for p in self.team_a:
            p.x, p.y = p.home_x, p.home_y
        for p in self.team_b:
            p.x, p.y = p.home_x, p.home_y
        self.ball.x, self.ball.y = self.pitch_w / 2, self.pitch_h / 2
        self.ball.possessor = self.rng.choice(self.team_b[1:] if self.goals_a > self.goals_b else self.team_a[1:])

    def get_stats(self):
        """Compute simulation statistics."""
        if not self.history:
            return {}

        poss_a = sum(1 for h in self.history if h['possession'] == 'A')
        poss_b = sum(1 for h in self.history if h['possession'] == 'B')
        total_poss = max(poss_a + poss_b, 1)

        # Territorial control: avg ball x position
        avg_ball_x = np.mean([h['ball']['x'] for h in self.history])
        terr_a = avg_ball_x / self.pitch_w * 100

        # Average team positions
        avg_a_x = np.mean([np.mean([p['x'] for p in h['team_a']]) for h in self.history])
        avg_b_x = np.mean([np.mean([p['x'] for p in h['team_b']]) for h in self.history])

        return {
            'tactic_a': self.tactic_a['name'],
            'tactic_b': self.tactic_b['name'],
            'goals_a': self.goals_a,
            'goals_b': self.goals_b,
            'possession_a': round(poss_a / total_poss * 100, 1),
            'possession_b': round(poss_b / total_poss * 100, 1),
            'territorial_control_a': round(terr_a, 1),
            'territorial_control_b': round(100 - terr_a, 1),
            'avg_position_a': round(avg_a_x, 1),
            'avg_position_b': round(avg_b_x, 1),
            'total_steps': len(self.history),
            'events': self.events,
            'team_size': self.team_size,
        }

    # ── Comparison Mode ────────────────────────────────────────

    def compare_tactics(self, tactic_a_key, tactic_b_key, n_runs=5,
                        n_steps=300):
        """Run multiple simulations and aggregate results."""
        results = {'runs': [], 'tactic_a': TACTICAL_PRESETS[tactic_a_key]['name'],
                   'tactic_b': TACTICAL_PRESETS[tactic_b_key]['name']}

        for i in range(n_runs):
            self.rng = np.random.RandomState(42 + i)
            self.set_tactics(tactic_a_key, tactic_b_key)
            stats = self.run(n_steps)
            results['runs'].append(stats)

        # Aggregate
        results['avg_goals_a'] = np.mean([r['goals_a'] for r in results['runs']])
        results['avg_goals_b'] = np.mean([r['goals_b'] for r in results['runs']])
        results['avg_possession_a'] = np.mean([r['possession_a'] for r in results['runs']])
        results['avg_possession_b'] = np.mean([r['possession_b'] for r in results['runs']])
        results['avg_territorial_a'] = np.mean([r['territorial_control_a'] for r in results['runs']])
        results['avg_territorial_b'] = np.mean([r['territorial_control_b'] for r in results['runs']])
        results['wins_a'] = sum(1 for r in results['runs'] if r['goals_a'] > r['goals_b'])
        results['wins_b'] = sum(1 for r in results['runs'] if r['goals_b'] > r['goals_a'])
        results['draws'] = sum(1 for r in results['runs'] if r['goals_a'] == r['goals_b'])
        return results

    # ── Visualization ──────────────────────────────────────────

    def draw_frame(self, step=0, figsize=(10, 7)):
        """Draw a single simulation frame."""
        if step >= len(self.history):
            step = len(self.history) - 1
        frame = self.history[step]

        fig, ax = plt.subplots(figsize=figsize, facecolor='#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        pw, ph = self.pitch_w, self.pitch_h
        ax.set_xlim(-3, pw + 3)
        ax.set_ylim(-3, ph + 3)

        # Pitch lines
        ax.add_patch(plt.Rectangle((0, 0), pw, ph, fill=False, edgecolor='#e0e0e0', linewidth=1))
        ax.plot([pw/2, pw/2], [0, ph], color='#e0e0e0', linewidth=0.5)
        ax.add_patch(Circle((pw/2, ph/2), ph*0.15, fill=False, edgecolor='#e0e0e0', linewidth=0.5))
        # Goals
        gw = ph * 0.3
        ax.add_patch(plt.Rectangle((-2, ph/2 - gw/2), 2, gw, fill=False, edgecolor='#e0e0e0', linewidth=1))
        ax.add_patch(plt.Rectangle((pw, ph/2 - gw/2), 2, gw, fill=False, edgecolor='#e0e0e0', linewidth=1))

        for p in frame['team_a']:
            ax.scatter(p['x'], p['y'], c='#a50044', s=200, edgecolors='white', linewidths=1.5, zorder=6)
            ax.annotate(str(p['pid']), xy=(p['x'], p['y']), ha='center', va='center',
                        fontsize=7, fontweight='bold', color='white', zorder=7)
        for p in frame['team_b']:
            ax.scatter(p['x'], p['y'], c='#ffffff', s=200, edgecolors='#333333', linewidths=1.5, zorder=6)
            ax.annotate(str(p['pid']), xy=(p['x'], p['y']), ha='center', va='center',
                        fontsize=7, fontweight='bold', color='#333333', zorder=7)

        ax.scatter(frame['ball']['x'], frame['ball']['y'], c='#f1c40f', s=80,
                   edgecolors='white', linewidths=1.5, zorder=8)

        ax.set_title(f"SpaceAI FC Simulation  |  Step {step}  |  "
                     f"{self.tactic_a['name']} vs {self.tactic_b['name']}  |  "
                     f"{self.goals_a}-{self.goals_b}",
                     color='white', fontsize=11, fontweight='bold', pad=10)
        ax.set_aspect('equal')
        ax.tick_params(colors='#666666', labelsize=6)
        return fig, ax

    def save_animation(self, filename="18_simulation.gif", max_frames=80, interval=100):
        """Save simulation as animated GIF."""
        if not self.history:
            return

        frames = self.history[:max_frames]
        fig, ax = plt.subplots(figsize=(10, 7), facecolor='#1a1a2e')
        pw, ph = self.pitch_w, self.pitch_h

        def animate(i):
            ax.clear()
            ax.set_facecolor('#1a1a2e')
            ax.set_xlim(-3, pw + 3)
            ax.set_ylim(-3, ph + 3)
            ax.add_patch(plt.Rectangle((0, 0), pw, ph, fill=False, edgecolor='#e0e0e0', linewidth=1))
            ax.plot([pw/2, pw/2], [0, ph], color='#e0e0e0', linewidth=0.5)
            gw = ph * 0.3
            ax.add_patch(plt.Rectangle((-2, ph/2-gw/2), 2, gw, fill=False, edgecolor='#e0e0e0', lw=1))
            ax.add_patch(plt.Rectangle((pw, ph/2-gw/2), 2, gw, fill=False, edgecolor='#e0e0e0', lw=1))

            f = frames[i]
            for p in f['team_a']:
                ax.scatter(p['x'], p['y'], c='#a50044', s=180, edgecolors='white', linewidths=1.2, zorder=6)
            for p in f['team_b']:
                ax.scatter(p['x'], p['y'], c='#ffffff', s=180, edgecolors='#333333', linewidths=1.2, zorder=6)
            ax.scatter(f['ball']['x'], f['ball']['y'], c='#f1c40f', s=60, edgecolors='white', linewidths=1, zorder=8)
            ax.set_title(f"Step {f['step']}  |  {self.tactic_a['name']} vs {self.tactic_b['name']}",
                         color='white', fontsize=10, fontweight='bold', pad=8)
            ax.set_aspect('equal')
            ax.tick_params(colors='#666666', labelsize=5)

        anim = animation.FuncAnimation(fig, animate, frames=len(frames), interval=interval, blit=False)
        filepath = f"outputs/{filename}"
        anim.save(filepath, writer='pillow', fps=8)
        plt.close(fig)
        print(f"  Saved: {filepath}")

    def draw_comparison(self, results, filename="18_simulation_comparison.png"):
        """Draw side-by-side comparison chart."""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6), facecolor='#1a1a2e')
        fig.suptitle(f"SpaceAI FC - Tactical Comparison: {results['tactic_a']} vs {results['tactic_b']}",
                     color='white', fontsize=14, fontweight='bold', y=0.98)

        colors_a, colors_b = '#a50044', '#3498db'

        # Panel 1: Goals
        ax1 = axes[0]
        ax1.set_facecolor('#1a1a2e')
        cats = ['Goals', 'Wins']
        vals_a = [results['avg_goals_a'], results['wins_a']]
        vals_b = [results['avg_goals_b'], results['wins_b']]
        x = np.arange(len(cats))
        ax1.bar(x - 0.15, vals_a, 0.3, color=colors_a, alpha=0.85, label=results['tactic_a'])
        ax1.bar(x + 0.15, vals_b, 0.3, color=colors_b, alpha=0.85, label=results['tactic_b'])
        ax1.set_xticks(x)
        ax1.set_xticklabels(cats)
        ax1.set_title('Goals & Wins', color='white', fontsize=11, fontweight='bold', pad=10)
        ax1.tick_params(colors='#aaaaaa')
        ax1.legend(fontsize=8, facecolor='#2c3e50', edgecolor='#444', labelcolor='white')
        for spine in ax1.spines.values():
            spine.set_color('#444444')

        # Panel 2: Possession
        ax2 = axes[1]
        ax2.set_facecolor('#1a1a2e')
        sizes = [results['avg_possession_a'], results['avg_possession_b']]
        labels = [f"{results['tactic_a']}\n{sizes[0]:.0f}%", f"{results['tactic_b']}\n{sizes[1]:.0f}%"]
        wedges, texts = ax2.pie(sizes, labels=labels, colors=[colors_a, colors_b],
                                 startangle=90, textprops={'color': 'white', 'fontsize': 9})
        ax2.set_title('Possession', color='white', fontsize=11, fontweight='bold', pad=10)

        # Panel 3: Territorial Control
        ax3 = axes[2]
        ax3.set_facecolor('#1a1a2e')
        metrics = ['Territorial\nControl', 'Avg Position\n(normalized)']
        n_runs = len(results['runs'])
        pw = self.pitch_w
        vals_a = [results['avg_territorial_a'], results.get('avg_goals_a', 0) * 20 + 30]
        vals_b = [results['avg_territorial_b'], results.get('avg_goals_b', 0) * 20 + 30]
        x = np.arange(len(metrics))
        ax3.bar(x - 0.15, vals_a, 0.3, color=colors_a, alpha=0.85, label=results['tactic_a'])
        ax3.bar(x + 0.15, vals_b, 0.3, color=colors_b, alpha=0.85, label=results['tactic_b'])
        ax3.set_xticks(x)
        ax3.set_xticklabels(metrics)
        ax3.set_title('Territorial Analysis', color='white', fontsize=11, fontweight='bold', pad=10)
        ax3.tick_params(colors='#aaaaaa')
        ax3.legend(fontsize=8, facecolor='#2c3e50', edgecolor='#444', labelcolor='white')
        for spine in ax3.spines.values():
            spine.set_color('#444444')

        plt.tight_layout()
        filepath = f"outputs/{filename}"
        fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"  Saved: {filepath}")
        return fig

    # ── Text Output ────────────────────────────────────────────

    def print_summary(self, stats=None):
        """Print simulation summary."""
        if stats is None:
            stats = self.get_stats()
        if not stats:
            print("  No simulation data.")
            return

        print(f"\n  ╔══════════════════════════════════════════╗")
        print(f"  ║   SIMULATION SUMMARY                     ║")
        print(f"  ╚══════════════════════════════════════════╝")
        print(f"  Format: {stats['team_size']}v{stats['team_size']}")
        print(f"  {stats['tactic_a']} vs {stats['tactic_b']}")
        print(f"  Steps: {stats['total_steps']}")
        print(f"\n  Score: {stats['goals_a']} - {stats['goals_b']}")
        print(f"  Possession: {stats['possession_a']}% - {stats['possession_b']}%")
        print(f"  Territorial: {stats['territorial_control_a']}% - {stats['territorial_control_b']}%")
        print(f"  Avg Position: {stats['avg_position_a']:.1f} - {stats['avg_position_b']:.1f}")
        if stats['events']:
            print(f"\n  Events:")
            for e in stats['events']:
                print(f"    Step {e['step']}: {'⚽ GOAL' if e['type'] == 'goal' else e['type']} (Team {e['team']})")
        print()

    def get_summary_data(self):
        """Get summary dict for MatchReport integration."""
        stats = self.get_stats()
        if not stats:
            return None
        return stats


# ════════════════════════════════════════════════════════════════
# Standalone Demo
# ════════════════════════════════════════════════════════════════

def demo():
    """Run a 5v5 High Press vs Low Block comparison demo."""
    print("\n" + "=" * 60)
    print("  SpaceAI FC - Multi-Agent Simulation Demo")
    print("  Phase 4 Module 3: Tactical Scenario Testing")
    print("=" * 60)

    os.makedirs("outputs", exist_ok=True)

    sim = TacticalSimulation(team_size=5, seed=42)

    # ── Step 1: Single run ─────────────────────────────────────
    print("\n[1/4] Running single simulation: High Press vs Low Block...")
    sim.set_tactics('high_press', 'low_block')
    stats = sim.run(n_steps=300)
    sim.print_summary(stats)

    # ── Step 2: Frame snapshot ─────────────────────────────────
    print("[2/4] Saving frame snapshot...")
    fig, ax = sim.draw_frame(step=150)
    fig.savefig("outputs/18_simulation_frame.png", dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print("  Saved: outputs/18_simulation_frame.png")

    # ── Step 3: Animation ──────────────────────────────────────
    print("\n[3/4] Generating animation...")
    try:
        sim.save_animation("18_simulation.gif", max_frames=80, interval=100)
    except Exception as e:
        print(f"  ⚠ Could not save animation: {e}")

    # ── Step 4: Comparison ─────────────────────────────────────
    print("\n[4/4] Running tactical comparison (5 runs)...")
    comparison = sim.compare_tactics('high_press', 'low_block', n_runs=5, n_steps=300)

    print(f"\n  ╔══════════════════════════════════════════════════╗")
    print(f"  ║   TACTICAL COMPARISON: High Press vs Low Block   ║")
    print(f"  ╚══════════════════════════════════════════════════╝")
    print(f"  Runs: {len(comparison['runs'])}")
    print(f"  Results: {comparison['wins_a']}W / {comparison['draws']}D / {comparison['wins_b']}L")
    print(f"  Avg Goals: {comparison['avg_goals_a']:.1f} - {comparison['avg_goals_b']:.1f}")
    print(f"  Avg Possession: {comparison['avg_possession_a']:.0f}% - {comparison['avg_possession_b']:.0f}%")
    print(f"  Avg Territorial: {comparison['avg_territorial_a']:.0f}% - {comparison['avg_territorial_b']:.0f}%")

    sim.draw_comparison(comparison)

    print("\n" + "=" * 60)
    print("  Simulation Demo Complete!")
    print("  Outputs: outputs/18_*.png, outputs/18_*.gif")
    print("=" * 60)

    plt.close('all')
    return sim


if __name__ == "__main__":
    demo()
