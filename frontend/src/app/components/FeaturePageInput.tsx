import { motion, AnimatePresence } from "motion/react";
import {
  Upload, FileUp, Play, Plus, Trash2, Youtube, FileJson, FileSpreadsheet,
  CheckCircle2, AlertTriangle, Keyboard, Film, ScanLine, type LucideIcon,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState, type DragEvent } from "react";
import { toast } from "sonner";
import type { AnalysisFormData, FormPlayer, InputType, PlayerData, PassEvent, MatchInfo, DemoMatch, DemoMatchSummary } from "../../lib/types";
import {
  DEMO_TEAM_A, DEMO_TEAM_B, DEMO_TEAM_A_NAME, DEMO_TEAM_B_NAME, DEMO_TEAM_A_COLOR, DEMO_TEAM_B_COLOR,
  DEMO_PASSES_TEXT, DEMO_MATCH_INFO, POSITIONS, SITUATIONS, emptyPlayers,
} from "../../lib/demo";
import {
  FEATURES_NEEDING_TEAM_B, FEATURES_WITH_PASSES, toPlayerData, parsePassesText,
  uploadVideo, processYouTube, uploadDataset, datasetTemplateUrl, getDemoMatch,
  getDemoVideoInfo, analyzeDemoVideo, type DemoVideoInfo,
} from "../../lib/api";
import { Page, PageHeader, Panel, Button, SectionTitle } from "./common/Primitives";
import { DemoPicker } from "./common/DemoPicker";
import { FEATURE_BY_ID, SECTION_LABEL } from "../../lib/features";
import { PitchPreview } from "./common/PitchPreview";
import { cn } from "./ui/utils";
import { springSoft, crossfade } from "../../lib/motion";

// ── Props ───────────────────────────────────────────────────────

interface FeaturePageInputProps {
  featureId: string;
  featureName: string;
  featureDescription: string;
  icon: LucideIcon;
  onAnalyze: (data: AnalysisFormData) => void;
  isLoading?: boolean;
  initial?: AnalysisFormData | null;
  /** Bundled fixture to load and run immediately (picked on Home). */
  autoDemoId?: string | null;
  onAutoDemoUsed?: () => void;
}

type Tab = { id: InputType; label: string; icon: LucideIcon };
const TABS: Tab[] = [
  { id: "manual", label: "Manual entry", icon: Keyboard },
  { id: "video", label: "Video or YouTube", icon: Youtube },
  { id: "dataset", label: "Dataset", icon: FileUp },
];

const VIDEO_TYPES = [".mp4", ".avi", ".mov", ".mkv"];
const DATASET_TYPES = [".csv", ".json"];
const MAX_VIDEO_MB = 500;
const MAX_DATASET_MB = 50;

// ── Validation ──────────────────────────────────────────────────

type PlayerErrors = Partial<Record<keyof FormPlayer, string>>;

function validatePlayer(p: FormPlayer): PlayerErrors {
  const errs: PlayerErrors = {};
  const touched = p.name.trim() || p.number.trim() || p.x.trim() || p.y.trim();
  if (!touched) return errs;
  if (!p.name.trim()) errs.name = "Name required";
  const num = Number(p.number);
  if (p.number.trim() === "" || !Number.isInteger(num) || num < 0 || num > 99) errs.number = "0–99";
  const x = Number(p.x);
  if (p.x.trim() === "" || Number.isNaN(x) || x < 0 || x > 120) errs.x = "0–120";
  const y = Number(p.y);
  if (p.y.trim() === "" || Number.isNaN(y) || y < 0 || y > 80) errs.y = "0–80";
  return errs;
}

function isBlank(p: FormPlayer): boolean {
  return !(p.name.trim() || p.number.trim() || p.x.trim() || p.y.trim());
}

function isYouTube(url: string): boolean {
  return /^https?:\/\/(www\.|m\.)?(youtube\.com|youtu\.be)\//i.test(url.trim());
}

function extOf(name: string): string {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i).toLowerCase() : "";
}

// ── Component ───────────────────────────────────────────────────

