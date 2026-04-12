"""
SpaceAI FC - Simulation + RL Router
  POST /api/simulation/run
  POST /api/simulation/compare
  POST /api/rl/predict
  POST /api/rl/train
"""

import numpy as np
from fastapi import APIRouter, HTTPException
from api.models.requests import (
    SimulationRequest, SimulationCompareRequest,
    RLMatchState, RLTrainRequest,
)
from api.models.responses import (
    SimulationResponse, SimulationCompareResponse,
    RLPredictResponse, RLTrainResponse,
)

router = APIRouter(tags=["Simulation & RL"])

# Action names for RL coach
ACTION_NAMES = {
    0: "Keep current tactics",
    1: "Press higher",
    2: "Drop deeper",
    3: "Switch to attacking formation",
    4: "Switch to defensive formation",
    5: "Exploit width",
    6: "Play through center",
    7: "Increase tempo",
    8: "Slow down play",
}


# ── Simulation ────────────────────────────────────────────────────

@router.post("/api/simulation/run", response_model=SimulationResponse)
async def simulation_run(req: SimulationRequest):
    try:
        from engine.intelligence.simulation import TacticalSimulation

        sim = TacticalSimulation(team_size=req.team_size, max_steps=req.steps, seed=req.seed)
        sim.set_tactics(req.tactic_a, req.tactic_b)
        stats = sim.run(n_steps=req.steps)

        return SimulationResponse(
            success=True,
            tactic_a=stats.get("tactic_a", req.tactic_a),
            tactic_b=stats.get("tactic_b", req.tactic_b),
            goals_a=stats.get("goals_a", 0),
            goals_b=stats.get("goals_b", 0),
            possession_a=round(stats.get("possession_a", 50.0), 1),
            possession_b=round(stats.get("possession_b", 50.0), 1),
            territorial_control_a=round(stats.get("territorial_control_a", 50.0), 1),
            steps=req.steps,
            events=sim.events[:50],  # cap event list for API response size
        )
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"Simulation module unavailable: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/simulation/compare", response_model=SimulationCompareResponse)
async def simulation_compare(req: SimulationCompareRequest):
    try:
        from engine.intelligence.simulation import TacticalSimulation

        def _run_avg(tactic_a, tactic_b, runs, steps):
            totals = {"goals_a": 0, "goals_b": 0, "possession_a": 0.0, "terr": 0.0}
            for seed in range(runs):
                sim = TacticalSimulation(team_size=req.team_size, max_steps=steps, seed=seed)
                sim.set_tactics(tactic_a, tactic_b)
                s = sim.run(n_steps=steps)
                totals["goals_a"] += s.get("goals_a", 0)
                totals["goals_b"] += s.get("goals_b", 0)
                totals["possession_a"] += s.get("possession_a", 50.0)
                totals["terr"] += s.get("territorial_control_a", 50.0)
            return {
                "tactic_a": tactic_a,
                "tactic_b": tactic_b,
                "avg_goals_a": round(totals["goals_a"] / runs, 2),
                "avg_goals_b": round(totals["goals_b"] / runs, 2),
                "avg_possession_a": round(totals["possession_a"] / runs, 1),
                "avg_territorial_control_a": round(totals["terr"] / runs, 1),
                "runs": runs,
            }

        m1 = _run_avg(req.tactic_a, req.tactic_b, req.runs, req.steps_per_run)
        m2 = _run_avg(req.tactic_a2, req.tactic_b2, req.runs, req.steps_per_run)

        # Simple verdict
        score1 = m1["avg_goals_a"] - m1["avg_goals_b"] + (m1["avg_possession_a"] - 50) * 0.05
        score2 = m2["avg_goals_a"] - m2["avg_goals_b"] + (m2["avg_possession_a"] - 50) * 0.05
        if score1 > score2:
            verdict = f"Matchup 1 ({req.tactic_a} vs {req.tactic_b}) performs better."
        elif score2 > score1:
            verdict = f"Matchup 2 ({req.tactic_a2} vs {req.tactic_b2}) performs better."
        else:
            verdict = "Both matchups are evenly balanced."

        return SimulationCompareResponse(
            success=True,
            matchup_1=m1,
            matchup_2=m2,
            verdict=verdict,
        )
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── RL Coach ──────────────────────────────────────────────────────

@router.post("/api/rl/predict", response_model=RLPredictResponse)
async def rl_predict(req: RLMatchState):
    """
    Get RL coach tactical recommendation for a given match state.
    Returns a rule-based prediction if RL dependencies are not installed.
    """
    state_dict = req.model_dump()

    try:
        from engine.intelligence.rl_coach import RLCoach, HAS_GYM, HAS_SB3

        if not (HAS_GYM and HAS_SB3):
            return _rule_based_predict(state_dict)

        coach = RLCoach()
        coach.train(timesteps=5_000, seed=42, verbose=0)  # quick train if not trained

        state_arr = np.array([
            req.own_formation, req.opp_formation, req.space_control,
            req.press_resistance, req.score_diff, req.minute, req.possession,
        ], dtype=np.float32)

        action, _ = coach.model.predict(state_arr, deterministic=True)
        action_id = int(action)

        return RLPredictResponse(
            success=True,
            action_id=action_id,
            action_name=ACTION_NAMES.get(action_id, "Unknown"),
            state=state_dict,
            available=True,
        )

    except ImportError:
        return _rule_based_predict(state_dict)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/rl/train", response_model=RLTrainResponse)
async def rl_train(req: RLTrainRequest):
    """Train the RL PPO agent (admin). Requires gymnasium + stable-baselines3."""
    try:
        from engine.intelligence.rl_coach import RLCoach, HAS_GYM, HAS_SB3

        if not (HAS_GYM and HAS_SB3):
            raise HTTPException(
                status_code=503,
                detail="gymnasium and stable-baselines3 are required. "
                       "Run: pip install gymnasium stable-baselines3",
            )

        coach = RLCoach()
        coach.train(timesteps=req.timesteps, seed=req.seed, verbose=0)

        avg_reward = float(np.mean(coach.training_rewards)) if coach.training_rewards else 0.0
        episodes = len(coach.training_rewards)

        return RLTrainResponse(
            success=True,
            timesteps=req.timesteps,
            episodes_trained=episodes,
            avg_reward=round(avg_reward, 3),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _rule_based_predict(state: dict) -> RLPredictResponse:
    """Simple rule-based fallback when RL deps are absent."""
    score_diff = state.get("score_diff", 0)
    space = state.get("space_control", 50)
    minute = state.get("minute", 0)
    press = state.get("press_resistance", 50)

    if score_diff < 0 and minute > 60:
        action_id = 3  # attacking formation
    elif score_diff > 0 and minute > 75:
        action_id = 4  # defensive formation
    elif space < 40:
        action_id = 1  # press higher to gain space
    elif press < 40:
        action_id = 2  # drop deeper to improve press resistance
    else:
        action_id = 0  # keep current

    return RLPredictResponse(
        success=True,
        action_id=action_id,
        action_name=ACTION_NAMES[action_id],
        state=state,
        available=False,
    )
