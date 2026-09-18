import { motion, AnimatePresence } from "motion/react";
import {
  Upload, FileUp, Play, Sparkles, Plus, Trash2, Youtube, FileJson, FileSpreadsheet,
  CheckCircle2, AlertTriangle, Loader2, Wand2, type LucideIcon,
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
import { Page, PageHeader, GlassCard, Button, SectionTitle } from "./common/Primitives";
import { DemoPicker } from "./common/DemoPicker";
import { PitchPreview } from "./common/PitchPreview";
import { cn } from "./ui/utils";
import { springSoft } from "../../lib/motion";

// ── Props ───────────────────────────────────────────────────────

interface FeaturePageInputProps {
  featureId: string;
  featureName: string;
  featureDescription: string;
  icon: LucideIcon;
  onAnalyze: (data: AnalysisFormData) => void;
  isLoading?: boolean;
  initial?: AnalysisFormData | null;
}

type Tab = { id: InputType; label: string; icon: LucideIcon };
const TABS: Tab[] = [
  { id: "manual", label: "Manual Entry", icon: Wand2 },
  { id: "video", label: "Video / YouTube", icon: Youtube },
  { id: "dataset", label: "Dataset Upload", icon: FileUp },
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
      setResolved({ teamA: res.tracking_data.team_a, teamB: res.tracking_data.team_b, passes: [], note: res.message, source: "video" });
      toast.success("Sample clip tracked", { description: (res.message || "").slice(0, 120) });
    } catch (err) {
      toast.error("Could not analyse the sample clip", { description: err instanceof Error ? err.message : undefined });
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
    teamAColor: m.team_a.color || DEMO_TEAM_A_COLOR, teamBColor: m.team_b.color || DEMO_TEAM_B_COLOR,
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
      <div className="space-y-5">
        <PageHeader
          icon={icon}
          title={featureName}
          description={featureDescription}
          eyebrow="Analysis"
          actions={<DemoPicker onRun={(m) => loadDemo(true, m)} onLoad={(m) => loadDemo(false, m)} disabled={isLoading || demoBusy !== null} busyId={demoBusy} />}
        />

        {/* Tabs */}
        <div className="glass flex overflow-x-auto p-1">
          {TABS.map((tab) => {
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "relative flex flex-1 items-center justify-center gap-2 whitespace-nowrap rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors",
                  active ? "text-white" : "text-text-secondary hover:text-white"
                )}
              >
                {active && (
                  <motion.span layoutId="input-tab" transition={springSoft} className="absolute inset-0 rounded-lg bg-brand/15 ring-1 ring-brand/40" />
                )}
                <tab.icon className="relative h-4 w-4" />
                <span className="relative">{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
          {/* ── Left: inputs ── */}
          <div className="min-w-0 space-y-5">
            <AnimatePresence mode="wait" initial={false}>
              {activeTab === "manual" && (
                <motion.div key="manual" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }} className="space-y-5">
                  <div className={cn("grid gap-5", needsTeamB && "2xl:grid-cols-2")}>
                    <TeamEditor
                      label="Team A"
                      accent={teamAColor}
                      name={teamAName} onName={setTeamAName}
                      color={teamAColor} onColor={setTeamAColor}
                      players={teamAPlayers} errors={errorsA} showErrors={showErrors}
                      onChange={(i, f, v) => updatePlayer("a", i, f, v)}
                      onAdd={() => addPlayer("a")} onRemove={(i) => removePlayer("a", i)}
                    />
                    {needsTeamB && (
                      <TeamEditor
                        label="Team B"
                        accent={teamBColor}
                        name={teamBName} onName={setTeamBName}
                        color={teamBColor} onColor={setTeamBColor}
                        players={teamBPlayers} errors={errorsB} showErrors={showErrors}
                        onChange={(i, f, v) => updatePlayer("b", i, f, v)}
                        onAdd={() => addPlayer("b")} onRemove={(i) => removePlayer("b", i)}
                      />
                    )}
                  </div>
                  {!needsTeamB && (
                    <p className="text-xs text-text-muted">This analysis only needs one team. Opponent positions are optional.</p>
                  )}
                  <div className="flex justify-end">
                    <Button variant="ghost" size="sm" icon={Trash2} onClick={clearManual}>Clear all</Button>
                  </div>
                </motion.div>
              )}

              {activeTab === "video" && (
                <motion.div key="video" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }} className="space-y-5">
                  <input ref={videoInputRef} type="file" accept={VIDEO_TYPES.join(",")} className="hidden" onChange={(e) => pickFile(e.target.files?.[0], "video")} />
                  {sampleClip && (
                    <GlassCard className="flex flex-col gap-3 border-brand/30 sm:flex-row sm:items-center sm:justify-between">
                      <div className="min-w-0">
                        <div className="mb-0.5 flex flex-wrap items-center gap-2">
                          <span className="text-sm font-bold text-white">Sample clip · {sampleClip.title}</span>
                          <span className="chip border-success/40 bg-success/10 text-[10px] text-success">{sampleClip.license}</span>
                        </div>
                        <p className="text-xs text-text-secondary">{sampleClip.subtitle} · {sampleClip.duration_s}s</p>
                        <p className="mt-1 text-[11px] text-text-muted">{sampleClip.note}</p>
                        <a href={sampleClip.source_url} target="_blank" rel="noreferrer" className="text-[11px] text-brand hover:underline">
                          {sampleClip.author}, Wikimedia Commons
                        </a>
                      </div>
                      <Button variant="demo" icon={Sparkles} loading={sampleBusy} onClick={useSampleClip} className="shrink-0">
                        Track sample clip
                      </Button>
                    </GlassCard>
                  )}

                  <Dropzone
                    icon={Upload}
                    onClick={() => videoInputRef.current?.click()}
                    onDrop={(e) => onDrop(e, "video")}
                    file={videoFile}
                    onClear={() => setVideoFile(undefined)}
                    title="Drop a match clip here"
                    hint={`MP4, AVI, MOV or MKV · up to ${MAX_VIDEO_MB} MB`}
                  />
                  <div className="flex items-center gap-3 text-xs font-semibold uppercase tracking-widest text-text-muted">
                    <span className="h-px flex-1 bg-white/10" /> or <span className="h-px flex-1 bg-white/10" />
                  </div>
                  <GlassCard>
                    <label className="mb-2 block text-sm font-semibold text-white">YouTube URL</label>
                    <div className="relative">
                      <Youtube className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                      <input
                        type="url"
                        value={youtubeUrl}
                        onChange={(e) => { setYoutubeUrl(e.target.value); if (e.target.value) setVideoFile(undefined); }}
                        placeholder="https://www.youtube.com/watch?v=…"
                        aria-invalid={Boolean(youtubeUrl) && !isYouTube(youtubeUrl)}
                        className="field pl-9"
                      />
                    </div>
                    {youtubeUrl && !isYouTube(youtubeUrl) && <p className="mt-1.5 text-xs text-danger">Only youtube.com / youtu.be links are supported.</p>}
                  </GlassCard>
                  <GlassCard className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="text-sm text-text-secondary">
                      Phase 4 runs YOLOv8 detection, tracking and homography to turn footage into pitch coordinates.
                      Without the optional CV packages the backend returns a clearly labelled synthetic tracking snapshot.
                    </div>
                    <Button variant="secondary" icon={Sparkles} loading={isResolving} onClick={extractFromSource} disabled={!videoFile && !isYouTube(youtubeUrl)}>
                      Extract positions
                    </Button>
                  </GlassCard>
                  <ResolvedNote resolved={resolved} source="video" />
                </motion.div>
              )}

              {activeTab === "dataset" && (
                <motion.div key="dataset" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }} className="space-y-5">
                  <input ref={datasetInputRef} type="file" accept={DATASET_TYPES.join(",")} className="hidden" onChange={(e) => pickFile(e.target.files?.[0], "dataset")} />
                  <Dropzone
                    icon={FileUp}
                    onClick={() => datasetInputRef.current?.click()}
                    onDrop={(e) => onDrop(e, "dataset")}
                    file={datasetFile}
                    onClear={() => setDatasetFile(undefined)}
                    title="Drop a CSV or JSON dataset here"
                    hint={`Columns: team, name, number, x, y, position · up to ${MAX_DATASET_MB} MB`}
                  />
                  <GlassCard className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="text-sm text-text-secondary">
                      Need the format? Download a ready-made El Clásico template and edit it.
                    </div>
                    <div className="flex gap-2">
                      <a href={datasetTemplateUrl("csv")} download className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-white hover:bg-white/10">
                        <FileSpreadsheet className="h-3.5 w-3.5" /> CSV template
                      </a>
                      <a href={datasetTemplateUrl("json")} download className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-white hover:bg-white/10">
                        <FileJson className="h-3.5 w-3.5" /> JSON template
                      </a>
                    </div>
                  </GlassCard>
                  <div className="flex justify-end">
                    <Button variant="secondary" icon={Sparkles} loading={isResolving} onClick={extractFromSource} disabled={!datasetFile}>
                      Parse dataset
                    </Button>
                  </div>
                  <ResolvedNote resolved={resolved} source="dataset" />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Feature settings */}
            <GlassCard>
              <SectionTitle hint="Tune how the engine analyses this fixture">Settings</SectionTitle>
              <div className="grid gap-4 sm:grid-cols-2">
                {(activeTab !== "manual") && (
                  <>
                    <Field label="Team A name"><input className="field" value={teamAName} onChange={(e) => setTeamAName(e.target.value)} placeholder="Team A" /></Field>
                    {needsTeamB && <Field label="Team B name"><input className="field" value={teamBName} onChange={(e) => setTeamBName(e.target.value)} placeholder="Team B" /></Field>}
                  </>
                )}
                {usesBall && (
                  <Field label="Ball position (x, y)" error={showErrors && ballErr ? "x 0–120, y 0–80" : undefined}>
                    <div className="flex gap-2">
                      <input className="field" inputMode="decimal" value={ballX} onChange={(e) => setBallX(e.target.value)} placeholder="X" aria-invalid={ballErr} />
                      <input className="field" inputMode="decimal" value={ballY} onChange={(e) => setBallY(e.target.value)} placeholder="Y" aria-invalid={ballErr} />
                    </div>
                  </Field>
                )}
                {usesPasses && activeTab === "manual" && (
                  <Field label="Pass events" hint={`passer->receiver or passer->receiver->1|0 · ${parsedPasses.length} parsed`} className="sm:col-span-2">
                    <textarea className="field min-h-[72px] font-mono text-xs" value={passesText} onChange={(e) => { setPassesText(e.target.value); setManualPasses(undefined); setDemoMatch(undefined); }} placeholder="e.g. 4->8, 8->6->1, 6->9->0" />
                  </Field>
                )}
                {featureId === "pass-network" && (
                  <Field label={`Minimum passes per link: ${minPasses}`}>
                    <input type="range" min={1} max={5} value={minPasses} onChange={(e) => setMinPasses(Number(e.target.value))} className="w-full" />
                  </Field>
                )}
                {featureId === "space-control" && (
                  <Field label="Visualisation">
                    <select className="field" value={vizMode} onChange={(e) => setVizMode(e.target.value as typeof vizMode)}>
                      <option value="both">Voronoi + Influence</option>
                      <option value="voronoi">Voronoi only</option>
                      <option value="influence">Influence only</option>
                    </select>
                  </Field>
                )}
                {featureId === "press-resistance" && (
                  <Field label={`Pressure radius: ${pressureRadius} m`}>
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
                  <Field label="Tactical situation" hint="Feeds the knowledge graph for counter-strategies">
                    <select className="field" value={situation} onChange={(e) => setSituation(e.target.value)}>
                      {SITUATIONS.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
                    </select>
                  </Field>
                )}
                {featureId === "explanation" && (
                  <Field label="Report engine" hint="LLM mode falls back to templates when no API key is set on the backend">
                    <select className="field" value={explanationMode} onChange={(e) => setExplanationMode(e.target.value as typeof explanationMode)}>
                      <option value="llm">AI narrative (LLM)</option>
                      <option value="template">Deterministic template</option>
                    </select>
                  </Field>
                )}
                {usesMatchInfo && (
                  <>
                    <Field label="Score (A – B)">
                      <div className="flex gap-2">
                        <input className="field" type="number" min={0} value={matchInfo.score_home ?? 0} onChange={(e) => setMatchInfo({ ...matchInfo, score_home: Number(e.target.value) })} />
                        <input className="field" type="number" min={0} value={matchInfo.score_away ?? 0} onChange={(e) => setMatchInfo({ ...matchInfo, score_away: Number(e.target.value) })} />
                      </div>
                    </Field>
                    <Field label="Minute / competition">
                      <div className="flex gap-2">
                        <input className="field w-24" type="number" min={0} max={120} value={matchInfo.minute ?? 0} onChange={(e) => setMatchInfo({ ...matchInfo, minute: Number(e.target.value) })} />
                        <input className="field" value={matchInfo.competition ?? ""} onChange={(e) => setMatchInfo({ ...matchInfo, competition: e.target.value })} placeholder="La Liga" />
                      </div>
                    </Field>
                  </>
                )}
              </div>
            </GlassCard>
          </div>

          {/* ── Right: preview + CTA ── */}
          <div className="space-y-4 lg:sticky lg:top-0 lg:self-start">
            <GlassCard className="p-3">
              <div className="mb-2 flex items-center justify-between px-1">
                <span className="eyebrow">Live pitch preview</span>
                <span className="text-xs text-text-muted">{previewA.length} v {previewB.length}</span>
              </div>
              <div className="overflow-hidden rounded-lg">
                <PitchPreview
                  teamA={previewA}
                  teamB={previewB}
                  teamAColor={teamAColor}
                  teamBColor={teamBColor}
                  ball={usesBall ? { x: Number(ballX), y: Number(ballY) } : null}
                />
              </div>
              <div className="mt-2 flex items-center gap-4 px-1 text-xs text-text-secondary">
                <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: teamAColor }} />{teamAName || "Team A"}</span>
                {(needsTeamB || previewB.length > 0) && <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: teamBColor }} />{teamBName || "Team B"}</span>}
              </div>
            </GlassCard>

            <AnimatePresence>
              {showErrors && manualProblems.length > 0 && (
                <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="rounded-xl border border-danger/40 bg-danger/10 p-3 text-sm text-danger">
                  <div className="mb-1 flex items-center gap-2 font-semibold"><AlertTriangle className="h-4 w-4" /> Fix before analysing</div>
                  <ul className="list-disc space-y-0.5 pl-5 text-danger/90">
                    {manualProblems.map((m) => <li key={m}>{m}</li>)}
                  </ul>
                </motion.div>
              )}
            </AnimatePresence>

            <Button variant="success" size="lg" block icon={Play} loading={isLoading} onClick={handleAnalyze}>
              {isLoading ? "Analysing…" : "Analyse"}
            </Button>
            <p className="text-center text-xs text-text-muted">
              {activeTab === "manual"
                ? `${filledA}${needsTeamB ? ` + ${filledB}` : ""} players entered${usesPasses ? ` · ${parsedPasses.length} passes` : ""}`
                : resolved ? "Positions ready — hit Analyse" : "Upload will be processed when you analyse"}
            </p>
          </div>
        </div>
      </div>
    </Page>
  );
}