export function FeaturePageInput({
  featureId,
  featureName,
  featureDescription,
  icon,
  onAnalyze,
  isLoading = false,
  initial,
  autoDemoId,
  onAutoDemoUsed,
}: FeaturePageInputProps) {
  const needsTeamB = FEATURES_NEEDING_TEAM_B.has(featureId);
  const usesPasses = FEATURES_WITH_PASSES.has(featureId);
  const usesBall = ["full-match", "space-control", "strategy", "explanation"].includes(featureId);
  const usesMatchInfo = ["full-match", "explanation"].includes(featureId);

  const [activeTab, setActiveTab] = useState<InputType>(initial?.inputType ?? "manual");
  const [teamAPlayers, setTeamAPlayers] = useState<FormPlayer[]>(initial?.teamAPlayers ?? emptyPlayers());
  const [teamBPlayers, setTeamBPlayers] = useState<FormPlayer[]>(initial?.teamBPlayers ?? emptyPlayers());
  const [teamAName, setTeamAName] = useState(initial?.teamAName ?? "");
  const [teamBName, setTeamBName] = useState(initial?.teamBName ?? "");
  const [teamAColor, setTeamAColor] = useState(initial?.teamAColor ?? DEMO_TEAM_A_COLOR);
  const [teamBColor, setTeamBColor] = useState(initial?.teamBColor ?? DEMO_TEAM_B_COLOR);
  const [ballX, setBallX] = useState(initial?.ballX ?? "60");
  const [ballY, setBallY] = useState(initial?.ballY ?? "40");
  const [passesText, setPassesText] = useState(initial?.passesText ?? "");
  const [youtubeUrl, setYoutubeUrl] = useState(initial?.youtubeUrl ?? "");
  const [videoFile, setVideoFile] = useState<File | undefined>(initial?.videoFile);
  const [datasetFile, setDatasetFile] = useState<File | undefined>(initial?.datasetFile);
  const [matchInfo, setMatchInfo] = useState<MatchInfo>(initial?.matchInfo ?? { score_home: 0, score_away: 0, minute: 0, competition: "" });

  // Feature settings
  const [minPasses, setMinPasses] = useState(initial?.minPasses ?? 2);
  const [vizMode, setVizMode] = useState<"both" | "influence" | "voronoi">(initial?.vizMode ?? "both");
  const [pressureRadius, setPressureRadius] = useState(initial?.pressureRadius ?? 10);
  const [analyzeTeam, setAnalyzeTeam] = useState<"both" | "a" | "b">(initial?.analyzeTeam ?? "both");
  const [situation, setSituation] = useState(initial?.situation ?? "");
  const [explanationMode, setExplanationMode] = useState<"template" | "llm">(initial?.explanationMode ?? "llm");

  // Resolved data from uploads
  const [resolved, setResolved] = useState<{ teamA: PlayerData[]; teamB: PlayerData[]; passes: PassEvent[]; note?: string; source: InputType } | null>(
    initial?.resolvedTeamA ? { teamA: initial.resolvedTeamA, teamB: initial.resolvedTeamB ?? [], passes: initial.resolvedPasses ?? [], note: initial.resolvedNote, source: initial.inputType } : null
  );
  const [isResolving, setIsResolving] = useState(false);
  const [showErrors, setShowErrors] = useState(false);
  const [manualPasses, setManualPasses] = useState<PassEvent[] | undefined>(initial?.manualPasses);
  const [demoMatch, setDemoMatch] = useState<AnalysisFormData["demoMatch"]>(initial?.demoMatch);
  const [demoBusy, setDemoBusy] = useState<string | null>(null);
  const [sampleClip, setSampleClip] = useState<DemoVideoInfo | null>(null);
  const [sampleBusy, setSampleBusy] = useState(false);

  useEffect(() => {
    let off = false;
    getDemoVideoInfo().then((v) => { if (!off && v.available) setSampleClip(v); }).catch(() => {});
    return () => { off = true; };
  }, []);

  const useSampleClip = async () => {
    setSampleBusy(true);
    try {
      const res = await analyzeDemoVideo();
      if (!res.success || !res.tracking_data) throw new Error(res.message || "Sample clip could not be analysed.");
      setVideoFile(undefined); setYoutubeUrl("");
      // Teams in the clip are colour clusters, not identified clubs: label them neutrally
      // rather than inheriting names from whatever demo fixture was loaded before.
      setTeamAName("Kit A"); setTeamBName("Kit B");
      setTeamAColor(DEMO_TEAM_A_COLOR); setTeamBColor(DEMO_TEAM_B_COLOR);
      setDemoMatch(undefined); setManualPasses(undefined);
      setResolved({ teamA: res.tracking_data.team_a, teamB: res.tracking_data.team_b, passes: [], note: res.message, source: "video" });
      toast.success("Sample clip tracked", { id: "sample-clip", description: (res.message || "").slice(0, 120) });
    } catch (err) {
      toast.error("Could not analyse the sample clip", { id: "sample-clip", description: err instanceof Error ? err.message : undefined });
    } finally {
      setSampleBusy(false);
    }
  };

  const videoInputRef = useRef<HTMLInputElement>(null);
  const datasetInputRef = useRef<HTMLInputElement>(null);

  // Reset resolved data when the source file changes
  useEffect(() => { setResolved((r) => (r?.source === "video" ? null : r)); }, [videoFile, youtubeUrl]);
  useEffect(() => { setResolved((r) => (r?.source === "dataset" ? null : r)); }, [datasetFile]);

  // ── Derived ─────────────────────────────────────────────────
  const errorsA = useMemo(() => teamAPlayers.map(validatePlayer), [teamAPlayers]);
  const errorsB = useMemo(() => teamBPlayers.map(validatePlayer), [teamBPlayers]);
  const errorCount = errorsA.reduce((n, e) => n + Object.keys(e).length, 0) + (needsTeamB ? errorsB.reduce((n, e) => n + Object.keys(e).length, 0) : 0);
  const filledA = teamAPlayers.filter((p) => !isBlank(p)).length;
  const filledB = teamBPlayers.filter((p) => !isBlank(p)).length;

  const previewA = useMemo(() => (activeTab === "manual" ? toPlayerData(teamAPlayers) : resolved?.teamA ?? []), [activeTab, teamAPlayers, resolved]);
  const previewB = useMemo(() => (activeTab === "manual" ? toPlayerData(teamBPlayers) : resolved?.teamB ?? []), [activeTab, teamBPlayers, resolved]);
  const parsedPasses = useMemo(
    () => (activeTab === "manual" ? (manualPasses?.length ? manualPasses : parsePassesText(passesText, previewA)) : resolved?.passes ?? []),
    [activeTab, passesText, previewA, resolved, manualPasses]
  );

  const ballErr = usesBall && (Number.isNaN(Number(ballX)) || Number(ballX) < 0 || Number(ballX) > 120 || Number.isNaN(Number(ballY)) || Number(ballY) < 0 || Number(ballY) > 80);

  const manualProblems: string[] = [];
  if (activeTab === "manual") {
    if (filledA === 0) manualProblems.push("Add at least one Team A player.");
    if (needsTeamB && filledB === 0) manualProblems.push("Add at least one Team B player.");
    if (errorCount > 0) manualProblems.push(`${errorCount} field${errorCount === 1 ? "" : "s"} need attention.`);
    if (ballErr) manualProblems.push("Ball position must be within x 0–120, y 0–80.");
  } else if (activeTab === "video") {
    const alreadyResolved = resolved?.source === "video" && resolved.teamA.length > 0;
    if (!alreadyResolved) {
      if (!videoFile && !youtubeUrl.trim()) manualProblems.push("Choose a video file, paste a YouTube link, or track the sample clip.");
      else if (!videoFile && youtubeUrl.trim() && !isYouTube(youtubeUrl)) manualProblems.push("Only youtube.com / youtu.be links are supported.");
    }
  } else if (activeTab === "dataset") {
    const alreadyResolved = resolved?.source === "dataset" && resolved.teamA.length > 0;
    if (!datasetFile && !alreadyResolved) manualProblems.push("Choose a CSV or JSON dataset.");
  }
  const canAnalyze = manualProblems.length === 0 && !isLoading && !isResolving;

  // ── Handlers ────────────────────────────────────────────────
  const buildFormData = (): AnalysisFormData => ({
    inputType: activeTab,
    teamAPlayers, teamBPlayers, teamAName, teamBName, teamAColor, teamBColor,
    ballX, ballY, passesText, videoFile, youtubeUrl, datasetFile,
    resolvedTeamA: resolved?.source === activeTab ? resolved.teamA : undefined,
    resolvedTeamB: resolved?.source === activeTab ? resolved.teamB : undefined,
    resolvedPasses: resolved?.source === activeTab ? resolved.passes : undefined,
    resolvedNote: resolved?.source === activeTab ? resolved.note : undefined,
    manualPasses: activeTab === "manual" ? manualPasses : undefined,
    demoMatch: activeTab === "manual" ? demoMatch : undefined,
    minPasses, vizMode, pressureRadius, analyzeTeam, situation, explanationMode,
    matchInfo: usesMatchInfo ? { ...matchInfo, home_team: teamAName || "Team A", away_team: teamBName || "Team B" } : undefined,
  });

  const handleAnalyze = () => {
    if (!canAnalyze) {
      setShowErrors(true);
      toast.error(manualProblems[0] ?? "Please complete the form.");
      return;
    }
    onAnalyze(buildFormData());
  };

  const toForm = (players: PlayerData[]): FormPlayer[] =>
    players.map((p) => ({ name: p.name, number: String(p.number), x: String(p.x), y: String(p.y), position: p.position }));
  const toText = (passes: PassEvent[]) => passes.map((p) => `${p.passer}->${p.receiver}->${p.success === false ? 0 : 1}`).join(", ");

  /** Snapshot of a fixture in the shape the form (and onAnalyze) expects. */
  const formFromMatch = (m: DemoMatch): AnalysisFormData => ({
    inputType: "manual",
    teamAPlayers: toForm(m.players_a), teamBPlayers: toForm(m.players_b),
    teamAName: m.team_a.name, teamBName: m.team_b.name,
    teamAColor: DEMO_TEAM_A_COLOR, teamBColor: DEMO_TEAM_B_COLOR,
    ballX: String(m.ball?.x ?? 60), ballY: String(m.ball?.y ?? 40),
    passesText: usesPasses ? toText(m.passes) : "",
    manualPasses: usesPasses ? m.passes : undefined,
    demoMatch: { id: m.id, title: m.title, subtitle: m.subtitle, sourceKind: m.source?.kind ?? "statsbomb", note: m.source?.note, formationA: m.team_a.formation, formationB: m.team_b.formation },
    minPasses, vizMode, pressureRadius, analyzeTeam, situation, explanationMode,
    matchInfo: usesMatchInfo ? { ...m.match_info } : undefined,
  });

  const builtinMatch = (): DemoMatch => ({
    id: "builtin", title: "FC Barcelona 2-1 Real Madrid", subtitle: "Built-in sample line-ups",
    competition: DEMO_MATCH_INFO.competition ?? "", date: DEMO_MATCH_INFO.date ?? "",
    team_a: { name: DEMO_TEAM_A_NAME, color: DEMO_TEAM_A_COLOR }, team_b: { name: DEMO_TEAM_B_NAME, color: DEMO_TEAM_B_COLOR },
    score: { a: 2, b: 1 },
    players_a: toPlayerData(DEMO_TEAM_A), players_b: toPlayerData(DEMO_TEAM_B),
    passes: parsePassesText(DEMO_PASSES_TEXT, toPlayerData(DEMO_TEAM_A)),
    ball: { x: 60, y: 40 }, match_info: { ...DEMO_MATCH_INFO },
    source: { kind: "sample", match_id: null, note: "Built-in sample line-ups." },
  });

  const applyForm = (data: AnalysisFormData) => {
    setActiveTab("manual");
    setTeamAName(data.teamAName); setTeamBName(data.teamBName);
    setTeamAColor(data.teamAColor); setTeamBColor(data.teamBColor);
    setTeamAPlayers(data.teamAPlayers); setTeamBPlayers(data.teamBPlayers);
    setBallX(data.ballX); setBallY(data.ballY);
    setPassesText(data.passesText ?? ""); setManualPasses(data.manualPasses);
    setDemoMatch(data.demoMatch);
    if (data.matchInfo) setMatchInfo({ ...data.matchInfo });
    setShowErrors(false);
  };

  const loadDemo = async (run: boolean, summary?: DemoMatchSummary) => {
    const id = summary?.id ?? "builtin";
    setDemoBusy(id);
    try {
      const match = id === "builtin" ? builtinMatch() : await getDemoMatch(id);
      const data = formFromMatch(match);
      applyForm(data);
      if (run) {
        onAnalyze(data);
      } else {
        toast.success(`${match.title} loaded`, { description: "Review the line-ups, then hit Analyse." });
      }
    } catch (err) {
      toast.error("Could not load the demo fixture", { description: err instanceof Error ? err.message : undefined });
    } finally {
      setDemoBusy(null);
    }
  };

  useEffect(() => {
    if (!autoDemoId) return;
    onAutoDemoUsed?.();
    void loadDemo(true, { id: autoDemoId } as DemoMatchSummary);
    // Run once, on arrival from Home
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const clearManual = () => {
    setTeamAPlayers(emptyPlayers());
    setTeamBPlayers(emptyPlayers());
    setTeamAName(""); setTeamBName(""); setPassesText("");
    setManualPasses(undefined); setDemoMatch(undefined);
    setShowErrors(false);
  };

  const pickFile = (file: File | undefined, kind: "video" | "dataset") => {
    if (!file) return;
    const ext = extOf(file.name);
    const allowed = kind === "video" ? VIDEO_TYPES : DATASET_TYPES;
    const maxMb = kind === "video" ? MAX_VIDEO_MB : MAX_DATASET_MB;
    if (!allowed.includes(ext)) {
      toast.error(`Unsupported file type "${ext || "none"}"`, { description: `Allowed: ${allowed.join(", ")}` });
      return;
    }
    if (file.size > maxMb * 1024 * 1024) {
      toast.error(`File is too large`, { description: `Maximum ${maxMb} MB.` });
      return;
    }
    if (kind === "video") { setVideoFile(file); setYoutubeUrl(""); }
    else setDatasetFile(file);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>, kind: "video" | "dataset") => {
    e.preventDefault();
    pickFile(e.dataTransfer.files?.[0], kind);
  };

  const extractFromSource = async () => {
    setIsResolving(true);
    try {
      if (activeTab === "video") {
        const res = videoFile ? await uploadVideo(videoFile) : await processYouTube(youtubeUrl.trim());
        if (!res.success || !res.tracking_data) throw new Error(res.message || "No tracking data returned.");
        setResolved({ teamA: res.tracking_data.team_a, teamB: res.tracking_data.team_b, passes: [], note: res.message, source: "video" });
        toast.success(`Extracted ${res.tracking_data.team_a.length + res.tracking_data.team_b.length} players`, { description: res.message });
      } else {
        if (!datasetFile) return;
        const res = await uploadDataset(datasetFile);
        setResolved({ teamA: res.team_a, teamB: res.team_b, passes: res.passes, note: res.message, source: "dataset" });
        if (!teamAName && res.match_info?.home_team) setTeamAName(String(res.match_info.home_team));
        if (!teamBName && res.match_info?.away_team) setTeamBName(String(res.match_info.away_team));
        toast.success("Dataset parsed", { description: res.message });
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not process the file.");
    } finally {
      setIsResolving(false);
    }
  };

  // ── Player editors ───────────────────────────────────────────
  const updatePlayer = (team: "a" | "b", i: number, field: keyof FormPlayer, value: string) => {
    const setter = team === "a" ? setTeamAPlayers : setTeamBPlayers;
    setter((prev) => prev.map((p, idx) => (idx === i ? { ...p, [field]: value } : p)));
  };
  const addPlayer = (team: "a" | "b") => {
    const setter = team === "a" ? setTeamAPlayers : setTeamBPlayers;
    setter((prev) => (prev.length >= 16 ? prev : [...prev, { name: "", number: "", x: "", y: "", position: "CM" }]));
  };
  const removePlayer = (team: "a" | "b", i: number) => {
    const setter = team === "a" ? setTeamAPlayers : setTeamBPlayers;
    setter((prev) => (prev.length <= 1 ? prev : prev.filter((_, idx) => idx !== i)));
  };

  // ── Render ──────────────────────────────────────────────────
  return (
    <Page>
      <PageHeader
        area={SECTION_LABEL[FEATURE_BY_ID[featureId]?.section ?? "analysis"]}
        title={featureName}
        description={featureDescription}
        actions={<DemoPicker onRun={(m) => loadDemo(true, m)} onLoad={(m) => loadDemo(false, m)} disabled={isLoading || demoBusy !== null} busyId={demoBusy} />}
      />

      {/* Input method tabs */}
      <div role="tablist" aria-label="Input method" className="mt-6 flex overflow-x-auto border-b border-line">
        {TABS.map((tab) => {
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "relative flex shrink-0 items-center gap-2 px-4 py-3 text-sm font-medium transition-colors duration-150",
                active ? "text-text-primary" : "text-text-muted hover:text-text-primary"
              )}
            >
              <tab.icon className={cn("h-4 w-4", active && "text-section")} strokeWidth={1.75} />
              {tab.label}
              {active && <motion.span layoutId="input-tab" transition={springSoft} className="absolute inset-x-0 -bottom-px h-0.5 bg-section-fill" />}
            </button>
          );
        })}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        {/* ── Left: inputs ── */}
        <div className="min-w-0 space-y-5">
          <AnimatePresence mode="wait" initial={false}>
            {activeTab === "manual" && (
              <motion.div key="manual" variants={crossfade} initial="hidden" animate="show" exit="exit" className="space-y-5">
                <div className={cn("grid gap-5", needsTeamB && "2xl:grid-cols-2")}>
                  <TeamEditor
                    label="Team A"
                    name={teamAName} onName={setTeamAName}
                    color={teamAColor} onColor={setTeamAColor}
                    players={teamAPlayers} errors={errorsA} showErrors={showErrors}
                    onChange={(i, f, v) => updatePlayer("a", i, f, v)}
                    onAdd={() => addPlayer("a")} onRemove={(i) => removePlayer("a", i)}
                  />
                  {needsTeamB && (
                    <TeamEditor
                      label="Team B"
                      name={teamBName} onName={setTeamBName}
                      color={teamBColor} onColor={setTeamBColor}
                      players={teamBPlayers} errors={errorsB} showErrors={showErrors}
                      onChange={(i, f, v) => updatePlayer("b", i, f, v)}
                      onAdd={() => addPlayer("b")} onRemove={(i) => removePlayer("b", i)}
                    />
                  )}
                </div>
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm text-text-muted">{needsTeamB ? "Empty rows are ignored." : "This analysis only needs one team. Empty rows are ignored."}</p>
                  <Button variant="ghost" size="sm" icon={Trash2} onClick={clearManual}>Clear all</Button>
                </div>
              </motion.div>
            )}

            {activeTab === "video" && (
              <motion.div key="video" variants={crossfade} initial="hidden" animate="show" exit="exit" className="space-y-5">
                <input ref={videoInputRef} type="file" accept={VIDEO_TYPES.join(",")} className="hidden" onChange={(e) => pickFile(e.target.files?.[0], "video")} />
                {sampleClip && (
                  <Panel className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium text-text-primary">Sample clip: {sampleClip.title}</span>
                        <span className="chip border-line-strong text-text-secondary">{sampleClip.license}</span>
                      </div>
                      <p className="mt-0.5 text-sm text-text-secondary">{sampleClip.subtitle}, {sampleClip.duration_s}s. {sampleClip.note}</p>
                      <a href={sampleClip.source_url} target="_blank" rel="noreferrer" className="text-xs text-section underline-offset-4 hover:underline">
                        {sampleClip.author}, Wikimedia Commons
                      </a>
                    </div>
                    <Button variant="accent" icon={Film} loading={sampleBusy} onClick={useSampleClip} className="shrink-0">
                      {sampleBusy ? "Tracking…" : "Track sample clip"}
                    </Button>
                  </Panel>
                )}

                <Dropzone
                  icon={Upload}
                  onClick={() => videoInputRef.current?.click()}
                  onDrop={(e) => onDrop(e, "video")}
                  file={videoFile}
                  onClear={() => setVideoFile(undefined)}
                  title="Drop a match clip here, or click to browse"
                  hint={`MP4, AVI, MOV or MKV, up to ${MAX_VIDEO_MB} MB`}
                />
                <div className="flex items-center gap-3 text-sm text-text-muted">
                  <span className="h-px flex-1 bg-line" /> or paste a link <span className="h-px flex-1 bg-line" />
                </div>
                <Panel>
                  <label className="label" htmlFor="yt-url">YouTube link</label>
                  <div className="relative">
                    <Youtube className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                    <input
                      id="yt-url"
                      type="url"
                      value={youtubeUrl}
                      onChange={(e) => { setYoutubeUrl(e.target.value); if (e.target.value) setVideoFile(undefined); }}
                      placeholder="https://www.youtube.com/watch?v=…"
                      aria-invalid={Boolean(youtubeUrl) && !isYouTube(youtubeUrl)}
                      className="field pl-9"
                    />
                  </div>
                  {youtubeUrl && !isYouTube(youtubeUrl) && <p className="mt-1.5 text-sm text-danger">Only youtube.com and youtu.be links are supported.</p>}
                </Panel>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-text-secondary">
                    YOLOv8 detection, tracking and a homography turn footage into pitch coordinates. Without the optional
                    vision packages the backend returns a synthetic snapshot and says so.
                  </p>
                  <Button variant="secondary" icon={ScanLine} loading={isResolving} onClick={extractFromSource} disabled={!videoFile && !isYouTube(youtubeUrl)} className="shrink-0">
                    {isResolving ? "Extracting…" : "Extract positions"}
                  </Button>
                </div>
                <ResolvedNote resolved={resolved} source="video" />
              </motion.div>
            )}

            {activeTab === "dataset" && (
              <motion.div key="dataset" variants={crossfade} initial="hidden" animate="show" exit="exit" className="space-y-5">
                <input ref={datasetInputRef} type="file" accept={DATASET_TYPES.join(",")} className="hidden" onChange={(e) => pickFile(e.target.files?.[0], "dataset")} />
                <Dropzone
                  icon={FileUp}
                  onClick={() => datasetInputRef.current?.click()}
                  onDrop={(e) => onDrop(e, "dataset")}
                  file={datasetFile}
                  onClear={() => setDatasetFile(undefined)}
                  title="Drop a CSV or JSON dataset here, or click to browse"
                  hint={`Columns: team, name, number, x, y, position. Up to ${MAX_DATASET_MB} MB.`}
                />
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-text-secondary">Not sure of the format? Start from a template.</p>
                  <div className="flex flex-wrap gap-2">
                    <a href={datasetTemplateUrl("csv")} download className="press inline-flex h-8 items-center gap-1.5 rounded-md border border-line-strong bg-surface-2 px-3 text-sm font-medium text-text-primary hover:bg-surface-3">
                      <FileSpreadsheet className="h-3.5 w-3.5" /> CSV template
                    </a>
                    <a href={datasetTemplateUrl("json")} download className="press inline-flex h-8 items-center gap-1.5 rounded-md border border-line-strong bg-surface-2 px-3 text-sm font-medium text-text-primary hover:bg-surface-3">
                      <FileJson className="h-3.5 w-3.5" /> JSON template
                    </a>
                    <Button variant="secondary" size="sm" icon={ScanLine} loading={isResolving} onClick={extractFromSource} disabled={!datasetFile}>
                      {isResolving ? "Parsing…" : "Parse dataset"}
                    </Button>
                  </div>
                </div>
                <ResolvedNote resolved={resolved} source="dataset" />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Feature settings */}
          <Panel>
            <SectionTitle hint="How the engine should read this fixture">Settings</SectionTitle>
            <div className="grid gap-4 sm:grid-cols-2">
              {activeTab !== "manual" && (
                <>
                  <Field label="Team A name"><input className="field" value={teamAName} onChange={(e) => setTeamAName(e.target.value)} placeholder="Team A" /></Field>
                  {needsTeamB && <Field label="Team B name"><input className="field" value={teamBName} onChange={(e) => setTeamBName(e.target.value)} placeholder="Team B" /></Field>}
                </>
              )}
              {usesBall && (
                <Field label="Ball position (x, y)" error={showErrors && ballErr ? "x must be 0–120 and y 0–80" : undefined}>
                  <div className="flex gap-2">
                    <input className="field" inputMode="decimal" value={ballX} onChange={(e) => setBallX(e.target.value)} placeholder="x" aria-label="Ball x" aria-invalid={ballErr} />
                    <input className="field" inputMode="decimal" value={ballY} onChange={(e) => setBallY(e.target.value)} placeholder="y" aria-label="Ball y" aria-invalid={ballErr} />
                  </div>
                </Field>
              )}
              {usesPasses && activeTab === "manual" && (
                <Field label="Passes" hint={`Shirt numbers, passer->receiver, optionally ->1 or ->0 for completed or not. ${parsedPasses.length} read so far.`} className="sm:col-span-2">
                  <textarea className="field min-h-[80px] font-mono text-sm" value={passesText} onChange={(e) => { setPassesText(e.target.value); setManualPasses(undefined); setDemoMatch(undefined); }} placeholder="4->8, 8->6->1, 6->9->0" />
                </Field>
              )}
              {featureId === "pass-network" && (
                <Field label={`Minimum passes per link: ${minPasses}`}>
                  <input type="range" min={1} max={5} value={minPasses} onChange={(e) => setMinPasses(Number(e.target.value))} className="w-full" />
                </Field>
              )}
              {featureId === "space-control" && (
                <Field label="Maps to draw">
                  <select className="field" value={vizMode} onChange={(e) => setVizMode(e.target.value as typeof vizMode)}>
                    <option value="both">Voronoi and influence</option>
                    <option value="voronoi">Voronoi only</option>
                    <option value="influence">Influence only</option>
                  </select>
                </Field>
              )}
              {featureId === "press-resistance" && (
                <Field label={`Pressure radius: ${pressureRadius} m`} hint="Opponents this close to the passer count as pressing">
                  <input type="range" min={5} max={20} value={pressureRadius} onChange={(e) => setPressureRadius(Number(e.target.value))} className="w-full" />
                </Field>
              )}
              {featureId === "patterns" && (
                <Field label="Analyse">
                  <select className="field" value={analyzeTeam} onChange={(e) => setAnalyzeTeam(e.target.value as typeof analyzeTeam)}>
                    <option value="both">Both teams</option>
                    <option value="a">Team A only</option>
                    <option value="b">Team B only</option>
                  </select>
                </Field>
              )}
              {featureId === "strategy" && (
                <Field label="Tactical situation" hint="Steers the knowledge graph towards matching counter-strategies">
                  <select className="field" value={situation} onChange={(e) => setSituation(e.target.value)}>
                    {SITUATIONS.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
                  </select>
                </Field>
              )}
              {featureId === "explanation" && (
                <Field label="Written by" hint="The language model needs a key on the backend; without one the template engine writes the report">
                  <select className="field" value={explanationMode} onChange={(e) => setExplanationMode(e.target.value as typeof explanationMode)}>
                    <option value="llm">Language model, if available</option>
                    <option value="template">Template engine</option>
                  </select>
                </Field>
              )}
              {usesMatchInfo && (
                <>
                  <Field label="Score (A, B)">
                    <div className="flex gap-2">
                      <input className="field" type="number" min={0} aria-label="Team A score" value={matchInfo.score_home ?? 0} onChange={(e) => setMatchInfo({ ...matchInfo, score_home: Number(e.target.value) })} />
                      <input className="field" type="number" min={0} aria-label="Team B score" value={matchInfo.score_away ?? 0} onChange={(e) => setMatchInfo({ ...matchInfo, score_away: Number(e.target.value) })} />
                    </div>
                  </Field>
                  <Field label="Minute and competition">
                    <div className="flex gap-2">
                      <input className="field w-24" type="number" min={0} max={120} aria-label="Minute" value={matchInfo.minute ?? 0} onChange={(e) => setMatchInfo({ ...matchInfo, minute: Number(e.target.value) })} />
                      <input className="field" aria-label="Competition" value={matchInfo.competition ?? ""} onChange={(e) => setMatchInfo({ ...matchInfo, competition: e.target.value })} placeholder="La Liga" />
                    </div>
                  </Field>
                </>
              )}
            </div>
          </Panel>
        </div>

        {/* ── Right: preview + run ── */}
        <div className="space-y-4 lg:sticky lg:top-0 lg:self-start">
          <figure className="tile overflow-hidden">
            <PitchPreview
              teamA={previewA}
              teamB={previewB}
              teamAColor={teamAColor}
              teamBColor={teamBColor}
              passes={usesPasses ? parsedPasses : undefined}
              passDelay={0}
              ball={usesBall ? { x: Number(ballX), y: Number(ballY) } : null}
            />
            <figcaption className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-line px-3 py-2.5 text-sm text-text-secondary">
              <span className="flex min-w-0 items-center gap-1.5"><span className="h-2 w-2 shrink-0 rounded-full" style={{ background: teamAColor }} /><span className="truncate">{teamAName || "Team A"}</span></span>
              {(needsTeamB || previewB.length > 0) && <span className="flex min-w-0 items-center gap-1.5"><span className="h-2 w-2 shrink-0 rounded-full" style={{ background: teamBColor }} /><span className="truncate">{teamBName || "Team B"}</span></span>}
              <span className="tabular ml-auto text-text-muted">{previewA.length} v {previewB.length}</span>
            </figcaption>
          </figure>

          <AnimatePresence>
            {showErrors && manualProblems.length > 0 && (
              <motion.div
                role="alert"
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, transition: { duration: 0.12 } }}
                className="rounded-md border border-danger/50 bg-danger/10 p-3 text-sm text-danger"
              >
                <div className="mb-1 flex items-center gap-2 font-medium"><AlertTriangle className="h-4 w-4" /> Fix these before analysing</div>
                <ul className="list-disc space-y-0.5 pl-5">
                  {manualProblems.map((m) => <li key={m}>{m}</li>)}
                </ul>
              </motion.div>
            )}
          </AnimatePresence>

          <Button size="lg" block icon={Play} loading={isLoading} onClick={handleAnalyze}>
            {isLoading ? "Analysing…" : `Analyse`}
          </Button>
          <p className="text-center text-sm text-text-muted">
            {activeTab === "manual"
              ? `${filledA}${needsTeamB ? ` + ${filledB}` : ""} players${usesPasses ? `, ${parsedPasses.length} passes` : ""}`
              : resolved?.source === activeTab ? "Positions ready to analyse" : "The upload is processed when you analyse"}
          </p>
        </div>
      </div>
    </Page>
  );
}

