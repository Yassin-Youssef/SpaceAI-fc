import { motion, AnimatePresence } from "motion/react";
import { UserSearch, Play, ArrowLeft, Video, Database, SlidersHorizontal, RefreshCw, Upload, Youtube, CheckCircle2, AlertTriangle, type LucideIcon } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import { assessPlayer, uploadVideo, listDemoPlayers } from "../../lib/api";
import type { HealthResponse, PlayerAssessmentResponse, DemoPlayer } from "../../lib/types";
import { PresetPicker, type PresetItem } from "./common/PresetPicker";
import { Page, PageHeader, ResultsHeader, Panel, Button, ResultsSkeleton, LoadSwap, EmptyState, FillBar } from "./common/Primitives";
import { RangeField } from "./common/RangeField";
import { cn } from "./ui/utils";
import { springSoft, crossfade } from "../../lib/motion";
import { POSITIONS } from "../../lib/demo";

type Mode = "video" | "data" | "manual";

const MODES: Array<{ id: Mode; label: string; icon: LucideIcon; blurb: string }> = [
  { id: "data", label: "Match stats", icon: Database, blurb: "Raw counts from a match or season" },
  { id: "manual", label: "Scout ratings", icon: SlidersHorizontal, blurb: "Rate six attributes from 0 to 100" },
  { id: "video", label: "Video", icon: Video, blurb: "Track a player from footage" },
];

const DEMO_PLAYER = { name: "Lamine Yamal", number: "19", age: "18", foot: "Left", height: "180cm", weight: "72kg", position: "RW" };
const DEMO_STATS = { passes_completed: 45, passes_attempted: 52, tackles: 3, interceptions: 2, shots: 4, dribbles: 7, aerial_duels: 1, distance_covered: 10.5, sprints: 22 };
const DEMO_MANUAL = { Pace: 90, Shooting: 82, Passing: 85, Dribbling: 94, Defending: 38, Physical: 68 };