// ── Sub-components ──────────────────────────────────────────────

function Field({ label, hint, error, children, className }: { label: string; hint?: string; error?: string; children: React.ReactNode; className?: string }) {
  return (
    <label className={cn("block", className)}>
      <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-secondary">{label}</span>
      {children}
      {error ? <span className="mt-1 block text-xs text-danger">{error}</span> : hint ? <span className="mt-1 block text-xs text-text-muted">{hint}</span> : null}
    </label>
  );
}

interface TeamEditorProps {
  label: string;
  accent: string;
  name: string; onName: (v: string) => void;
  color: string; onColor: (v: string) => void;
  players: FormPlayer[];
  errors: PlayerErrors[];
  showErrors: boolean;
  onChange: (i: number, field: keyof FormPlayer, value: string) => void;
  onAdd: () => void;
  onRemove: (i: number) => void;
}

function TeamEditor({ label, accent, name, onName, color, onColor, players, errors, showErrors, onChange, onAdd, onRemove }: TeamEditorProps) {
  const filled = players.filter((p) => !isBlank(p)).length;
  return (
    <GlassCard className="min-w-0">
      <div className="mb-3 flex items-center gap-3">
        <span className="h-8 w-1.5 rounded-full" style={{ background: accent }} />
        <input
          type="text"
          value={name}
          onChange={(e) => onName(e.target.value)}
          placeholder={`${label} name`}
          className="field flex-1 font-semibold"
        />
        <input type="color" value={color} onChange={(e) => onColor(e.target.value)} aria-label={`${label} colour`} className="h-9 w-10 cursor-pointer rounded-lg" />
      </div>
      <div className="overflow-x-auto">
      <div className="mb-1.5 grid min-w-[420px] grid-cols-[minmax(120px,1fr)_48px_58px_58px_68px_26px] gap-1.5 px-0.5 text-[10px] font-bold uppercase tracking-wider text-text-muted">
        <span>Name</span><span>#</span><span>X</span><span>Y</span><span>Pos</span><span />
      </div>
      <div className="max-h-[420px] min-w-[420px] space-y-1.5 overflow-y-auto pr-0.5">
        {players.map((p, i) => {
          const e = showErrors ? errors[i] : {};
          return (
            <motion.div key={i} layout className="grid grid-cols-[minmax(120px,1fr)_48px_58px_58px_68px_26px] gap-1.5">
              <input value={p.name} onChange={(ev) => onChange(i, "name", ev.target.value)} placeholder={`Player ${i + 1}`} aria-invalid={Boolean(e.name)} title={e.name} className="field px-2 py-1.5 text-xs" />
              <input value={p.number} onChange={(ev) => onChange(i, "number", ev.target.value)} placeholder="#" inputMode="numeric" aria-invalid={Boolean(e.number)} title={e.number} className="field px-2 py-1.5 text-xs" />
              <input value={p.x} onChange={(ev) => onChange(i, "x", ev.target.value)} placeholder="0–120" inputMode="decimal" aria-invalid={Boolean(e.x)} title={e.x} className="field px-2 py-1.5 text-xs" />
              <input value={p.y} onChange={(ev) => onChange(i, "y", ev.target.value)} placeholder="0–80" inputMode="decimal" aria-invalid={Boolean(e.y)} title={e.y} className="field px-2 py-1.5 text-xs" />
              <select value={p.position} onChange={(ev) => onChange(i, "position", ev.target.value)} className="field px-1.5 py-1.5 text-xs">
                {POSITIONS.map((pos) => <option key={pos} value={pos}>{pos}</option>)}
              </select>
              <button type="button" onClick={() => onRemove(i)} aria-label="Remove player" className="flex items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-danger/15 hover:text-danger">
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </motion.div>
          );
        })}
      </div>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-text-muted">{filled} of {players.length} rows filled</span>
        <button type="button" onClick={onAdd} className="inline-flex items-center gap-1 text-xs font-semibold text-brand hover:underline disabled:opacity-40" disabled={players.length >= 16}>
          <Plus className="h-3.5 w-3.5" /> Add player
        </button>
      </div>
    </GlassCard>
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
        "glass cursor-pointer border-2 border-dashed p-8 text-center transition-all sm:p-12",
        over ? "border-brand/70 bg-brand/10" : "border-white/15 hover:border-brand/40"
      )}
    >
      <motion.div animate={{ y: over ? -4 : 0 }} transition={springSoft}>
        <Icon className={cn("mx-auto mb-4 h-12 w-12", file ? "text-success" : "text-text-muted")} />
      </motion.div>
      {file ? (
        <>
          <div className="flex items-center justify-center gap-2 text-base font-semibold text-white">
            <CheckCircle2 className="h-4 w-4 text-success" /> {file.name}
          </div>
          <p className="mt-1 text-xs text-text-muted">{(file.size / (1024 * 1024)).toFixed(1)} MB</p>
          <button type="button" onClick={(e) => { e.stopPropagation(); onClear(); }} className="mt-3 text-xs font-semibold text-text-secondary underline-offset-2 hover:text-white hover:underline">
            Choose a different file
          </button>
        </>
      ) : (
        <>
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <p className="mt-1 text-sm text-text-secondary">or click to browse</p>
          <p className="mt-2 text-xs text-text-muted">{hint}</p>
        </>
      )}
    </div>
  );
}

function ResolvedNote({ resolved, source }: { resolved: { teamA: PlayerData[]; teamB: PlayerData[]; passes: PassEvent[]; note?: string; source: InputType } | null; source: InputType }) {
  if (!resolved || resolved.source !== source) return null;
  const synthetic = /synthetic/i.test(resolved.note ?? "");
  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className={cn("rounded-xl border p-4 text-sm", synthetic ? "border-warning/40 bg-warning/10 text-warning" : "border-success/40 bg-success/10 text-success")}>
      <div className="flex items-start gap-2">
        {synthetic ? <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /> : <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />}
        <div>
          <div className="font-semibold">
            {resolved.teamA.length} + {resolved.teamB.length} players{resolved.passes.length ? ` · ${resolved.passes.length} passes` : ""} ready
          </div>
          {resolved.note && <div className="mt-0.5 text-xs opacity-90">{resolved.note}</div>}
        </div>
      </div>
    </motion.div>
  );
}

export { Loader2 };