// ── Sub-components ──────────────────────────────────────────────

function Field({ label, hint, error, children, className }: { label: string; hint?: string; error?: string; children: React.ReactNode; className?: string }) {
  return (
    <label className={cn("block", className)}>
      <span className="label">{label}</span>
      {children}
      {error ? <span className="mt-1 block text-sm text-danger">{error}</span> : hint ? <span className="mt-1 block text-xs text-text-muted">{hint}</span> : null}
    </label>
  );
}

interface TeamEditorProps {
  label: string;
  name: string; onName: (v: string) => void;
  color: string; onColor: (v: string) => void;
  players: FormPlayer[];
  errors: PlayerErrors[];
  showErrors: boolean;
  onChange: (i: number, field: keyof FormPlayer, value: string) => void;
  onAdd: () => void;
  onRemove: (i: number) => void;
}

// Desktop: one row per player. Phone: name / number / remove on top, x / y / position below.
const ROW = "grid grid-cols-6 gap-1.5 sm:grid-cols-[minmax(0,1fr)_3rem_3.75rem_3.75rem_4.75rem_2rem]";

function TeamEditor({ label, name, onName, color, onColor, players, errors, showErrors, onChange, onAdd, onRemove }: TeamEditorProps) {
  const filled = players.filter((p) => !isBlank(p)).length;
  return (
    <Panel className="min-w-0">
      <div className="mb-4 flex items-center gap-3">
        <span className="h-8 w-1 shrink-0 rounded-[1px]" style={{ background: color }} />
        <input type="text" value={name} onChange={(e) => onName(e.target.value)} placeholder={`${label} name`} aria-label={`${label} name`} className="field min-w-0 flex-1 font-medium" />
        <input type="color" value={color} onChange={(e) => onColor(e.target.value)} aria-label={`${label} colour`} className="h-9 w-10 shrink-0 cursor-pointer" />
      </div>
      <div className={cn(ROW, "mb-1.5 hidden px-0.5 text-xs text-text-muted sm:grid")}>
        <span>Name</span><span>No.</span><span>x</span><span>y</span><span>Pos.</span><span />
      </div>
      <div className="max-h-[440px] space-y-2 overflow-y-auto overflow-x-hidden pr-0.5 sm:space-y-1.5">
        {players.map((p, i) => {
          const e = showErrors ? errors[i] : {};
          return (
            <div key={i} className={cn(ROW, "border-b border-line pb-2 last:border-b-0 sm:border-0 sm:pb-0")}>
              <input value={p.name} onChange={(ev) => onChange(i, "name", ev.target.value)} placeholder={`Player ${i + 1}`} aria-label={`${label} player ${i + 1} name`} aria-invalid={Boolean(e.name)} title={e.name} className="field order-1 col-span-4 px-2 py-1.5 sm:order-none sm:col-span-1" />
              <input value={p.number} onChange={(ev) => onChange(i, "number", ev.target.value)} placeholder="No." inputMode="numeric" aria-label={`${label} player ${i + 1} number`} aria-invalid={Boolean(e.number)} title={e.number} className="field order-2 col-span-1 px-2 py-1.5 sm:order-none" />
              <input value={p.x} onChange={(ev) => onChange(i, "x", ev.target.value)} placeholder="x 0–120" inputMode="decimal" aria-label={`${label} player ${i + 1} x`} aria-invalid={Boolean(e.x)} title={e.x} className="field order-4 col-span-2 px-2 py-1.5 sm:order-none sm:col-span-1" />
              <input value={p.y} onChange={(ev) => onChange(i, "y", ev.target.value)} placeholder="y 0–80" inputMode="decimal" aria-label={`${label} player ${i + 1} y`} aria-invalid={Boolean(e.y)} title={e.y} className="field order-5 col-span-2 px-2 py-1.5 sm:order-none sm:col-span-1" />
              <select value={p.position} onChange={(ev) => onChange(i, "position", ev.target.value)} aria-label={`${label} player ${i + 1} position`} className="field order-6 col-span-2 px-1.5 py-1.5 sm:order-none sm:col-span-1">
                {POSITIONS.map((pos) => <option key={pos} value={pos}>{pos}</option>)}
              </select>
              <button type="button" onClick={() => onRemove(i)} aria-label={`Remove ${label} player ${i + 1}`} className="press order-3 col-span-1 flex items-center justify-center rounded-md text-text-muted hover:bg-danger/15 hover:text-danger sm:order-none">
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          );
        })}
      </div>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-sm text-text-muted">{filled} of {players.length} rows filled</span>
        <button type="button" onClick={onAdd} className="inline-flex items-center gap-1 text-sm font-medium text-section underline-offset-4 hover:underline disabled:opacity-40" disabled={players.length >= 16}>
          <Plus className="h-3.5 w-3.5" /> Add player
        </button>
      </div>
    </Panel>
  );
}

