/**
 * SpaceAI FC — Shared TypeScript types
 * =====================================
 * Mirrors the FastAPI Pydantic models in api/models/
 */

// ── Player & Match primitives ───────────────────────────────────

export interface PlayerData {
  name: string;
  number: number;
  x: number;
  y: number;
  position: string;
  passes_made?: number;
  passes_received?: number;
  defensive_actions?: number;
  touches_in_box?: number;
}

export interface PassEvent {
  passer: number;
  receiver: number;
  success?: boolean;
  x?: number;
  y?: number;
  end_x?: number;
  end_y?: number;
}

export interface MatchInfo {
  home_team?: string;
  away_team?: string;
  score_home?: number;
  score_away?: number;
  minute?: number;
  competition?: string;
  date?: string;
}

// ── Frontend form player (string values from inputs) ────────────

export interface FormPlayer {
  name: string;
  number: string;
  x: string;
  y: string;
  position: string;
}

export type InputType = "manual" | "video" | "dataset";

// ── API Request types ───────────────────────────────────────────

export interface BaseAnalysisRequest {
  input_type: InputType;
  match_info?: MatchInfo;
  team_a_name?: string;
  team_b_name?: string;
  team_a_color?: string;
  team_b_color?: string;
  team_a?: PlayerData[];
  team_b?: PlayerData[];
  passes?: PassEvent[];
  ball_x?: number;
  ball_y?: number;
  video_file?: string;
  youtube_url?: string;
  dataset_file?: string;
}

export interface SimulationRequest {
  team_size?: number;
  tactic_a?: string;
  tactic_b?: string;
  steps?: number;
  seed?: number;
}

export interface SimulationCompareRequest {
  team_size?: number;
  tactic_a?: string;
  tactic_b?: string;
  tactic_a2?: string;
  tactic_b2?: string;
  runs?: number;
  steps_per_run?: number;
}

export interface AskRequest {
  question: string;
  match_context?: Record<string, unknown>;
  team_name?: string;
  opponent_name?: string;
}

export interface ExportRequest {
  analysis_data: Record<string, unknown>;
  match_info?: Record<string, unknown>;
  team_name?: string;
  opponent_name?: string;
  team_a_color?: string;
  team_b_color?: string;
  team_a?: PlayerData[];
  team_b?: PlayerData[];
  passes?: PassEvent[];
  ball_x?: number;
  ball_y?: number;
  feature?: string;
}

// ── API Response types ──────────────────────────────────────────

export interface VisualizationData {
  image_base64: string;
  title: string;
  description?: string;
}

export interface PlayerRoleItem {
  name: string;
  number: number;
  position: string;
  role: string;
  confidence: number;
  reasoning: string;
}

export interface PatternItem {
  name: string;
  detected: boolean;
  confidence: number;
  description: string;
  involved_players: string[];
}

export interface SWOTItem {
  category: string;
  description: string;
  confidence: number;
  source?: string;
}

export interface RecommendationItem {
  priority: "high" | "medium" | "low" | string;
  category: string;
  description: string;
  reasoning: string;
  expected_impact: string;
}

export interface FormationResponse {
  success: boolean;
  team_a_formation?: string | null;
  team_a_confidence?: number | null;
  team_a_method?: string | null;
  team_b_formation?: string | null;
  team_b_confidence?: number | null;
  team_b_method?: string | null;
  visualizations: VisualizationData[];
}

export interface SpaceControlResponse {
  success: boolean;
  team_a_control: number;
  team_b_control: number;
  zones: Record<string, { team_a: number; team_b: number }>;
  midfield_control: Record<string, number>;
  visualizations: VisualizationData[];
}

export interface PassNetworkResponse {
  success: boolean;
  total_passes: number;
  key_distributor: Record<string, unknown>;
  most_involved: Record<string, unknown>;
  top_connections: Array<Record<string, unknown>>;
  weak_links: Array<Record<string, unknown>>;
  centrality: Record<string, Record<string, unknown>>;
  visualizations: VisualizationData[];
}

export interface PressResistanceResponse {
  success: boolean;
  press_resistance_score: number;
  total_passes: number;
  passes_under_pressure: number;
  pass_success_overall: number;
  pass_success_under_pressure: number;
  escape_rate: number;
  vulnerable_zones: Array<Record<string, unknown>>;
  visualizations: VisualizationData[];
}

export interface PatternsResponse {
  success: boolean;
  team_a_patterns: PatternItem[];
  team_b_patterns: PatternItem[];
  visualizations: VisualizationData[];
}

export interface RolesResponse {
  success: boolean;
  team_a_roles: PlayerRoleItem[];
  team_b_roles: PlayerRoleItem[];
  visualizations: VisualizationData[];
}

export interface IntelligenceResponse {
  success: boolean;
  swot: SWOTItem[];
  recommendations: RecommendationItem[];
  knowledge_graph_insights: string[];
  situations: string[];
  formation_a?: string | null;
  formation_b?: string | null;
  visualizations: VisualizationData[];
}

export interface ExplanationResponse {
  success: boolean;
  mode: string;
  text: string;
  sections: string[];
  summary: Record<string, unknown>;
  visualizations: VisualizationData[];
}

export interface FullAnalysisResponse {
  success: boolean;
  match_info: Record<string, unknown>;
  formation?: FormationResponse | null;
  space_control?: SpaceControlResponse | null;
  pass_network?: PassNetworkResponse | null;
  press_resistance?: PressResistanceResponse | null;
  patterns?: PatternsResponse | null;
  roles?: RolesResponse | null;
  intelligence?: IntelligenceResponse | null;
  explanation?: ExplanationResponse | null;
  visualizations: VisualizationData[];
}

