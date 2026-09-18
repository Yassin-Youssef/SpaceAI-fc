/**
 * SpaceAI FC — FastAPI Backend Client
 * ====================================
 * All API communication via native fetch.
 * Backend: http://localhost:8000/api (override with VITE_API_URL)
 */

import type {
  FormPlayer,
  PlayerData,
  PassEvent,
  BaseAnalysisRequest,
  FeatureApiResponse,
  HealthResponse,
  AskResponse,
  SimulationRequest,
  SimulationResponse,
  SimulationCompareRequest,
  SimulationCompareResponse,
  VideoResponse,
  DatasetResponse,
  ExportRequest,
  AnalysisFormData,
  PlayerAssessmentResponse,
  DemoMatchSummary,
  DemoMatch,
  DemoPlayer,
} from "./types";

export const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) || "http://localhost:8000/api";

/** Human-readable base URL (without the /api suffix) for status messages. */
export const API_ORIGIN = API_BASE.replace(/\/api\/?$/, "");

// ── Errors ──────────────────────────────────────────────────────

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function friendlyNetworkError(err: unknown): Error {
  if (err instanceof ApiError) return err;
  if (err instanceof TypeError) {
    return new ApiError(
      `Cannot reach the SpaceAI FC backend at ${API_ORIGIN}. Start it with "uvicorn api.main:app --port 8000".`,
      0
    );
  }
  return err instanceof Error ? err : new Error(String(err));
}

async function parseError(res: Response): Promise<never> {
  let detail = res.statusText || `HTTP ${res.status}`;
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") detail = data.detail;
    else if (Array.isArray(data?.detail)) {
      // FastAPI validation errors
      detail = data.detail
        .map((d: { loc?: unknown[]; msg?: string }) => `${(d.loc ?? []).slice(1).join(".")}: ${d.msg}`)
        .join("; ");
    }
  } catch {
    /* ignore */
  }
  if (res.status === 429) detail = "Too many requests. Please wait a moment and try again.";
  throw new ApiError(detail, res.status);
}

// ── Helpers ─────────────────────────────────────────────────────

/** Convert base64 string to a renderable image URL */
export function base64ToImageUrl(base64: string): string {
  if (!base64) return "";
  if (base64.startsWith("data:")) return base64;
  return `data:image/png;base64,${base64}`;
}

/** Convert frontend form players (string values) to backend PlayerData (numeric). */
export function toPlayerData(players: FormPlayer[]): PlayerData[] {
  return players
    .filter((p) => p.name.trim() !== "" || p.x.trim() !== "" || p.y.trim() !== "")
    .map((p, i) => ({
      name: p.name.trim() || `Player ${i + 1}`,
      number: parseInt(p.number, 10) || i + 1,
      x: clamp(parseFloat(p.x), 0, 120),
      y: clamp(parseFloat(p.y), 0, 80),
      position: (p.position || "CM").toUpperCase(),
    }));
}

function clamp(v: number, lo: number, hi: number): number {
  if (Number.isNaN(v)) return (lo + hi) / 2;
  return Math.min(hi, Math.max(lo, v));
}

/**
 * Parse pass events from free text.
 * Accepts "4->8", "4->8->1" (success flag), "4,8", "4,8,0", separated by commas,
 * semicolons or new lines.  Origin/destination coordinates are filled in from
 * the passer's and receiver's positions so the press-resistance engine has
 * real locations to work with.
 */
export function parsePassesText(text: string | undefined, players: PlayerData[]): PassEvent[] {
  if (!text) return [];
  const byNumber = new Map(players.map((p) => [p.number, p]));
  const passes: PassEvent[] = [];

  const tokens = text
    .split(/[\n;]+|,(?=\s*\d+\s*(?:->|→|>))/)
    .map((t) => t.trim())
    .filter(Boolean);

  for (const token of tokens) {
    const parts = token.split(/->|→|>|,/).map((s) => s.trim()).filter(Boolean);
    if (parts.length < 2) continue;
    const passer = parseInt(parts[0], 10);
    const receiver = parseInt(parts[1], 10);
    if (Number.isNaN(passer) || Number.isNaN(receiver)) continue;
    const flag = parts[2];
    const success = flag === undefined ? true : !/^(0|false|f|n|no|fail)$/i.test(flag);
    const from = byNumber.get(passer);
    const to = byNumber.get(receiver);
    passes.push({
      passer,
      receiver,
      success,
      x: from?.x ?? 60,
      y: from?.y ?? 40,
      end_x: to?.x ?? 60,
      end_y: to?.y ?? 40,
    });
  }
  return passes;
}

/** Fill in pass coordinates for passes that came from a dataset without them. */
function hydratePasses(passes: PassEvent[], players: PlayerData[]): PassEvent[] {
  const byNumber = new Map(players.map((p) => [p.number, p]));
  return passes.map((p) => {
    const hasCoords = (p.x ?? 0) !== 0 || (p.y ?? 0) !== 0 || (p.end_x ?? 0) !== 0;
    if (hasCoords) return p;
    const from = byNumber.get(p.passer);
    const to = byNumber.get(p.receiver);
    return { ...p, x: from?.x ?? 60, y: from?.y ?? 40, end_x: to?.x ?? 60, end_y: to?.y ?? 40 };
  });
}

