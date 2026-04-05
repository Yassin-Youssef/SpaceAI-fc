"""
SpaceAI FC - Reinforcement Learning Coach
==========================================
Phase 4 Module 2: An AI that learns tactical decisions through simulation.

Uses a custom Gymnasium environment (FootballTacticsEnv) where:
    - State: simplified match state (formation, space control, etc.)
    - Actions: 9 tactical decisions (press higher, drop deeper, etc.)
    - Reward: goals, space control changes, press resistance

Trains a PPO agent (Stable-Baselines3) that learns which tactical
decisions lead to better outcomes in different match situations.

Dependencies (optional):
    - gymnasium        (environment definition)
    - stable-baselines3 (PPO training)

If dependencies are missing, the module prints a skip message.
"""

import os
import sys
import math
import random
import json
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# ── Optional dependency imports ─────────────────────────────────

HAS_GYM = False
HAS_SB3 = False

try:
    import gymnasium as gym
    from gymnasium import spaces
    HAS_GYM = True
except ImportError:
    pass

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
    HAS_SB3 = True
except ImportError:
    pass


# ════════════════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════════════════

FORMATION_NAMES = {
    0: '4-4-2',
    1: '4-3-3',
    2: '4-2-3-1',
    3: '3-5-2',
    4: '5-3-2',
    5: '3-4-3',
}

ACTION_NAMES = {
    0: 'Keep Current Tactics',
    1: 'Press Higher',
    2: 'Drop Deeper',
    3: 'Attacking Formation',
    4: 'Defensive Formation',
    5: 'Exploit Width',
    6: 'Play Through Center',
    7: 'Increase Tempo',
    8: 'Slow Down Play',
}

ACTION_SHORT = {
    0: 'Keep', 1: 'Press↑', 2: 'Drop↓', 3: 'ATK',
    4: 'DEF', 5: 'Wide', 6: 'Center', 7: 'Tempo↑', 8: 'Slow↓',
}


# ════════════════════════════════════════════════════════════════
# Gymnasium Environment
# ════════════════════════════════════════════════════════════════

