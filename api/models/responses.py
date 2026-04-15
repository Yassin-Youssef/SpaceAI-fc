"""
SpaceAI FC - Response Models
==============================
Pydantic output models for all API endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# ── Shared primitives ────────────────────────────────────────────

class VisualizationData(BaseModel):
    image_base64: str
    title: str
    description: str = ""


class FeatureResponse(BaseModel):
    feature: str
    success: bool
    data: Dict[str, Any]
    visualizations: List[VisualizationData] = []
    insights: List[str] = []
    recommendations: List[str] = []
    error: Optional[str] = None


# ── Health / features ────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    engine_phases: int
    llm_available: bool
    available_tactics: List[str]


class FeatureInfoItem(BaseModel):
    endpoint: str
    description: str
    input_types: List[str]


class FeaturesListResponse(BaseModel):
    total: int
    features: List[FeatureInfoItem]


# ── Pass network ─────────────────────────────────────────────────

class PassNetworkResponse(BaseModel):
    success: bool
    total_passes: int
    key_distributor: Dict[str, Any]
    most_involved: Dict[str, Any]
    top_connections: List[Dict[str, Any]]
    weak_links: List[Dict[str, Any]]
    centrality: Dict[str, Any]
    visualizations: List[VisualizationData] = []
    error: Optional[str] = None


# ── Space control ────────────────────────────────────────────────

class SpaceControlResponse(BaseModel):
    success: bool
    team_a_control: float
    team_b_control: float
    zones: Dict[str, Any]
    midfield_control: Dict[str, Any]
    visualizations: List[VisualizationData] = []
    error: Optional[str] = None


# ── Formation ────────────────────────────────────────────────────

class FormationResponse(BaseModel):
    success: bool
    team_a_formation: Optional[str] = None
    team_a_confidence: Optional[float] = None
    team_a_method: Optional[str] = None
    team_b_formation: Optional[str] = None
    team_b_confidence: Optional[float] = None
    team_b_method: Optional[str] = None
    visualizations: List[VisualizationData] = []
    error: Optional[str] = None


# ── Roles ────────────────────────────────────────────────────────

class PlayerRoleItem(BaseModel):
    name: str
    number: int
    position: str
    role: str
    confidence: float
    reasoning: str


class RolesResponse(BaseModel):
    success: bool
    team_a_roles: List[PlayerRoleItem] = []
    team_b_roles: List[PlayerRoleItem] = []
    visualizations: List[VisualizationData] = []
    error: Optional[str] = None

class PlayerAssessmentResponse(BaseModel):
    success: bool
    recommended_role: str
    radar_data: Dict[str, float]
    scouting_report: str
    strengths: List[str] = []
    weaknesses: List[str] = []
    visualizations: List[VisualizationData] = []
    error: Optional[str] = None


# ── Press resistance ─────────────────────────────────────────────

class PressResistanceResponse(BaseModel):
    success: bool
    press_resistance_score: float
    total_passes: int
    passes_under_pressure: int
    pass_success_overall: float
    pass_success_under_pressure: float
    escape_rate: float
    vulnerable_zones: List[Dict[str, Any]] = []
    visualizations: List[VisualizationData] = []
    error: Optional[str] = None


# ── Patterns ─────────────────────────────────────────────────────

class PatternItem(BaseModel):
    name: str
    detected: bool
    confidence: float
    description: str
    involved_players: List[str] = []


class PatternsResponse(BaseModel):
    success: bool
    team_a_patterns: List[PatternItem] = []
    team_b_patterns: List[PatternItem] = []
    visualizations: List[VisualizationData] = []
    error: Optional[str] = None


# ── Intelligence ─────────────────────────────────────────────────

class SWOTItem(BaseModel):
    category: str  # strength / weakness / opportunity / threat
    description: str
    confidence: float
    source: str = ""


class RecommendationItem(BaseModel):
    priority: str  # high / medium / low
    category: str
    description: str
    reasoning: str
    expected_impact: str


class IntelligenceResponse(BaseModel):
    success: bool
    swot: List[SWOTItem] = []
    recommendations: List[RecommendationItem] = []
    knowledge_graph_insights: List[str] = []
    error: Optional[str] = None


class KnowledgeGraphResponse(BaseModel):
    success: bool
    formation: Optional[str] = None
    situation: Optional[str] = None
    counter_strategies: List[str] = []
    weaknesses: List[str] = []
    strengths: List[str] = []
    error: Optional[str] = None


# ── Explanation ──────────────────────────────────────────────────

class ExplanationResponse(BaseModel):
    success: bool
    mode: str
    text: str
    sections: List[str] = []
    error: Optional[str] = None


# ── Video ────────────────────────────────────────────────────────

class VideoTrackingData(BaseModel):
    team_a: List[Dict[str, Any]]
    team_b: List[Dict[str, Any]]
    frames_processed: int
    method: str  # "yolo" or "synthetic"


class VideoResponse(BaseModel):
    success: bool
    tracking_data: Optional[VideoTrackingData] = None
    message: str = ""
    error: Optional[str] = None


class PlayerTrackResponse(BaseModel):
    success: bool
    player_id: int
    trajectory: List[Dict[str, Any]] = []
    heatmap_base64: Optional[str] = None
    total_distance: float = 0.0
    avg_speed: float = 0.0
    error: Optional[str] = None


# ── Simulation ───────────────────────────────────────────────────

class SimulationResponse(BaseModel):
    success: bool
    tactic_a: str
    tactic_b: str
    goals_a: int
    goals_b: int
    possession_a: float
    possession_b: float
    territorial_control_a: float
    steps: int
    events: List[Dict[str, Any]] = []
    error: Optional[str] = None


class SimulationCompareResponse(BaseModel):
    success: bool
    matchup_1: Dict[str, Any]
    matchup_2: Dict[str, Any]
    verdict: str
    error: Optional[str] = None


# ── RL coach ─────────────────────────────────────────────────────

class RLPredictResponse(BaseModel):
    success: bool
    action_id: int
    action_name: str
    state: Dict[str, Any]
    available: bool  # False if RL deps not installed
    error: Optional[str] = None


class RLTrainResponse(BaseModel):
    success: bool
    timesteps: int
    episodes_trained: int
    avg_reward: float
    error: Optional[str] = None


# ── Ask SpaceAI ──────────────────────────────────────────────────

class AskResponse(BaseModel):
    success: bool
    question: str
    answer: str
    mode: str  # "llm" or "knowledge_graph"
    error: Optional[str] = None


# ── Full analysis ────────────────────────────────────────────────

class FullAnalysisResponse(BaseModel):
    success: bool
    match_info: Dict[str, Any] = {}
    formation: Optional[FormationResponse] = None
    space_control: Optional[SpaceControlResponse] = None
    pass_network: Optional[PassNetworkResponse] = None
    press_resistance: Optional[PressResistanceResponse] = None
    patterns: Optional[PatternsResponse] = None
    roles: Optional[RolesResponse] = None
    intelligence: Optional[IntelligenceResponse] = None
    explanation: Optional[ExplanationResponse] = None
    visualizations: List[VisualizationData] = []
    error: Optional[str] = None