async function request<T>(endpoint: string, init: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${endpoint}`, init);
  } catch (err) {
    throw friendlyNetworkError(err);
  }
  if (!res.ok) await parseError(res);
  return res.json() as Promise<T>;
}

async function post<T>(endpoint: string, body: unknown): Promise<T> {
  return request<T>(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function get<T>(endpoint: string): Promise<T> {
  return request<T>(endpoint, { method: "GET" });
}

// ── Feature ID → Endpoint mapping ───────────────────────────────

export const FEATURE_ENDPOINTS: Record<string, string> = {
  "full-match": "/analyze",
  "pass-network": "/pass-network",
  "space-control": "/space-control",
  formation: "/formation",
  roles: "/roles",
  "press-resistance": "/press-resistance",
  patterns: "/patterns",
  strategy: "/recommendations",
  explanation: "/explanation",
};

/** Which features need an opponent (team B). */
export const FEATURES_NEEDING_TEAM_B = new Set([
  "full-match", "space-control", "press-resistance", "patterns", "strategy", "explanation",
]);

/** Which features use pass events. */
export const FEATURES_WITH_PASSES = new Set([
  "full-match", "pass-network", "press-resistance", "strategy", "explanation",
]);

// ── Resolve players from any input method ───────────────────────

export interface ResolvedInput {
  teamA: PlayerData[];
  teamB: PlayerData[];
  passes: PassEvent[];
  note?: string;
}

/**
 * Turn the form into engine-ready players regardless of input method.
 * Video and dataset inputs are uploaded first; the returned players are then
 * sent as manual coordinates to the analysis endpoint.
 */
export async function resolveFormInput(formData: AnalysisFormData): Promise<ResolvedInput> {
  if (formData.inputType === "video") {
    if (formData.resolvedTeamA?.length) {
      return {
        teamA: formData.resolvedTeamA,
        teamB: formData.resolvedTeamB ?? [],
        passes: formData.resolvedPasses ?? [],
        note: formData.resolvedNote,
      };
    }
    let res: VideoResponse;
    if (formData.videoFile) {
      res = await uploadVideo(formData.videoFile);
    } else if (formData.youtubeUrl?.trim()) {
      res = await processYouTube(formData.youtubeUrl.trim());
    } else {
      throw new ApiError("Choose a video file or paste a YouTube link first.", 400);
    }
    if (!res.success || !res.tracking_data) {
      throw new ApiError(res.message || "No tracking data could be extracted from the video.", 400);
    }
    return {
      teamA: res.tracking_data.team_a,
      teamB: res.tracking_data.team_b,
      passes: [],
      note: res.message,
    };
  }

  if (formData.inputType === "dataset") {
    if (formData.resolvedTeamA?.length) {
      const teamA = formData.resolvedTeamA;
      return {
        teamA,
        teamB: formData.resolvedTeamB ?? [],
        passes: hydratePasses(formData.resolvedPasses ?? [], teamA),
        note: formData.resolvedNote,
      };
    }
    if (!formData.datasetFile) {
      throw new ApiError("Choose a CSV or JSON dataset first.", 400);
    }
    const res = await uploadDataset(formData.datasetFile);
    return {
      teamA: res.team_a,
      teamB: res.team_b,
      passes: hydratePasses(res.passes, res.team_a),
      note: res.message,
    };
  }

  const teamA = toPlayerData(formData.teamAPlayers);
  const teamB = toPlayerData(formData.teamBPlayers);
  const passes = formData.manualPasses?.length
    ? formData.manualPasses
    : parsePassesText(formData.passesText, teamA);
  return { teamA, teamB, passes };
}

// ── Build request body from form data ───────────────────────────

function buildRequestBody(
  featureId: string,
  formData: AnalysisFormData,
  resolved: ResolvedInput
): Record<string, unknown> {
  const base: BaseAnalysisRequest = {
    input_type: "manual",
    team_a_name: formData.teamAName?.trim() || "Team A",
    team_b_name: formData.teamBName?.trim() || "Team B",
    team_a_color: formData.teamAColor || "#00d9ff",
    team_b_color: formData.teamBColor || "#ff5a6e",
    team_a: resolved.teamA,
    team_b: resolved.teamB,
    passes: resolved.passes,
    ball_x: clamp(parseFloat(formData.ballX), 0, 120),
    ball_y: clamp(parseFloat(formData.ballY), 0, 80),
    match_info: formData.matchInfo,
  };

  const body: Record<string, unknown> = { ...base };
  switch (featureId) {
    case "space-control":
      return { ...body, mode: formData.vizMode ?? "both", sigma: 15.0 };
    case "formation":
      return { ...body, method: "auto" };
    case "press-resistance":
      return { ...body, pressure_radius: formData.pressureRadius ?? 10, pressure_threshold: 2 };
    case "patterns":
      return { ...body, analyze_team: formData.analyzeTeam ?? "both" };
    case "pass-network":
      return { ...body, min_passes: formData.minPasses ?? 2 };
    case "strategy":
      return { ...body, situation: formData.situation || undefined };
    case "explanation":
      return {
        ...body,
        mode: formData.explanationMode ?? "template",
        report_match_info: formData.matchInfo,
      };
    default:
      return body;
  }
}

// ── Public API functions ────────────────────────────────────────

export interface AnalyzeResult {
  results: FeatureApiResponse;
  resolved: ResolvedInput;
}

/** Run analysis for any position-based feature. */
export async function analyzeFeature(
  featureId: string,
  formData: AnalysisFormData
): Promise<AnalyzeResult> {
  const endpoint = FEATURE_ENDPOINTS[featureId];
  if (!endpoint) throw new ApiError(`Unknown feature: ${featureId}`, 400);

  const resolved = await resolveFormInput(formData);
  if (resolved.teamA.length === 0) {
    throw new ApiError("Add at least one player for Team A before analysing.", 400);
  }
  if (FEATURES_NEEDING_TEAM_B.has(featureId) && resolved.teamB.length === 0) {
    throw new ApiError("This analysis needs both teams. Add Team B players (or use Try Demo).", 400);
  }

  const body = buildRequestBody(featureId, formData, resolved);
  const results = await post<FeatureApiResponse>(endpoint, body);
  return { results, resolved };
}

/** Ask SpaceAI via the backend /api/ask endpoint */
export async function askBackend(
  question: string,
  matchContext?: Record<string, unknown>
): Promise<AskResponse> {
  return post<AskResponse>("/ask", { question, match_context: matchContext });
}

/** Upload a video file for analysis */
export async function uploadVideo(file: File): Promise<VideoResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return request<VideoResponse>("/video/upload", { method: "POST", body: formData });
}

/** Process a YouTube URL for analysis */
export async function processYouTube(url: string): Promise<VideoResponse> {
  return post<VideoResponse>("/video/youtube", { url, demo_mode: false });
}

/** Upload a CSV / JSON dataset and get normalised players back */
export async function uploadDataset(file: File): Promise<DatasetResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return request<DatasetResponse>("/dataset/upload", { method: "POST", body: formData });
}

/** URL of a downloadable dataset template */
export function datasetTemplateUrl(fmt: "csv" | "json"): string {
  return `${API_BASE}/dataset/template/${fmt}`;
}

/** Run a tactical simulation */
export async function runSimulation(data: SimulationRequest): Promise<SimulationResponse> {
  return post<SimulationResponse>("/simulation/run", data);
}

/** Compare two tactical matchups */
export async function compareSimulations(
  data: SimulationCompareRequest
): Promise<SimulationCompareResponse> {
  return post<SimulationCompareResponse>("/simulation/compare", data);
}

/** Assess a player (video / data / manual) */
export async function assessPlayer(data: Record<string, unknown>): Promise<PlayerAssessmentResponse> {
  return post<PlayerAssessmentResponse>("/player-assessment", data);
}

/** Export analysis as DOCX or PDF — returns a Blob */
export async function exportReport(data: ExportRequest, format: "docx" | "pdf" = "docx"): Promise<Blob> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/export/${format}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  } catch (err) {
    throw friendlyNetworkError(err);
  }
  if (!res.ok) await parseError(res);
  return res.blob();
}

/** Trigger a browser download for a blob */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Bundled demo fixtures (real matches) */
let demoListCache: DemoMatchSummary[] | null = null;
export async function listDemoMatches(): Promise<DemoMatchSummary[]> {
  if (demoListCache) return demoListCache;
  const res = await get<{ total: number; matches: DemoMatchSummary[] }>("/demo/matches");
  demoListCache = res.matches;
  return demoListCache;
}

const demoMatchCache = new Map<string, DemoMatch>();
export async function getDemoMatch(id: string): Promise<DemoMatch> {
  const cached = demoMatchCache.get(id);
  if (cached) return cached;
  const match = await get<DemoMatch>(`/demo/matches/${encodeURIComponent(id)}`);
  demoMatchCache.set(id, match);
  return match;
}

let demoPlayersCache: DemoPlayer[] | null = null;
export async function listDemoPlayers(): Promise<DemoPlayer[]> {
  if (demoPlayersCache) return demoPlayersCache;
  const res = await get<{ total: number; players: DemoPlayer[] }>("/demo/players");
  demoPlayersCache = res.players;
  return demoPlayersCache;
}

export interface DemoVideoInfo {
  available: boolean; title: string; subtitle: string; author: string;
  license: string; source_url: string; duration_s: number; resolution: string; note: string;
}

/** Metadata for the bundled sample clip */
export async function getDemoVideoInfo(): Promise<DemoVideoInfo> {
  return get<DemoVideoInfo>("/demo/video");
}

/** Run the bundled sample clip through the CV pipeline */
export async function analyzeDemoVideo(): Promise<VideoResponse> {
  return post<VideoResponse>("/demo/video/analyze", {});
}

/** Health check */
export async function healthCheck(): Promise<HealthResponse> {
  return get<HealthResponse>("/health");
}