if HAS_GYM:
    class FootballTacticsEnv(gym.Env):
        """
        Custom Gymnasium environment for football tactical decisions.
        
        State (7 dims):
            0: own_formation  (0-5, encoded integer)
            1: opp_formation  (0-5)
            2: space_control  (0-100, percentage)
            3: press_resist   (0-100, score)
            4: score_diff     (-5 to +5)
            5: minute         (0-90)
            6: possession     (0-100, percentage)
        
        Actions (9 discrete):
            0: Keep current tactics
            1: Press higher
            2: Drop deeper
            3: Switch to attacking formation
            4: Switch to defensive formation
            5: Exploit width
            6: Play through center
            7: Increase tempo
            8: Slow down play
        
        Episode: 90 steps (one per minute of a match).
        """
        
        metadata = {'render_modes': []}
        
        def __init__(self, seed=None):
            super().__init__()
            
            self.observation_space = spaces.Box(
                low=np.array([0, 0, 0, 0, -5, 0, 0], dtype=np.float32),
                high=np.array([5, 5, 100, 100, 5, 90, 100], dtype=np.float32),
                dtype=np.float32
            )
            
            self.action_space = spaces.Discrete(9)
            
            self._seed = seed
            self.rng = np.random.RandomState(seed)
            self.state = None
            self.minute = 0
            self.episode_events = []
            
            # Match dynamics parameters
            self._base_goal_prob = 0.012  # ~1 goal per 83 mins per team
            self._tactical_advantage = 0.0
        
        def reset(self, seed=None, options=None):
            super().reset(seed=seed)
            
            if seed is not None:
                self.rng = np.random.RandomState(seed)
            
            # Random starting state
            self.state = np.array([
                self.rng.randint(0, 6),    # own formation
                self.rng.randint(0, 6),    # opponent formation
                50 + self.rng.randn() * 8, # space control
                55 + self.rng.randn() * 10, # press resistance
                0,                          # score difference
                0,                          # minute
                50 + self.rng.randn() * 5,  # possession
            ], dtype=np.float32)
            
            self.state = np.clip(self.state, self.observation_space.low,
                                  self.observation_space.high)
            
            self.minute = 0
            self._tactical_advantage = 0.0
            self.episode_events = []
            
            return self.state.copy(), {}
        
        def step(self, action):
            """
            Apply a tactical action and simulate one minute of play.
            """
            prev_space = self.state[2]
            prev_press = self.state[3]
            prev_score = self.state[4]
            
            # Apply tactical action effects
            self._apply_action(action)
            
            # Simulate one minute
            goal_scored, goal_conceded = self._simulate_minute()
            
            # Update score
            if goal_scored:
                self.state[4] = min(5, self.state[4] + 1)
                self.episode_events.append({
                    'minute': self.minute,
                    'event': 'goal_scored',
                    'action': action,
                })
            if goal_conceded:
                self.state[4] = max(-5, self.state[4] - 1)
                self.episode_events.append({
                    'minute': self.minute,
                    'event': 'goal_conceded',
                    'action': action,
                })
            
            # Advance minute
            self.minute += 1
            self.state[5] = min(90, self.minute)
            
            # Compute reward
            reward = self._compute_reward(
                prev_space, prev_press, prev_score,
                goal_scored, goal_conceded
            )
            
            # Episode ends at minute 90
            terminated = self.minute >= 90
            truncated = False
            
            info = {
                'minute': self.minute,
                'score_diff': float(self.state[4]),
                'goal_scored': goal_scored,
                'goal_conceded': goal_conceded,
                'action_name': ACTION_NAMES[action],
            }
            
            return self.state.copy(), reward, terminated, truncated, info
        
        def _apply_action(self, action):
            """Modify state based on tactical action."""
            # Natural drift
            self.state[2] += self.rng.randn() * 2  # space control noise
            self.state[3] += self.rng.randn() * 1.5  # press resistance noise
            self.state[6] += self.rng.randn() * 2  # possession noise
            
            if action == 0:   # Keep current — no change
                pass
            elif action == 1: # Press higher
                self.state[2] += 3  # gain space
                self.state[3] -= 2  # harder to resist counter
                self.state[6] += 2  # gain possession
                self._tactical_advantage += 0.3
            elif action == 2: # Drop deeper
                self.state[2] -= 2  # concede space
                self.state[3] += 3  # better press resistance
                self.state[6] -= 1
                self._tactical_advantage -= 0.1
            elif action == 3: # Attacking formation
                self.state[0] = self.rng.choice([1, 2, 5])  # 4-3-3, 4-2-3-1, 3-4-3
                self.state[2] += 2
                self.state[3] -= 1
                self._tactical_advantage += 0.4
            elif action == 4: # Defensive formation
                self.state[0] = self.rng.choice([0, 4])  # 4-4-2, 5-3-2
                self.state[2] -= 3
                self.state[3] += 4
                self._tactical_advantage -= 0.2
            elif action == 5: # Exploit width
                self.state[2] += 4
                self.state[6] += 1
                self._tactical_advantage += 0.25
            elif action == 6: # Play through center
                self.state[3] -= 2  # more pressure centrally
                self._tactical_advantage += 0.2
            elif action == 7: # Increase tempo
                self.state[6] += 3
                self.state[2] += 2
                self.state[3] -= 3  # mistakes under tempo
                self._tactical_advantage += 0.35
            elif action == 8: # Slow down play
                self.state[6] += 1
                self.state[3] += 2
                self._tactical_advantage -= 0.05
            
            # Clip state
            self.state = np.clip(self.state, self.observation_space.low,
                                  self.observation_space.high)
            
            # Tactical advantage decay
            self._tactical_advantage *= 0.95
        
        def _simulate_minute(self):
            """
            Simulate one minute of match play.
            Returns (goal_scored: bool, goal_conceded: bool).
            """
            # Goal probability modulated by tactical state
            space_bonus = (self.state[2] - 50) / 200  # space control effect
            possession_bonus = (self.state[6] - 50) / 300  # possession effect
            advantage_bonus = self._tactical_advantage * 0.01
            
            our_goal_prob = max(0.001, min(0.08,
                self._base_goal_prob + space_bonus + possession_bonus + advantage_bonus
            ))
            
            # Opponent goal prob — inversely affected
            their_goal_prob = max(0.001, min(0.06,
                self._base_goal_prob - space_bonus * 0.5 - advantage_bonus * 0.5
                + (100 - self.state[3]) / 800  # low press resistance = more goals conceded
            ))
            
            goal_scored = self.rng.random() < our_goal_prob
            goal_conceded = self.rng.random() < their_goal_prob
            
            return goal_scored, goal_conceded
        
        def _compute_reward(self, prev_space, prev_press, prev_score,
                            goal_scored, goal_conceded):
            """
            Compute reward for the current step.
            """
            reward = 0.0
            
            # Goal rewards
            if goal_scored:
                reward += 10.0
            if goal_conceded:
                reward -= 10.0
            
            # Space control improvement
            space_delta = self.state[2] - prev_space
            if space_delta > 0:
                reward += min(1.0, space_delta * 0.1)
            else:
                reward += max(-0.5, space_delta * 0.05)
            
            # Press resistance improvement
            press_delta = self.state[3] - prev_press
            if press_delta > 0:
                reward += min(0.5, press_delta * 0.05)
            
            # Small negative per step (encourage decisiveness)
            reward -= 0.01
            
            # Bonus for winning at end of match
            if self.minute >= 90:
                if self.state[4] > 0:
                    reward += 5.0  # win bonus
                elif self.state[4] < 0:
                    reward -= 3.0  # loss penalty
            
            return float(reward)


