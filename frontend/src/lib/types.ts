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

// ── API Request types ───────────────────────────────────────────

export interface BaseAnalysisRequest {
  input_type: "manual" | "video" | "dataset";
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
}

// ── API Response types ──────────────────────────────────────────

export interface VisualizationData {
  image_base64: string;
  title: string;
  description?: string;
}

export interface FeatureApiResponse {
  feature?: string;
  success: boolean;
  data: Record<string, unknown>;
  visualizations: VisualizationData[];
  insights: string[];
  recommendations: string[];
  error?: string | null;
  // Additional fields from specific response types
  [key: string]: unknown;
}

export interface HealthResponse {
  status: string;
  version: string;
  engine_phases: number;
  llm_available: boolean;
  available_tactics: string[];
}

export interface AskResponse {
  success: boolean;
  question: string;
  answer: string;
  mode: string;
  error?: string | null;
}

export interface SimulationResponse {
  success: boolean;
  tactic_a: string;
  tactic_b: string;
  goals_a: number;
  goals_b: number;
  possession_a: number;
  possession_b: number;
  territorial_control_a: number;
  steps: number;
  events: Record<string, unknown>[];
  error?: string | null;
}

export interface SimulationCompareResponse {
  success: boolean;
  matchup_1: Record<string, unknown>;
  matchup_2: Record<string, unknown>;
  verdict: string;
  error?: string | null;
}

export interface VideoResponse {
  success: boolean;
  tracking_data?: {
    team_a: Record<string, unknown>[];
    team_b: Record<string, unknown>[];
    frames_processed: number;
    method: string;
  };
  message?: string;
  error?: string | null;
}

// ── Supabase / App types ────────────────────────────────────────

export interface UserProfile {
  id: string;
  email: string;
  full_name?: string;
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
  inputType: "manual" | "video" | "dataset";
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
  minPasses?: number;
  vizMode?: "Both" | "Influence" | "Voronoi";
  pressureRadius?: number;
  analyzeTeam?: "Both" | "Team A" | "Team B";
}
