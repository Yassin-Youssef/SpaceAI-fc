"""
SpaceAI FC - Player Assessment Router
  POST /api/player-assessment

Builds a five-axis attribute radar from one of three inputs (video tracking,
raw match statistics, or manual scout ratings), infers the best tactical
role with a rule-based classifier, and writes a scouting report — enhanced
by the LLM when a key is configured, deterministic otherwise.
"""

from fastapi import APIRouter, HTTPException

from api.models.requests import PlayerAssessmentRequest
from api.models.responses import PlayerAssessmentResponse
from api.services.llm_service import ask_llm, has_llm
from api.services import video_service

router = APIRouter(tags=["Player Assessment"])


# ── Role model ────────────────────────────────────────────────────
# Each role lists the attributes it depends on with weights.  The role whose
# weighted attribute score is highest wins; the reasoning strings are used in
# the deterministic report.

ROLE_PROFILES = {
    "Ball-Playing Centre-Back": {"Defending": 0.5, "Passing": 0.3, "Aerial": 0.2},
    "Full-Back / Wing-Back":    {"Physical": 0.35, "Defending": 0.3, "Passing": 0.2, "Speed": 0.15},
    "Ball-Winning Midfielder":  {"Defending": 0.45, "Physical": 0.35, "Passing": 0.2},
    "Deep-Lying Playmaker":     {"Passing": 0.6, "Defending": 0.2, "Physical": 0.2},
    "Box-to-Box Midfielder":    {"Physical": 0.4, "Passing": 0.3, "Attacking": 0.3},
    "Advanced Playmaker":       {"Passing": 0.45, "Attacking": 0.35, "Dribbling": 0.2},
    "Inverted Winger":          {"Dribbling": 0.4, "Attacking": 0.35, "Speed": 0.25},
    "Inside Forward":           {"Shooting": 0.4, "Attacking": 0.3, "Dribbling": 0.3},
    "Target Striker":           {"Aerial": 0.45, "Shooting": 0.35, "Physical": 0.2},
    "Complete Forward":         {"Shooting": 0.35, "Attacking": 0.3, "Physical": 0.2, "Speed": 0.15},
}

# Attribute aliases so any radar vocabulary maps onto the role model
_ALIASES = {
    "speed": "Speed", "pace": "Speed", "acceleration": "Speed",
    "stamina": "Physical", "physical": "Physical", "work rate": "Physical", "strength": "Physical",
    "passing": "Passing", "vision": "Passing",
    "dribbling": "Dribbling",
    "shooting": "Shooting", "finishing": "Shooting",
    "defending": "Defending", "tackling": "Defending", "positioning": "Defending",
    "attacking": "Attacking", "creativity": "Attacking",
    "aerial": "Aerial", "heading": "Aerial",
}