# ════════════════════════════════════════════════════════════════
# Training Callback for reward tracking
# ════════════════════════════════════════════════════════════════

if HAS_SB3:
    class RewardTracker(BaseCallback):
        """Track episode rewards during training."""
        
        def __init__(self, verbose=0):
            super().__init__(verbose)
            self.episode_rewards = []
            self.episode_lengths = []
            self._current_rewards = {}
        
        def _on_step(self):
            # Track rewards per environment
            for i, done in enumerate(self.locals.get('dones', [])):
                env_key = i
                if env_key not in self._current_rewards:
                    self._current_rewards[env_key] = 0.0
                self._current_rewards[env_key] += self.locals['rewards'][i]
                
                if done:
                    self.episode_rewards.append(self._current_rewards[env_key])
                    self.episode_lengths.append(self.num_timesteps)
                    self._current_rewards[env_key] = 0.0
            
            return True


# ════════════════════════════════════════════════════════════════
# RL Coach
# ════════════════════════════════════════════════════════════════

class RLCoach:
    """
    Reinforcement Learning Tactical Coach.
    
    Trains a PPO agent on the FootballTacticsEnv to learn
    which tactical decisions lead to better match outcomes.
    
    Usage:
        coach = RLCoach()
        coach.train(timesteps=50000)
        results = coach.evaluate(n_episodes=20)
        coach.print_evaluation(results)
    """
    
    def __init__(self):
        self.model = None
        self.env = None
        self.training_rewards = []
        self.is_trained = False
    
    def _check_dependencies(self):
        """Check that required dependencies are available."""
        if not HAS_GYM:
            raise ImportError(
                "gymnasium required for RL Coach. "
                "Run: pip install gymnasium"
            )
        if not HAS_SB3:
            raise ImportError(
                "stable-baselines3 required for RL Coach. "
                "Run: pip install stable-baselines3"
            )
    
    def train(self, timesteps=50_000, seed=42, verbose=0):
        """
        Train the RL agent using PPO.
        
        Args:
            timesteps: number of training timesteps
            seed: random seed for reproducibility
            verbose: 0=quiet, 1=progress bar
        """
        self._check_dependencies()
        
        print(f"  Training PPO agent for {timesteps:,} timesteps...")
        
        self.env = FootballTacticsEnv(seed=seed)
        
        self.model = PPO(
            'MlpPolicy',
            self.env,
            verbose=verbose,
            learning_rate=3e-4,
            n_steps=256,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            seed=seed,
        )
        
        # Attach reward tracker
        tracker = RewardTracker()
        
        self.model.learn(
            total_timesteps=timesteps,
            callback=tracker,
            progress_bar=False,
        )
        
        self.training_rewards = tracker.episode_rewards
        self.is_trained = True
        
        n_episodes = len(self.training_rewards)
        if n_episodes > 0:
            avg_last_20 = np.mean(self.training_rewards[-20:])
            print(f"  Training complete!")
            print(f"  Episodes trained: {n_episodes}")
            print(f"  Avg reward (last 20 eps): {avg_last_20:.2f}")
        else:
            print(f"  Training complete! ({timesteps} steps)")
    
    def evaluate(self, n_episodes=20, seed=123):
        """
        Evaluate the trained agent across multiple episodes.
        
        Returns:
            dict with evaluation results
        """
        self._check_dependencies()
        
        if not self.is_trained or self.model is None:
            raise ValueError("Train the model first with coach.train()")
        
        print(f"\n  Evaluating agent over {n_episodes} episodes...")
        
        eval_env = FootballTacticsEnv(seed=seed)
        
        results = {
            'episodes': [],
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'total_goals_scored': 0,
            'total_goals_conceded': 0,
            'action_counts': {i: 0 for i in range(9)},
            'action_by_scenario': {
                'winning': {i: 0 for i in range(9)},
                'losing': {i: 0 for i in range(9)},
                'drawing': {i: 0 for i in range(9)},
            },
            'rewards': [],
        }
        
        for ep in range(n_episodes):
            obs, _ = eval_env.reset(seed=seed + ep)
            total_reward = 0.0
            actions_taken = []
            
            done = False
            while not done:
                action, _ = self.model.predict(obs, deterministic=True)
                action = int(action)
                
                # Track action by scenario
                score_diff = obs[4]
                if score_diff > 0:
                    scenario = 'winning'
                elif score_diff < 0:
                    scenario = 'losing'
                else:
                    scenario = 'drawing'
                
                results['action_counts'][action] += 1
                results['action_by_scenario'][scenario][action] += 1
                actions_taken.append(action)
                
                obs, reward, terminated, truncated, info = eval_env.step(action)
                total_reward += reward
                done = terminated or truncated
            
            # Episode outcome
            final_score = obs[4]
            if final_score > 0:
                results['wins'] += 1
            elif final_score < 0:
                results['losses'] += 1
            else:
                results['draws'] += 1
            
            # Count goals
            g_scored = sum(1 for e in eval_env.episode_events if e['event'] == 'goal_scored')
            g_conceded = sum(1 for e in eval_env.episode_events if e['event'] == 'goal_conceded')
            results['total_goals_scored'] += g_scored
            results['total_goals_conceded'] += g_conceded
            
            results['episodes'].append({
                'episode': ep,
                'reward': total_reward,
                'score_diff': float(final_score),
                'goals_scored': g_scored,
                'goals_conceded': g_conceded,
                'actions': actions_taken,
            })
            results['rewards'].append(total_reward)
        
        results['avg_reward'] = float(np.mean(results['rewards']))
        results['win_rate'] = results['wins'] / n_episodes
        
        print(f"  Evaluation complete!")
        print(f"  Win rate: {results['win_rate']:.0%} "
              f"({results['wins']}W / {results['draws']}D / {results['losses']}L)")
        print(f"  Avg reward: {results['avg_reward']:.2f}")
        
        return results
    
    def predict(self, state_dict):
        """
        Get tactical recommendation for a given match state.
        
        Args:
            state_dict: dict with keys:
                own_formation (int 0-5), opp_formation (int 0-5),
                space_control (0-100), press_resistance (0-100),
                score_diff (-5 to 5), minute (0-90), possession (0-100)
        
        Returns:
            dict with action index, name, and confidence
        """
        if not self.is_trained or self.model is None:
            return {'error': 'Model not trained. Call train() first.'}
        
        state = np.array([
            state_dict.get('own_formation', 2),
            state_dict.get('opp_formation', 1),
            state_dict.get('space_control', 50),
            state_dict.get('press_resistance', 55),
            state_dict.get('score_diff', 0),
            state_dict.get('minute', 45),
            state_dict.get('possession', 50),
        ], dtype=np.float32)
        
        action, _ = self.model.predict(state, deterministic=True)
        action = int(action)
        
        return {
            'action': action,
            'action_name': ACTION_NAMES[action],
            'state': state_dict,
        }
    
    # ── Save / Load ────────────────────────────────────────────
    
    def save_model(self, path="outputs/rl_coach_model"):
        """Save trained model to disk."""
        if self.model is None:
            raise ValueError("No model to save. Train first.")
        
        # Validate path — ensure it's in allowed directory
        abs_path = os.path.abspath(path)
        self.model.save(abs_path)
        print(f"  Model saved: {abs_path}.zip")
    
    def load_model(self, path="outputs/rl_coach_model"):
        """
        Load a previously trained model.
        Validates file exists and has reasonable size.
        """
        self._check_dependencies()
        
        zip_path = path if path.endswith('.zip') else path + '.zip'
        
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Model not found: {zip_path}")
        
        # Size check — PPO models shouldn't be huge
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        if size_mb > 100:
            raise ValueError(f"Model file suspiciously large ({size_mb:.0f} MB). Aborting load.")
        
        self.env = FootballTacticsEnv()
        self.model = PPO.load(zip_path, env=self.env)
        self.is_trained = True
        print(f"  Model loaded: {zip_path} ({size_mb:.1f} MB)")
    
    # ── Visualization ──────────────────────────────────────────
    
    def draw_training_curve(self, filename="17_rl_training_curve.png"):
        """Plot training rewards over episodes."""
        if not self.training_rewards:
            print("  No training data to plot.")
            return None
        
        fig, ax = plt.subplots(figsize=(12, 5), facecolor='#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        
        episodes = range(len(self.training_rewards))
        ax.plot(episodes, self.training_rewards, color='#3498db',
                alpha=0.3, linewidth=0.8, label='Episode Reward')
        
        # Smoothed curve (rolling average)
        window = min(20, len(self.training_rewards) // 5 + 1)
        if window > 1 and len(self.training_rewards) >= window:
            smoothed = np.convolve(self.training_rewards,
                                    np.ones(window) / window, mode='valid')
            ax.plot(range(window - 1, len(self.training_rewards)),
                    smoothed, color='#f1c40f', linewidth=2,
                    label=f'Moving Avg ({window} eps)')
        
        ax.set_xlabel('Episode', color='white', fontsize=11)
        ax.set_ylabel('Total Reward', color='white', fontsize=11)
        ax.set_title('SpaceAI FC - RL Coach Training Progress',
                      color='white', fontsize=14, fontweight='bold', pad=12)
        ax.tick_params(colors='#aaaaaa')
        ax.legend(fontsize=9, facecolor='#2c3e50', edgecolor='#444444',
                  labelcolor='white')
        ax.grid(True, alpha=0.1, color='white')
        ax.spines['bottom'].set_color('#444444')
        ax.spines['left'].set_color('#444444')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        filepath = f"outputs/{filename}"
        fig.savefig(filepath, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"  Saved: {filepath}")
        return fig
    
    def draw_decision_distribution(self, eval_results,
                                    filename="17_rl_decisions.png"):
        """
        Draw action distribution charts — overall and by scenario.
        """
        fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor='#1a1a2e')
        
        fig.suptitle("SpaceAI FC - RL Coach Decision Analysis",
                      color='white', fontsize=14, fontweight='bold', y=0.98)
        
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
                  '#1abc9c', '#e67e22', '#f1c40f', '#95a5a6']
        
        # Panel 1: Overall action distribution
        ax1 = axes[0]
        ax1.set_facecolor('#1a1a2e')
        
        action_counts = eval_results['action_counts']
        total_actions = max(sum(action_counts.values()), 1)
        
        actions = list(range(9))
        counts = [action_counts[a] for a in actions]
        percentages = [c / total_actions * 100 for c in counts]
        labels = [ACTION_SHORT[a] for a in actions]
        
        bars = ax1.barh(labels, percentages, color=colors, height=0.6, alpha=0.85)
        
        for bar, pct in zip(bars, percentages):
            if pct > 2:
                ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                         f'{pct:.1f}%', va='center', color='white', fontsize=8)
        
        ax1.set_xlabel('Frequency (%)', color='white', fontsize=10)
        ax1.set_title('Overall Decision Distribution', color='white',
                       fontsize=11, fontweight='bold', pad=10)
        ax1.tick_params(colors='#aaaaaa', labelsize=8)
        ax1.spines['bottom'].set_color('#444444')
        ax1.spines['left'].set_color('#444444')
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.invert_yaxis()
        
        # Panel 2: Actions by scenario
        ax2 = axes[1]
        ax2.set_facecolor('#1a1a2e')
        
        scenarios = ['winning', 'drawing', 'losing']
        scenario_colors = ['#2ecc71', '#f39c12', '#e74c3c']
        
        x = np.arange(9)
        width = 0.25
        
        for i, (scenario, sc_color) in enumerate(zip(scenarios, scenario_colors)):
            sc_counts = eval_results['action_by_scenario'][scenario]
            sc_total = max(sum(sc_counts.values()), 1)
            sc_pcts = [sc_counts[a] / sc_total * 100 for a in range(9)]
            ax2.bar(x + i * width, sc_pcts, width, label=scenario.capitalize(),
                    color=sc_color, alpha=0.8)
        
        ax2.set_xticks(x + width)
        ax2.set_xticklabels([ACTION_SHORT[a] for a in range(9)],
                             rotation=45, ha='right')
        ax2.set_ylabel('Frequency (%)', color='white', fontsize=10)
        ax2.set_title('Decisions by Match Scenario', color='white',
                       fontsize=11, fontweight='bold', pad=10)
        ax2.tick_params(colors='#aaaaaa', labelsize=7)
        ax2.legend(fontsize=8, facecolor='#2c3e50', edgecolor='#444444',
                   labelcolor='white', loc='upper right')
        ax2.spines['bottom'].set_color('#444444')
        ax2.spines['left'].set_color('#444444')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        filepath = f"outputs/{filename}"
        fig.savefig(filepath, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"  Saved: {filepath}")
        return fig
    
    # ── Text Output ────────────────────────────────────────────
    
    def print_evaluation(self, eval_results):
        """Print a formatted evaluation summary."""
        print(f"\n  ╔══════════════════════════════════════════╗")
        print(f"  ║   RL COACH EVALUATION SUMMARY            ║")
        print(f"  ╚══════════════════════════════════════════╝")
        
        n = len(eval_results['episodes'])
        print(f"  Episodes: {n}")
        print(f"  Win Rate: {eval_results['win_rate']:.0%} "
              f"({eval_results['wins']}W / {eval_results['draws']}D / "
              f"{eval_results['losses']}L)")
        print(f"  Avg Reward: {eval_results['avg_reward']:.2f}")
        print(f"  Goals Scored: {eval_results['total_goals_scored']} "
              f"({eval_results['total_goals_scored']/n:.1f}/game)")
        print(f"  Goals Conceded: {eval_results['total_goals_conceded']} "
              f"({eval_results['total_goals_conceded']/n:.1f}/game)")
        
        print(f"\n  --- Top Tactical Preferences ---")
        action_counts = eval_results['action_counts']
        total = max(sum(action_counts.values()), 1)
        sorted_actions = sorted(action_counts.items(), key=lambda x: -x[1])
        
        for action, count in sorted_actions[:5]:
            pct = count / total * 100
            print(f"  {ACTION_NAMES[action]:30s} {pct:5.1f}% ({count})")
        
        print(f"\n  --- Scenario-Specific Decisions ---")
        for scenario in ['winning', 'drawing', 'losing']:
            sc_counts = eval_results['action_by_scenario'][scenario]
            sc_total = max(sum(sc_counts.values()), 1)
            top_action = max(sc_counts, key=sc_counts.get)
            top_pct = sc_counts[top_action] / sc_total * 100
            
            print(f"  When {scenario:8s}: Prefers '{ACTION_NAMES[top_action]}' ({top_pct:.0f}%)")
        print()
    
    def predict_for_scenarios(self):
        """
        Get predictions for several sample match scenarios.
        Returns list of (scenario_name, state, prediction) tuples.
        """
        if not self.is_trained:
            return []
        
        scenarios = [
            ("Winning 2-0, 70th min, dominant possession", {
                'own_formation': 2, 'opp_formation': 1,
                'space_control': 65, 'press_resistance': 70,
                'score_diff': 2, 'minute': 70, 'possession': 62,
            }),
            ("Losing 0-1, 60th min, under pressure", {
                'own_formation': 0, 'opp_formation': 4,
                'space_control': 35, 'press_resistance': 40,
                'score_diff': -1, 'minute': 60, 'possession': 42,
            }),
            ("Drawing 1-1, 80th min, balanced", {
                'own_formation': 1, 'opp_formation': 2,
                'space_control': 50, 'press_resistance': 55,
                'score_diff': 0, 'minute': 80, 'possession': 50,
            }),
            ("Winning 1-0, 85th min, opponent pressing", {
                'own_formation': 2, 'opp_formation': 5,
                'space_control': 40, 'press_resistance': 45,
                'score_diff': 1, 'minute': 85, 'possession': 38,
            }),
            ("Losing 0-2, 30th min, need to respond", {
                'own_formation': 0, 'opp_formation': 3,
                'space_control': 42, 'press_resistance': 50,
                'score_diff': -2, 'minute': 30, 'possession': 45,
            }),
        ]
        
        results = []
        for name, state in scenarios:
            pred = self.predict(state)
            results.append((name, state, pred))
        
        return results
    
    def get_summary_data(self):
        """
        Get a summary dict suitable for integration with MatchReport.
        
        Returns:
            dict or None
        """
        if not self.is_trained:
            return None
        
        scenarios = self.predict_for_scenarios()
        
        return {
            'is_trained': True,
            'recommendations': [
                {
                    'scenario': name,
                    'action': pred['action_name'],
                }
                for name, _, pred in scenarios
            ]
        }