interface DropzoneProps {
  icon: LucideIcon;
  onClick: () => void;
  onDrop: (e: DragEvent<HTMLDivElement>) => void;
  file?: File;
  onClear: () => void;
  title: string;
  hint: string;
}

function Dropzone({ icon: Icon, onClick, onDrop, file, onClear, title, hint }: DropzoneProps) {
  const [over, setOver] = useState(false);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onClick(); } }}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { setOver(false); onDrop(e); }}
      className={cn(
        "flex cursor-pointer flex-col items-start gap-3 rounded-md border border-dashed p-6 transition-colors duration-150 sm:flex-row sm:items-center sm:p-8",
        over ? "border-section bg-section-fill/5" : "border-line-strong bg-surface-1 hover:border-section/60"
      )}
    >
      <Icon className={cn("h-8 w-8 shrink-0", file ? "text-success" : "text-section")} strokeWidth={1.5} />
      {file ? (
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-medium text-text-primary">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-success" /> <span className="truncate">{file.name}</span>
          </div>
          <p className="text-sm text-text-muted">{(file.size / (1024 * 1024)).toFixed(1)} MB</p>
          <button type="button" onClick={(e) => { e.stopPropagation(); onClear(); }} className="mt-1 text-sm text-text-secondary underline underline-offset-4 hover:text-text-primary">
            Choose a different file
          </button>
        </div>
      ) : (
        <div>
          <div className="font-medium text-text-primary">{title}</div>
          <p className="mt-0.5 text-sm text-text-muted">{hint}</p>
        </div>
      )}
    </div>
  );
}

function ResolvedNote({ resolved, source }: { resolved: { teamA: PlayerData[]; teamB: PlayerData[]; passes: PassEvent[]; note?: string; source: InputType } | null; source: InputType }) {
  if (!resolved || resolved.source !== source) return null;
  const synthetic = /synthetic/i.test(resolved.note ?? "");
  return (
    <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className={cn("flex items-start gap-3 rounded-md border p-4 text-sm", synthetic ? "border-warning/50 bg-warning/5" : "border-success/50 bg-success/5")}>
      {synthetic ? <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" /> : <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />}
      <div>
        <div className={cn("font-medium", synthetic ? "text-warning" : "text-success")}>
          {resolved.teamA.length} + {resolved.teamB.length} players{resolved.passes.length ? `, ${resolved.passes.length} passes` : ""} ready
        </div>
        {resolved.note && <div className="mt-0.5 text-text-secondary">{resolved.note}</div>}
      </div>
    </motion.div>
  );
}