export function PlayerAssessment({ health }: { health: HealthResponse | null }) {
  const [mode, setMode] = useState<Mode>("data");
  const [view, setView] = useState<"input" | "results">("input");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<PlayerAssessmentResponse | null>(null);

  const [bio, setBio] = useState({ name: "", number: "", age: "", foot: "Right", height: "", weight: "", position: "CM" });
  const [stats, setStats] = useState<Record<string, number>>({ passes_completed: 0, passes_attempted: 0, tackles: 0, interceptions: 0, shots: 0, dribbles: 0, aerial_duels: 0, distance_covered: 0, sprints: 0 });
  const [manual, setManual] = useState<Record<string, number>>({ Pace: 70, Shooting: 70, Passing: 70, Dribbling: 70, Defending: 70, Physical: 70 });
  const [error, setError] = useState<string | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [videoFile, setVideoFile] = useState<File | undefined>();
  const [tracking, setTracking] = useState<Record<string, unknown> | null>(null);
  const [uploading, setUploading] = useState(false);
  const [showErrors, setShowErrors] = useState(false);
  const [demoPlayers, setDemoPlayers] = useState<DemoPlayer[]>([]);
  const [demoSource, setDemoSource] = useState<{ title: string; match: string; kind: string; note: string } | null>(null);
  // Exact inputs a demo player was loaded with; the source badge is shown only if a run used them unchanged
  const [demoSnapshot, setDemoSnapshot] = useState<string | null>(null);
  const [resultSource, setResultSource] = useState<typeof demoSource>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;
    listDemoPlayers().then((list) => { if (!cancelled) setDemoPlayers(list); }).catch(() => { /* fallback below */ });
    return () => { cancelled = true; };
  }, []);

  const presetItems: PresetItem[] = demoPlayers.length
    ? demoPlayers.map((p) => ({ id: p.id, title: `${p.name} · ${p.team}`, subtitle: p.match_title + " · " + p.match_subtitle, kind: p.source.kind, meta: `${p.stats.passes_completed}/${p.stats.passes_attempted} passes · ${p.stats.shots} shots · ${p.stats.dribbles} dribbles` }))
    : [{ id: "builtin", title: DEMO_PLAYER.name, subtitle: "Built-in sample stat line", kind: "preset" }];

  const problems = useMemo(() => {
    const p: string[] = [];
    if (!bio.name.trim()) p.push("Player name is required.");
    if (bio.age && (Number(bio.age) < 14 || Number(bio.age) > 50)) p.push("Age must be between 14 and 50.");
    if (mode === "data" && stats.passes_attempted < stats.passes_completed) p.push("Passes completed cannot exceed passes attempted.");
    if (mode === "data" && Object.values(stats).every((v) => !v)) p.push("Enter at least one statistic.");
    if (mode === "video" && !videoFile && !/^https?:\/\/(www\.|m\.)?(youtube\.com|youtu\.be)\//i.test(youtubeUrl)) p.push("Provide a video file or a valid YouTube link.");
    return p;
  }, [bio, mode, stats, videoFile, youtubeUrl]);

  const loadDemo = (run: boolean, item?: PresetItem) => {
    const dp = item ? demoPlayers.find((p) => p.id === item.id) : undefined;
    const b = dp
      ? { name: dp.name, number: String(dp.number), age: String(dp.age), foot: dp.foot, height: dp.height, weight: dp.weight, position: dp.position }
      : DEMO_PLAYER;
    const s: Record<string, number> = dp
      ? {
          passes_completed: dp.stats.passes_completed, passes_attempted: dp.stats.passes_attempted,
          tackles: dp.stats.tackles, interceptions: dp.stats.interceptions, shots: dp.stats.shots,
          dribbles: dp.stats.dribbles, aerial_duels: dp.stats.aerial_duels,
          distance_covered: dp.stats.distance_covered, sprints: dp.stats.sprints,
          ...(dp.stats.minutes ? { minutes: dp.stats.minutes } : {}),
          ...(dp.stats.carry_distance_m ? { carry_distance_m: dp.stats.carry_distance_m } : {}),
        }
      : DEMO_STATS;
    setBio(b);
    setStats(s);
    setManual(DEMO_MANUAL);
    setShowErrors(false);
    setMode("data");
    setDemoSource(dp ? { title: dp.name, match: dp.match_title, kind: dp.source.kind, note: dp.source.note } : null);
    setDemoSnapshot(dp ? JSON.stringify({ b, s, m: "data" }) : null);
    if (run) void runAssessment({ ...b }, "data", s, DEMO_MANUAL);
    else toast.success(`${b.name} loaded`, { description: dp ? dp.match_title : "Sample stat line" });
  };

  const runAssessment = async (b = bio, m = mode, s = stats, man = manual) => {
    const untouchedDemo = demoSnapshot !== null && JSON.stringify({ b, s, m }) === demoSnapshot;
    setResultSource(untouchedDemo ? demoSource : null);
    setIsLoading(true);
    setError(null);
    setView("results");
    try {
      const payload: Record<string, unknown> = {
        name: b.name.trim() || "Unknown",
        number: parseInt(b.number, 10) || 0,
        age: parseInt(b.age, 10) || 25,
        preferred_foot: b.foot,
        height: b.height || "180cm",
        weight: b.weight || "75kg",
        position: b.position || undefined,
        input_type: m,
      };
      if (m === "video") {
        let td = tracking;
        if (!td && videoFile) {
          const up = await uploadVideo(videoFile);
          td = up.tracking_data ? { ...up.tracking_data, message: up.message } : null;
          setTracking(td);
        }
        if (td) payload.tracking_data = td;
        else payload.youtube_url = youtubeUrl.trim();
      } else if (m === "data") {
        payload.stats = s;
      } else {
        payload.manual_attributes = man;
      }
      const res = await assessPlayer(payload);
      setResults(res);
      toast.success(`Best fit: ${res.recommended_role}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "The assessment did not finish.";
      setResults(null);
      setError(message);
      toast.error("Assessment failed", { description: message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRun = () => {
    if (problems.length) { setShowErrors(true); toast.error(problems[0]); return; }
    void runAssessment();
  };

  const pickVideo = async (file?: File) => {
    if (!file) return;
    if (!/\.(mp4|avi|mov|mkv)$/i.test(file.name)) { toast.error("Unsupported video type", { description: "Use MP4, AVI, MOV or MKV." }); return; }
    if (file.size > 500 * 1024 * 1024) { toast.error("Video exceeds 500 MB"); return; }
    setVideoFile(file); setYoutubeUrl(""); setTracking(null);
    setUploading(true);
    try {
      const up = await uploadVideo(file);
      setTracking(up.tracking_data ? { ...up.tracking_data, message: up.message } : null);
      toast.success("Tracking extracted", { description: up.message });
    } catch (err) {
      toast.error("Upload failed", { description: err instanceof Error ? err.message : undefined });
    } finally {
      setUploading(false);
    }
  };

  const radarData = useMemo(() => Object.entries(results?.radar_data ?? {}).map(([k, v]) => ({ subject: k, value: v, fullMark: 100 })), [results]);

  // ── Results ─────────────────────────────────────────────────
  if (view === "results") {
    return (
      <Page>
        <ResultsHeader
          context="Player assessment"
          title={bio.name || "Player"}
          onBack={() => setView("input")}
          right={<Button variant="ghost" icon={RefreshCw} onClick={() => runAssessment()} disabled={isLoading}>Run again</Button>}
        />
        <div className="mt-6">
          <LoadSwap loading={isLoading} skeleton={<ResultsSkeleton variant="player" message="Building the radar and writing the scouting report…" />}>
            {error || !results ? (
              <EmptyState
                icon={UserSearch}
                title="The assessment did not finish"
                description={error ?? "No results came back."}
                action={<div className="flex gap-2"><Button icon={RefreshCw} onClick={() => runAssessment()}>Try again</Button><Button variant="secondary" icon={ArrowLeft} onClick={() => setView("input")}>Adjust inputs</Button></div>}
              />
            ) : (
              <div className="space-y-5">
                <div className="grid gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
                  <section className="tile p-5">
                    <div className="flex items-start gap-4">
                      <span className="font-display text-6xl font-semibold leading-none text-section">{bio.number || "–"}</span>
                      <div className="min-w-0 pt-1">
                        <div className="truncate font-display text-2xl font-semibold text-text-primary">{bio.name}</div>
                        <div className="text-sm text-text-secondary">Best fit: <span className="font-medium text-section">{results.recommended_role}</span></div>
                      </div>
                    </div>
                    {resultSource && (
                      <div className="mt-3 flex flex-wrap items-center gap-2">
                        <span className={cn("chip", resultSource.kind === "statsbomb" ? "border-success/40 text-success" : "border-warning/40 text-warning")} title={resultSource.note}>
                          {resultSource.kind === "statsbomb" ? "StatsBomb open data" : "Reconstructed stat line"}
                        </span>
                        <span className="text-xs text-text-muted">{resultSource.match}</span>
                      </div>
                    )}
                    <dl className="mt-5 divide-y divide-line border-y border-line text-sm">
                      {[["Position", bio.position || "–"], ["Age", bio.age || "–"], ["Preferred foot", bio.foot], ["Height and weight", `${bio.height || "–"}, ${bio.weight || "–"}`], ["Assessed from", MODES.find((m) => m.id === mode)?.label ?? mode]].map(([k, v]) => (
                        <div key={k} className="flex justify-between gap-3 py-2"><dt className="text-text-muted">{k}</dt><dd className="text-right text-text-primary">{v}</dd></div>
                      ))}
                    </dl>
                    <div className="mt-5 grid grid-cols-2 gap-4">
                      <div>
                        <div className="mb-1.5 text-sm font-medium text-success">Strengths</div>
                        <ul className="space-y-1 text-sm text-text-primary">{results.strengths.map((s) => <li key={s} className="flex gap-1.5"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />{s}</li>)}</ul>
                      </div>
                      <div>
                        <div className="mb-1.5 text-sm font-medium text-danger">To improve</div>
                        <ul className="space-y-1 text-sm text-text-primary">{results.weaknesses.map((s) => <li key={s} className="flex gap-1.5"><AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-danger" />{s}</li>)}</ul>
                      </div>
                    </div>
                  </section>

                  <section className="tile min-w-0 p-4 sm:p-5">
                    <h2 className="text-xl text-text-primary">Attribute radar</h2>
                    <div className="h-[340px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart cx="50%" cy="50%" outerRadius="72%" data={radarData}>
                          <PolarGrid stroke="var(--line-strong)" />
                          <PolarAngleAxis dataKey="subject" tick={{ fill: "var(--text-secondary)", fontSize: 13, fontFamily: "var(--font-sans)" }} />
                          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                          <Radar name={bio.name} dataKey="value" stroke="var(--section)" strokeWidth={2} fill="var(--section)" fillOpacity={0.25} isAnimationActive animationDuration={500} />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="grid grid-cols-2 gap-x-5 gap-y-3 sm:grid-cols-3">
                      {radarData.map((d, i) => (
                        <div key={d.subject}>
                          <div className="flex justify-between text-sm"><span className="text-text-secondary">{d.subject}</span><span className="tabular font-medium text-text-primary">{Math.round(d.value)}</span></div>
                          <FillBar value={d.value / 100} delay={i * 0.04} className="mt-1" />
                        </div>
                      ))}
                    </div>
                  </section>
                </div>

                <Panel>
                  <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
                    <h2 className="text-2xl text-text-primary">Scouting report</h2>
                    <span className="chip border-line-strong text-text-secondary">{health?.llm_available ? `Language model (${health.llm_provider})` : "Rule-based"}</span>
                  </div>
                  <p className="font-serif max-w-[70ch] text-lg leading-relaxed text-text-primary">{results.scouting_report}</p>
                  {!health?.llm_available && <p className="mt-3 text-sm text-text-muted">Add an LLM key to the backend for a report written by a language model.</p>}
                </Panel>

                <div className="flex flex-wrap gap-2 border-t border-line pt-5">
                  <Button variant="secondary" icon={ArrowLeft} onClick={() => setView("input")}>Adjust inputs</Button>
                </div>
              </div>
            )}
          </LoadSwap>
        </div>
      </Page>
    );
  }

  // ── Input ───────────────────────────────────────────────────
  return (
    <Page width="max-w-6xl">
      <PageHeader
        area="Advanced"
        title="Player Assessment"
        description="Build an attribute radar, find the role a player suits best, and write a scouting report."
        actions={<PresetPicker items={presetItems} storageKey="spaceai.demoPlayer" onRun={(i) => loadDemo(true, i)} onLoad={(i) => loadDemo(false, i)} disabled={isLoading} heading="Demo players" footer="Stat lines come from StatsBomb events in the demo fixtures; distance and sprints are estimates." />}
      />

      <div className="mt-6 grid gap-5 lg:grid-cols-[300px_minmax(0,1fr)]">
        <Panel className="self-start">
          <h3 className="mb-4 text-lg text-text-primary">Player</h3>
          <div className="space-y-3">
            <L label="Name"><input className="field" value={bio.name} onChange={(e) => setBio({ ...bio, name: e.target.value })} placeholder="Player name" aria-invalid={showErrors && !bio.name.trim()} /></L>
            <div className="grid grid-cols-2 gap-3">
              <L label="Shirt number"><input className="field" inputMode="numeric" value={bio.number} onChange={(e) => setBio({ ...bio, number: e.target.value })} placeholder="10" /></L>
              <L label="Age"><input className="field" inputMode="numeric" value={bio.age} onChange={(e) => setBio({ ...bio, age: e.target.value })} placeholder="24" aria-invalid={showErrors && Boolean(bio.age) && (Number(bio.age) < 14 || Number(bio.age) > 50)} /></L>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <L label="Position">
                <select className="field" value={bio.position} onChange={(e) => setBio({ ...bio, position: e.target.value })}>{POSITIONS.map((p) => <option key={p} value={p}>{p}</option>)}</select>
              </L>
              <L label="Preferred foot">
                <select className="field" value={bio.foot} onChange={(e) => setBio({ ...bio, foot: e.target.value })}><option>Right</option><option>Left</option><option>Both</option></select>
              </L>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <L label="Height"><input className="field" value={bio.height} onChange={(e) => setBio({ ...bio, height: e.target.value })} placeholder="180cm" /></L>
              <L label="Weight"><input className="field" value={bio.weight} onChange={(e) => setBio({ ...bio, weight: e.target.value })} placeholder="75kg" /></L>
            </div>
          </div>
        </Panel>

        <div className="min-w-0 space-y-5">
          <div role="tablist" aria-label="Assess from" className="flex overflow-x-auto border-b border-line">
            {MODES.map((m) => {
              const active = mode === m.id;
              return (
                <button key={m.id} type="button" role="tab" aria-selected={active} onClick={() => setMode(m.id)} className={cn("relative flex shrink-0 items-center gap-2 px-4 py-3 text-sm font-medium transition-colors duration-150", active ? "text-text-primary" : "text-text-muted hover:text-text-primary")}>
                  <m.icon className={cn("h-4 w-4", active && "text-section")} strokeWidth={1.75} />
                  {m.label}
                  {active && <motion.span layoutId="pa-tab" transition={springSoft} className="absolute inset-x-0 -bottom-px h-0.5 bg-section-fill" />}
                </button>
              );
            })}
          </div>
          <p className="text-sm text-text-muted">{MODES.find((m) => m.id === mode)?.blurb}.</p>

          <AnimatePresence mode="wait" initial={false}>
            <motion.div key={mode} variants={crossfade} initial="hidden" animate="show" exit="exit">
              {mode === "data" && (
                <Panel>
                  <p className="mb-4 text-sm text-text-secondary">Enter raw counts. The engine normalises them per 90 minutes when minutes are known, builds the radar and picks the best role for the position.</p>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <Pair label="Passes completed / attempted" a={stats.passes_completed} b={stats.passes_attempted} onA={(v) => { setDemoSource(null); setStats({ ...stats, passes_completed: v }); }} onB={(v) => { setDemoSource(null); setStats({ ...stats, passes_attempted: v }); }} invalid={showErrors && stats.passes_attempted < stats.passes_completed} />
                    <Pair label="Tackles / interceptions" a={stats.tackles} b={stats.interceptions} onA={(v) => setStats({ ...stats, tackles: v })} onB={(v) => setStats({ ...stats, interceptions: v })} />
                    <Pair label="Shots / dribbles" a={stats.shots} b={stats.dribbles} onA={(v) => setStats({ ...stats, shots: v })} onB={(v) => setStats({ ...stats, dribbles: v })} />
                    <Pair label="Aerial duels / sprints" a={stats.aerial_duels} b={stats.sprints} onA={(v) => setStats({ ...stats, aerial_duels: v })} onB={(v) => setStats({ ...stats, sprints: v })} />
                    <L label="Distance covered (km)"><input className="field" type="number" step="0.1" min={0} value={stats.distance_covered} onChange={(e) => setStats({ ...stats, distance_covered: Number(e.target.value) })} /></L>
                  </div>
                </Panel>
              )}
              {mode === "manual" && (
                <Panel>
                  <p className="mb-5 text-sm text-text-secondary">Rate each attribute from 0 to 100, as you would on a scouting sheet.</p>
                  <div className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
                    {Object.entries(manual).map(([k, v]) => (
                      <RangeField key={k} label={k} min={0} max={100} value={v} onChange={(nv) => setManual({ ...manual, [k]: nv })} />
                    ))}
                  </div>
                </Panel>
              )}
              {mode === "video" && (
                <Panel className="space-y-4">
                  <p className="text-sm text-text-secondary">Upload a clip or paste a YouTube link. The video pipeline tracks movement and estimates physical and positional attributes. Without the optional vision packages the backend uses a synthetic track and says so.</p>
                  <input ref={fileRef} type="file" accept=".mp4,.avi,.mov,.mkv" className="hidden" onChange={(e) => pickVideo(e.target.files?.[0])} />
                  <button type="button" onClick={() => fileRef.current?.click()} className="press flex w-full items-center gap-3 rounded-md border border-dashed border-line-strong bg-surface-inset p-5 text-left text-sm text-text-secondary hover:border-section/60">
                    <Upload className="h-5 w-5 shrink-0 text-section" /> <span className="truncate">{videoFile ? videoFile.name : "Choose a video file (MP4, AVI, MOV or MKV)"}</span>
                  </button>
                  <div className="relative">
                    <Youtube className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                    <input className="field pl-9" type="url" aria-label="YouTube link" value={youtubeUrl} onChange={(e) => { setYoutubeUrl(e.target.value); setVideoFile(undefined); setTracking(null); }} placeholder="https://www.youtube.com/watch?v=…" />
                  </div>
                  {uploading && <p className="text-sm text-section">Uploading and tracking…</p>}
                  {tracking && <p className="text-sm text-success">Tracking ready. {String((tracking as { message?: string }).message ?? "")}</p>}
                </Panel>
              )}
            </motion.div>
          </AnimatePresence>

          {showErrors && problems.length > 0 && (
            <div role="alert" className="rounded-md border border-danger/50 bg-danger/10 p-3 text-sm text-danger">
              <ul className="list-disc space-y-0.5 pl-5">{problems.map((p) => <li key={p}>{p}</li>)}</ul>
            </div>
          )}

          <Button size="lg" block icon={Play} loading={isLoading || uploading} onClick={handleRun}>
            Assess player
          </Button>
        </div>
      </div>
    </Page>
  );
}

function L({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block"><span className="label">{label}</span>{children}</label>;
}

function Pair({ label, a, b, onA, onB, invalid }: { label: string; a: number; b: number; onA: (v: number) => void; onB: (v: number) => void; invalid?: boolean }) {
  return (
    <L label={label}>
      <div className="flex items-center gap-2">
        <input className="field" type="number" min={0} value={a} onChange={(e) => onA(Number(e.target.value))} aria-invalid={invalid} />
        <span className="text-text-muted">/</span>
        <input className="field" type="number" min={0} value={b} onChange={(e) => onB(Number(e.target.value))} aria-invalid={invalid} />
      </div>
    </L>
  );
}