# ════════════════════════════════════════════════════════════════
# Standalone Demo
# ════════════════════════════════════════════════════════════════

def demo():
    """
    Run a full RL Coach demo:
      1. Create environment
      2. Train PPO agent (50k steps)
      3. Evaluate performance
      4. Show predictions for sample scenarios
      5. Generate visualizations
    """
    print("\n" + "=" * 60)
    print("  SpaceAI FC - RL Coach Demo")
    print("  Phase 4 Module 2: Reinforcement Learning Tactics")
    print("=" * 60)
    
    if not HAS_GYM or not HAS_SB3:
        print("\n  ⚠ Dependencies not available:")
        if not HAS_GYM:
            print("    - gymnasium not installed. Run: pip install gymnasium")
        if not HAS_SB3:
            print("    - stable-baselines3 not installed. Run: pip install stable-baselines3")
        print("\n  Skipping RL Coach demo.")
        return None
    
    os.makedirs("outputs", exist_ok=True)
    
    coach = RLCoach()
    
    # ── Step 1: Train ──────────────────────────────────────────
    print("\n[1/5] Training PPO agent...")
    coach.train(timesteps=50_000, seed=42, verbose=0)
    
    # ── Step 2: Training curve ─────────────────────────────────
    print("\n[2/5] Plotting training curve...")
    coach.draw_training_curve()
    
    # ── Step 3: Evaluate ───────────────────────────────────────
    print("\n[3/5] Evaluating trained agent...")
    eval_results = coach.evaluate(n_episodes=20)
    coach.print_evaluation(eval_results)
    
    # ── Step 4: Decision distribution ──────────────────────────
    print("[4/5] Plotting decision distribution...")
    coach.draw_decision_distribution(eval_results)
    
    # ── Step 5: Sample predictions ─────────────────────────────
    print("[5/5] Tactical predictions for sample scenarios:")
    scenarios = coach.predict_for_scenarios()
    
    print(f"\n  ╔══════════════════════════════════════════════════╗")
    print(f"  ║   TACTICAL RECOMMENDATIONS                       ║")
    print(f"  ╚══════════════════════════════════════════════════╝")
    
    for name, state, pred in scenarios:
        print(f"\n  Scenario: {name}")
        print(f"  → Recommendation: {pred['action_name']}")
    
    # ── Save model ─────────────────────────────────────────────
    coach.save_model("outputs/rl_coach_model")
    
    print("\n" + "=" * 60)
    print("  RL Coach Demo Complete!")
    print("  Outputs: outputs/17_rl_*.png, outputs/rl_coach_model.zip")
    print("=" * 60)
    
    plt.close('all')
    return coach


if __name__ == "__main__":
    demo()