/** Union of every analysis response; pages narrow by feature id. */
export type FeatureApiResponse = {
  success: boolean;
  visualizations?: VisualizationData[];
  error?: string | null;
  [key: string]: unknown;
};

export interface HealthResponse {
  status: string;
  version: string;
  engine_phases: number;
  llm_available: boolean;
  llm_provider: string;
  available_tactics: string[];
  capabilities: Record<string, boolean>;
}

export interface AskResponse {
  success: boolean;
  question: string;
  answer: string;
  mode: string;
  error?: string | null;
}

export interface SimulationFrame {
  step: number;
  a: [number, number][];
  b: [number, number][];
  ball: [number, number];
  pos: "A" | "B" | null;
}

export interface SimulationEvent {
  step: number;
  type: string;
  team: "A" | "B";
  player?: number | null;
  role?: string | null;
}

export interface SimulationResponse {
  success: boolean;
  tactic_a: string;
  tactic_b: string;
  tactic_a_key: string;
  tactic_b_key: string;
  goals_a: number;
  goals_b: number;
  possession_a: number;
  possession_b: number;
  territorial_control_a: number;
  territorial_control_b: number;
  steps: number;
  team_size: number;
  pitch_width: number;
  pitch_height: number;
  events: SimulationEvent[];
  frames: SimulationFrame[];
  error?: string | null;
}

export interface MatchupSummary {
  tactic_a: string;
  tactic_b: string;
  avg_goals_a: number;
  avg_goals_b: number;
  avg_possession_a: number;
  avg_territorial_control_a: number;
  runs: number;
}

export interface SimulationCompareResponse {
  success: boolean;
  matchup_1: MatchupSummary;
  matchup_2: MatchupSummary;
  verdict: string;
  error?: string | null;
}

export interface VideoTrackingData {
  team_a: PlayerData[];
  team_b: PlayerData[];
  frames_processed: number;
  method: string;
}

export interface VideoResponse {
  success: boolean;
  tracking_data?: VideoTrackingData;
  message?: string;
  error?: string | null;
}

export interface DatasetResponse {
  success: boolean;
  team_a: PlayerData[];
  team_b: PlayerData[];
  passes: PassEvent[];
  match_info: Record<string, unknown>;
  format: string;
  message: string;
  error?: string | null;
}

export interface PlayerAssessmentResponse {
  success: boolean;
  recommended_role: string;
  radar_data: Record<string, number>;
  scouting_report: string;
  strengths: string[];
  weaknesses: string[];
  error?: string | null;
}

// ── Demo matches (data/demo_matches/*.json) ─────────────────────

export interface DemoMatchSummary {
  id: string;
  title: string;
  subtitle: string;
  date: string;
  competition: string;
  team_a: string;
  team_b: string;
  score: { a: number; b: number };
  source_kind: "statsbomb" | "reconstructed" | string;
  formation_a?: string;
  formation_b?: string;
  players: number;
  passes: number;
}

export interface DemoMatch {
  id: string;
  title: string;
  subtitle: string;
  competition: string;
  date: string;
  team_a: { name: string; color: string; formation?: string };
  team_b: { name: string; color: string; formation?: string };
  score: { a: number; b: number };
  players_a: PlayerData[];
  players_b: PlayerData[];
  passes: PassEvent[];
  ball: { x: number; y: number };
  match_info: MatchInfo;
  source: { kind: string; match_id: number | null; note: string };
}

export interface DemoPlayer {
  id: string;
  match: string;
  team: string;
  name: string;
  number: number;
  age: number;
  foot: string;
  height: string;
  weight: string;
  position: string;
  stats: {
    passes_completed: number; passes_attempted: number; tackles: number; interceptions: number;
    shots: number; dribbles: number; aerial_duels: number; distance_covered: number; sprints: number;
    minutes?: number; carry_distance_m?: number;
  };
  match_title: string;
  match_subtitle: string;
  source: { kind: string; note: string };
}

// ── Supabase / App types ────────────────────────────────────────

export interface UserProfile {
  id: string;
  email: string;
  full_name?: string;
  isGuest?: boolean;
}

export interface SavedAnalysis {
  id: string;
  user_id: string;
  match_name: string;
  feature: string;
  input_data: Record<string, unknown>;
  results: Record<string, unknown>;
  created_at: string;
}

// ── Form data passed from FeaturePageInput → App ────────────────

export interface AnalysisFormData {
  inputType: InputType;
  teamAPlayers: FormPlayer[];
  teamBPlayers: FormPlayer[];
  teamAName: string;
  teamBName: string;
  teamAColor: string;
  teamBColor: string;
  ballX: string;
  ballY: string;
  passesText?: string;
  videoFile?: File;
  youtubeUrl?: string;
  datasetFile?: File;
  /** Players resolved from a dataset / video upload (already numeric). */
  resolvedTeamA?: PlayerData[];
  resolvedTeamB?: PlayerData[];
  resolvedPasses?: PassEvent[];
  resolvedNote?: string;
  /** Pass events with real coordinates (from a demo match); overrides passesText when set. */
  manualPasses?: PassEvent[];
  /** Label of the loaded demo fixture, shown on the results page. */
  demoMatch?: { id: string; title: string; subtitle: string; sourceKind: string; note?: string; formationA?: string; formationB?: string };
  minPasses?: number;
  vizMode?: "both" | "influence" | "voronoi";
  pressureRadius?: number;
  analyzeTeam?: "both" | "a" | "b";
  situation?: string;
  explanationMode?: "template" | "llm";
  matchInfo?: MatchInfo;
}