@router.post("/api/player-assessment", response_model=PlayerAssessmentResponse)
async def player_assessment(req: PlayerAssessmentRequest):
    try:
        radar, source_note = _build_radar(req)
        if not radar:
            raise HTTPException(status_code=400, detail="No usable player data was provided.")

        role, role_scores = _infer_role(radar, req.position)
        strengths, weaknesses = _strengths_weaknesses(radar)
        report = _template_report(req, radar, role, strengths, weaknesses, source_note)

        # LLM enhancement (optional)
        if has_llm():
            llm_report, llm_role, llm_str, llm_weak = await _llm_enhance(
                req, radar, role, strengths, weaknesses, source_note
            )
            if llm_report:
                report = llm_report
                role = llm_role or role
                strengths = llm_str or strengths
                weaknesses = llm_weak or weaknesses

        return PlayerAssessmentResponse(
            success=True,
            recommended_role=role,
            radar_data={k: float(v) for k, v in radar.items()},
            scouting_report=report,
            strengths=strengths,
            weaknesses=weaknesses,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Radar construction ────────────────────────────────────────────

def _clamp(v) -> int:
    return int(max(0, min(100, round(v))))


def _build_radar(req: PlayerAssessmentRequest) -> tuple:
    """Return (radar dict, source note) for the requested input type."""

    if req.input_type == "video":
        tracking = req.tracking_data
        if not tracking and (req.youtube_url or req.video_file):
            if req.youtube_url:
                tracking = video_service.process_youtube_url(req.youtube_url)
            else:
                tracking = video_service.process_video_file(req.video_file)
        if not tracking:
            raise HTTPException(
                status_code=400,
                detail="Video mode needs a YouTube URL, an uploaded video, or tracking data.",
            )
        return _radar_from_tracking(tracking, req.player_track_id)

    if req.input_type == "data":
        s = req.stats
        if not s:
            raise HTTPException(status_code=400, detail="Data mode needs a `stats` object.")
        minutes = max(30, int(s.minutes or 90))
        p90 = 90.0 / minutes
        attempted = max(1, s.passes_attempted)
        completion = s.passes_completed / attempted
        shots90, drib90 = s.shots * p90, s.dribbles * p90
        tack90, int90 = s.tackles * p90, s.interceptions * p90
        aer90, spr90 = s.aerial_duels * p90, s.sprints * p90
        carry90 = (s.carry_distance_m or 0.0) * p90
        radar = {
            "Passing":   _clamp(35 + completion * 45 + min(20, attempted * p90 / 5)),
            "Attacking": _clamp(15 + shots90 * 7 + drib90 * 6),
            "Dribbling": _clamp(25 + drib90 * 12 + carry90 / 25),
            "Defending": _clamp(15 + tack90 * 10 + int90 * 8),
            "Physical":  _clamp(40 + spr90 * 0.9 + min(10, s.distance_covered * 0.5)),
            "Aerial":    _clamp(20 + aer90 * 15),
        }
        note = (
            f"Derived from match statistics over {minutes} minutes: {s.passes_completed}/{s.passes_attempted} passes "
            f"({completion:.0%}), {s.tackles} tackles, {s.interceptions} interceptions, "
            f"{s.shots} shots, {s.dribbles} dribbles, {s.aerial_duels} aerial duels, "
            f"{s.sprints} sprints (physical output is estimated from event data)."
        )
        return radar, note

    # manual
    attrs = req.manual_attributes or {}
    radar = {str(k): _clamp(float(v)) for k, v in attrs.items() if _is_number(v)}
    if not radar:
        radar = {"Speed": 70, "Passing": 70, "Shooting": 70, "Defending": 70, "Physical": 70}
        return radar, "Default average scout ratings were applied (no attributes given)."
    return radar, "Derived from manual scout ratings."


def _radar_from_tracking(tracking: dict, track_id) -> tuple:
    """Estimate physical/tactical attributes from tracked movement."""
    frames = tracking.get("frames", []) or []
    method = tracking.get("method", "synthetic")

    # Pick a player: requested id, else the most-seen id on team A
    positions = []
    chosen = track_id
    if frames:
        counts: dict = {}
        for f in frames:
            for p in f.get("team_a", []) + f.get("team_b", []):
                counts[p["id"]] = counts.get(p["id"], 0) + 1
        if chosen is None and counts:
            chosen = max(counts, key=counts.get)
        for f in frames:
            for p in f.get("team_a", []) + f.get("team_b", []):
                if p["id"] == chosen:
                    positions.append((float(p["x"]), float(p["y"])))

    if len(positions) >= 2:
        import numpy as np
        arr = np.array(positions)
        steps = np.linalg.norm(np.diff(arr, axis=0), axis=1)
        total = float(steps.sum())
        top = float(np.percentile(steps, 95)) if steps.size else 0.0
        mean = float(steps.mean())
        avg_x = float(arr[:, 0].mean())
        spread_y = float(arr[:, 1].std())
        radar = {
            "Speed":       _clamp(45 + top * 12),
            "Stamina":     _clamp(40 + total / max(1, len(steps)) * 15 + min(30, len(steps) * 0.3)),
            "Work Rate":   _clamp(40 + mean * 18),
            "Positioning": _clamp(60 + (20 - abs(avg_x - 60)) * 0.8),
            "Attacking":   _clamp(30 + max(0, avg_x - 40) * 1.1),
            "Defending":   _clamp(30 + max(0, 80 - avg_x) * 1.0),
            "Dribbling":   _clamp(45 + spread_y * 1.5),
        }
        note = (
            f"Derived from {len(positions)} tracked frames "
            f"({'YOLOv8 detection' if method == 'yolo' else 'synthetic tracking fallback'}): "
            f"average station x={avg_x:.0f}, total displacement {total:.0f} units."
        )
        return radar, note

    radar = {"Speed": 78, "Stamina": 74, "Work Rate": 76, "Positioning": 72, "Attacking": 68, "Defending": 60}
    return radar, "Tracking produced too few frames; representative baseline attributes applied."


def _is_number(v) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


# ── Role inference ────────────────────────────────────────────────

def _canonical(radar: dict) -> dict:
    """Map arbitrary attribute names onto the canonical role-model vocabulary."""
    canon: dict = {}
    for k, v in radar.items():
        key = _ALIASES.get(k.strip().lower(), k.strip().title())
        canon[key] = max(canon.get(key, 0), float(v))
    # Stat-derived radars have no explicit Shooting / Speed axis: borrow the closest one
    if "Shooting" not in canon and "Attacking" in canon:
        canon["Shooting"] = canon["Attacking"]
    if "Speed" not in canon and "Physical" in canon:
        canon["Speed"] = canon["Physical"]
    # Fill missing canonical attributes with a neutral value so all roles are comparable
    for attr in ("Speed", "Physical", "Passing", "Dribbling", "Shooting", "Defending", "Attacking", "Aerial"):
        canon.setdefault(attr, 50.0)
    return canon


# Roles that are compatible with each position group (a scout never labels a
# striker as a centre-back because the numbers happen to line up)
_POSITION_ROLES = {
    "defender":   {"Ball-Playing Centre-Back", "Full-Back / Wing-Back", "Ball-Winning Midfielder"},
    "midfielder": {"Ball-Winning Midfielder", "Deep-Lying Playmaker", "Box-to-Box Midfielder", "Advanced Playmaker"},
    "attacker":   {"Advanced Playmaker", "Inverted Winger", "Inside Forward", "Target Striker", "Complete Forward"},
}
_POSITION_GROUP = {
    "GK": None, "CB": "defender", "RB": "defender", "LB": "defender", "RWB": "defender", "LWB": "defender",
    "CDM": "midfielder", "CM": "midfielder", "RM": "midfielder", "LM": "midfielder",
    "CAM": "attacker", "RW": "attacker", "LW": "attacker", "ST": "attacker", "CF": "attacker",
}


def _infer_role(radar: dict, position: str = None) -> tuple:
    canon = _canonical(radar)
    group = _POSITION_GROUP.get((position or "").upper())
    compatible = _POSITION_ROLES.get(group) if group else None
    scores = {}
    for role, weights in ROLE_PROFILES.items():
        scores[role] = sum(canon.get(attr, 50) * w for attr, w in weights.items())
    # With a known position, only roles that position can actually play are eligible;
    # a quiet game for a forward must not turn them into a centre-back.
    eligible = [r for r in scores if compatible is None or r in compatible] or list(scores)
    best = max(eligible, key=lambda r: scores[r])
    return best, scores


def _strengths_weaknesses(radar: dict) -> tuple:
    ordered = sorted(radar.items(), key=lambda kv: -float(kv[1]))
    strengths = [f"{k} ({int(v)})" for k, v in ordered[:2]]
    weaknesses = [f"{k} ({int(v)})" for k, v in ordered[-2:]] if len(ordered) > 2 else []
    return strengths, weaknesses


def _template_report(req, radar, role, strengths, weaknesses, note) -> str:
    avg = sum(radar.values()) / max(1, len(radar))
    tier = "elite" if avg >= 82 else "strong" if avg >= 70 else "developing" if avg >= 55 else "raw"
    age_note = (
        "with significant room to grow" if req.age and req.age <= 21
        else "entering peak years" if req.age and req.age <= 29
        else "bringing experience to the group"
    )
    top = strengths[0].split(" (")[0] if strengths else "all-round ability"
    weak = weaknesses[0].split(" (")[0] if weaknesses else "consistency"
    pos = f", {req.position.upper()}" if req.position else ""
    return (
        f"{req.name} (#{req.number}{pos}, {req.age}, {req.preferred_foot}-footed, {req.height}/{req.weight}) "
        f"profiles as a {tier} {role.lower()} {age_note}. "
        f"The standout attribute is {top.lower()}, which makes this player most effective when the "
        f"system puts them in situations that reward it. "
        f"The clearest development area is {weak.lower()}; a coaching plan should target it before "
        f"expanding the tactical brief. {note}"
    )


async def _llm_enhance(req, radar, role, strengths, weaknesses, note):
    prompt = (
        "Act as a professional football scout. Using the data below, answer in EXACTLY this format:\n"
        "Role: <best tactical role>\n"
        "Report: <3 sentence scouting report>\n"
        "Strengths: <s1>, <s2>\n"
        "Weaknesses: <w1>, <w2>\n\n"
        f"Player: {req.name}, #{req.number}, age {req.age}, {req.preferred_foot} foot, {req.height}, {req.weight}.\n"
        f"Attribute radar (0-100): {radar}\n"
        f"Rule-based role estimate: {role}\n"
        f"Data source: {note}"
    )
    try:
        answer, mode = await ask_llm(prompt, context=None)
    except Exception:
        return "", "", [], []
    if mode == "knowledge_graph":
        return "", "", [], []

    llm_role, llm_report, llm_str, llm_weak = "", "", [], []
    for line in answer.splitlines():
        line = line.strip()
        if line.lower().startswith("role:"):
            llm_role = line.split(":", 1)[1].strip()
        elif line.lower().startswith("report:"):
            llm_report = line.split(":", 1)[1].strip()
        elif line.lower().startswith("strengths:"):
            llm_str = [s.strip() for s in line.split(":", 1)[1].split(",") if s.strip()]
        elif line.lower().startswith("weaknesses:"):
            llm_weak = [w.strip() for w in line.split(":", 1)[1].split(",") if w.strip()]
    if not llm_report:
        llm_report = answer.strip()
    return llm_report, llm_role, llm_str, llm_weak
