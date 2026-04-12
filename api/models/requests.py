"""
SpaceAI FC - Request Models
==============================
Pydantic input models for all API endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ── Shared primitives ────────────────────────────────────────────

class PlayerData(BaseModel):
    name: str
    number: int
    x: float = Field(..., ge=0.0, le=120.0)
    y: float = Field(..., ge=0.0, le=80.0)
    position: str  # GK, CB, RB, LB, CM, CAM, CDM, RW, LW, ST, etc.
    # Optional per-player stats (used by role classifier and press resistance)
    passes_made: Optional[int] = None
    passes_received: Optional[int] = None
    defensive_actions: Optional[int] = None
    touches_in_box: Optional[int] = None


class PassEvent(BaseModel):
    passer: int
    receiver: int
    success: bool = True
    x: float = Field(0.0, ge=0.0, le=120.0)
    y: float = Field(0.0, ge=0.0, le=80.0)
    end_x: float = Field(0.0, ge=0.0, le=120.0)
    end_y: float = Field(0.0, ge=0.0, le=80.0)


class MatchInfo(BaseModel):
    home_team: str = "Home"
    away_team: str = "Away"
    score_home: int = 0
    score_away: int = 0
    minute: int = Field(0, ge=0, le=120)
    competition: str = ""
    date: str = ""


# ── Base analysis request ─────────────────────────────────────────

class BaseAnalysisRequest(BaseModel):
    input_type: str = Field("manual", pattern="^(manual|video|dataset)$")
    match_info: Optional[MatchInfo] = None
    team_a_name: str = "Team A"
    team_b_name: str = "Team B"
    team_a_color: str = "#e74c3c"
    team_b_color: str = "#3498db"
    # Manual input
    team_a: Optional[List[PlayerData]] = None
    team_b: Optional[List[PlayerData]] = None
    passes: Optional[List[PassEvent]] = None
    ball_x: float = Field(60.0, ge=0.0, le=120.0)
    ball_y: float = Field(40.0, ge=0.0, le=80.0)
    # File references (populated by upload endpoints)
    video_file: Optional[str] = None
    youtube_url: Optional[str] = None
    dataset_file: Optional[str] = None


# ── Full pipeline ────────────────────────────────────────────────

class AnalysisRequest(BaseAnalysisRequest):
    """Full match analysis — runs entire engine pipeline."""
    pass


class TacticalAnalysisRequest(BaseAnalysisRequest):
    """Tactical analysis — formation, space control, passes."""
    pass


# ── Individual feature requests ──────────────────────────────────

class PassNetworkRequest(BaseAnalysisRequest):
    min_passes: int = Field(2, ge=1, le=20)
    sequence: Optional[List[int]] = None  # optional pass sequence viz


class SpaceControlRequest(BaseAnalysisRequest):
    mode: str = Field("both", pattern="^(voronoi|influence|both)$")
    sigma: float = Field(15.0, ge=5.0, le=30.0)


class FormationRequest(BaseAnalysisRequest):
    method: str = Field("auto", pattern="^(auto|clustering|gap)$")


class RolesRequest(BaseAnalysisRequest):
    pass


class PressResistanceRequest(BaseAnalysisRequest):
    pressure_radius: float = Field(10.0, ge=3.0, le=25.0)
    pressure_threshold: int = Field(2, ge=1, le=5)


class PatternsRequest(BaseAnalysisRequest):
    analyze_team: str = Field("a", pattern="^(a|b|both)$")


# ── Intelligence requests ─────────────────────────────────────────

class KnowledgeGraphRequest(BaseModel):
    formation: Optional[str] = None
    situation: Optional[str] = None


class ReasoningRequest(BaseAnalysisRequest):
    # Can receive pre-computed analysis data or compute fresh
    pass


class RecommendationsRequest(BaseModel):
    swot_results: Optional[dict] = None
    analysis_data: Optional[dict] = None
    team_name: str = "Team A"
    opponent_name: str = "Team B"


class ExplanationRequest(BaseModel):
    mode: str = Field("template", pattern="^(template|llm)$")
    match_info: Optional[dict] = None
    report_data: Optional[dict] = None
    swot_results: Optional[dict] = None
    recommendations: Optional[list] = None
    team_name: str = "Team A"
    opponent_name: str = "Team B"


# ── Video requests ────────────────────────────────────────────────

class YouTubeRequest(BaseModel):
    url: str
    demo_mode: bool = False  # use synthetic data even if yt-dlp available


class TrackPlayerRequest(BaseModel):
    video_data: dict  # from upload/youtube endpoint
    player_id: int


# ── Simulation / RL requests ──────────────────────────────────────

VALID_TACTICS = {"high_press", "low_block", "wide_play", "narrow_play",
                 "counter_attack", "possession"}


class SimulationRequest(BaseModel):
    team_size: int = Field(5, ge=5, le=7)
    tactic_a: str = "possession"
    tactic_b: str = "low_block"
    steps: int = Field(300, ge=50, le=2000)
    seed: int = 42

    @field_validator("tactic_a", "tactic_b")
    @classmethod
    def validate_tactic(cls, v: str) -> str:
        if v not in VALID_TACTICS:
            raise ValueError(f"tactic must be one of {sorted(VALID_TACTICS)}")
        return v


class SimulationCompareRequest(BaseModel):
    team_size: int = Field(5, ge=5, le=7)
    tactic_a: str = "possession"
    tactic_b: str = "low_block"
    tactic_a2: str = "high_press"
    tactic_b2: str = "counter_attack"
    runs: int = Field(3, ge=1, le=10)
    steps_per_run: int = Field(300, ge=50, le=1000)

    @field_validator("tactic_a", "tactic_b", "tactic_a2", "tactic_b2")
    @classmethod
    def validate_tactic(cls, v: str) -> str:
        if v not in VALID_TACTICS:
            raise ValueError(f"tactic must be one of {sorted(VALID_TACTICS)}")
        return v


class RLMatchState(BaseModel):
    own_formation: int = Field(0, ge=0, le=5)
    opp_formation: int = Field(0, ge=0, le=5)
    space_control: float = Field(50.0, ge=0.0, le=100.0)
    press_resistance: float = Field(55.0, ge=0.0, le=100.0)
    score_diff: int = Field(0, ge=-5, le=5)
    minute: int = Field(0, ge=0, le=90)
    possession: float = Field(50.0, ge=0.0, le=100.0)


class RLTrainRequest(BaseModel):
    timesteps: int = Field(10_000, ge=1_000, le=500_000)
    seed: int = 42


# ── Ask SpaceAI ──────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    match_context: Optional[dict] = None  # optional analysis results for context
    team_name: str = "Team A"
    opponent_name: str = "Team B"


# ── Export ───────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    analysis_data: dict
    match_info: Optional[dict] = None
    team_name: str = "Team A"
    opponent_name: str = "Team B"
