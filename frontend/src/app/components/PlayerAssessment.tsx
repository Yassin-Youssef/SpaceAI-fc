import { motion, AnimatePresence } from "motion/react";
import { User, Play, ArrowLeft, Video, Database, SlidersHorizontal, Sparkles, Upload, Youtube, CheckCircle2, AlertTriangle, type LucideIcon } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import { assessPlayer, uploadVideo, listDemoPlayers } from "../../lib/api";
import type { HealthResponse, PlayerAssessmentResponse, DemoPlayer } from "../../lib/types";
import { PresetPicker, type PresetItem } from "./common/PresetPicker";
import { Page, PageHeader, GlassCard, Button, ResultsSkeleton, StaggerGrid, StaggerItem } from "./common/Primitives";
import { cn } from "./ui/utils";
import { springSoft } from "../../lib/motion";
import { POSITIONS } from "../../lib/demo";

type Mode = "video" | "data" | "manual";

const MODES: Array<{ id: Mode; label: string; icon: LucideIcon; blurb: string }> = [
  { id: "data", label: "Match data", icon: Database, blurb: "Raw counts from a match or season" },
  { id: "manual", label: "Scout ratings", icon: SlidersHorizontal, blurb: "Rate attributes 0–100 yourself" },
  { id: "video", label: "Video", icon: Video, blurb: "Track a player from footage" },
];

const DEMO_PLAYER = { name: "Lamine Yamal", number: "19", age: "18", foot: "Left", height: "180cm", weight: "72kg", position: "RW" };
const DEMO_STATS = { passes_completed: 45, passes_attempted: 52, tackles: 3, interceptions: 2, shots: 4, dribbles: 7, aerial_duels: 1, distance_covered: 10.5, sprints: 22 };
const DEMO_MANUAL = { Speed: 88, Acceleration: 92, Stamina: 80, Passing: 85, Dribbling: 94, Shooting: 82 };

export function PlayerAssessment({ health }: { health: HealthResponse | null }) {
  const [mode, setMode] = useState<Mode>("data");
  const [view, setView] = useState<"input" | "results">("input");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<PlayerAssessmentResponse | null>(null);

  const [bio, setBio] = useState({ name: "", number: "", age: "", foot: "Right", height: "", weight: "", position: "CM" });
  const [stats, setStats] = useState<Record<string, number>>({ passes_completed: 0, passes_attempted: 0, tackles: 0, interceptions: 0, shots: 0, dribbles: 0, aerial_duels: 0, distance_covered: 0, sprints: 0 });
  const [manual, setManual] = useState<Record<string, number>>({ Speed: 70, Acceleration: 70, Stamina: 70, Passing: 70, Dribbling: 70, Shooting: 70 });
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [videoFile, setVideoFile] = useState<File | undefined>();
  const [tracking, setTracking] = useState<Record<string, unknown> | null>(null);
  const [uploading, setUploading] = useState(false);
  const [showErrors, setShowErrors] = useState(false);
  const [demoPlayers, setDemoPlayers] = useState<DemoPlayer[]>([]);
  const [demoSource, setDemoSource] = useState<{ title: string; match: string; kind: string; note: string } | null>(null);
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
    if (run) void runAssessment({ ...b }, "data", s, DEMO_MANUAL);
    else toast.success(`${b.name} loaded`, { description: dp ? dp.match_title : "Sample stat line" });
  };

  const runAssessment = async (b = bio, m = mode, s = stats, man = manual) => {
    setIsLoading(true);
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
      toast.success(`${res.recommended_role} — assessment ready`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Assessment failed.";
      setResults(null);
      toast.error("Assessment failed", { description: message });
      setView("input");
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
        <div className="space-y-5">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-3">
            <button type="button" onClick={() => setView("input")} className="rounded-lg border border-white/10 bg-white/5 p-2 text-text-secondary hover:bg-white/10 hover:text-white" aria-label="Back"><ArrowLeft className="h-5 w-5" /></button>
            <div>
              <div className="eyebrow">Player assessment</div>
              <h2 className="text-xl font-bold text-white sm:text-2xl">Scouting & tactical profile</h2>
            </div>
          </motion.div>

          {isLoading && <ResultsSkeleton message="Building the attribute radar and scouting report…" />}

          {!isLoading && results && (
            <>
              <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
                <motion.div initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} className="glass-brand p-6">
                  <div className="mx-auto mb-4 flex h-24 w-24 items-center justify-center rounded-full border-4 border-white/10 bg-gradient-to-br from-cyan-500 to-blue-600 text-4xl font-black text-white shadow-[0_0_24px_rgba(0,217,255,0.35)]">{bio.number || "–"}</div>
                  <h3 className="text-center text-2xl font-bold text-white">{bio.name}</h3>
                  <p className="text-center font-semibold text-brand">{results.recommended_role}</p>
                  {demoSource && (
                    <div className="mt-3 flex flex-col items-center gap-1 text-center">
                      <span className={cn("chip", demoSource.kind === "statsbomb" ? "border-success/40 bg-success/10 text-success" : "border-warning/40 bg-warning/10 text-warning")} title={demoSource.note}>
                        {demoSource.kind === "statsbomb" ? "StatsBomb open data" : "Reconstructed stat line"}
                      </span>
                      <span className="text-[11px] text-text-muted">{demoSource.match}</span>
                    </div>
                  )}
                  <dl className="mt-5 space-y-2 text-sm">
                    {[["Position", bio.position || "–"], ["Age", bio.age || "–"], ["Foot", bio.foot], ["Build", `${bio.height || "–"} / ${bio.weight || "–"}`], ["Source", MODES.find((m) => m.id === mode)?.label ?? mode]].map(([k, v]) => (
                      <div key={k} className="flex justify-between border-b border-white/10 pb-2"><dt className="text-text-muted">{k}</dt><dd className="font-medium text-white">{v}</dd></div>
                    ))}
                  </dl>
                  <div className="mt-5 grid grid-cols-2 gap-3">
                    <div>
                      <div className="mb-1.5 text-xs font-bold uppercase tracking-wider text-success">Strengths</div>
                      <ul className="space-y-1 text-sm text-white/90">{results.strengths.map((s) => <li key={s} className="flex gap-1.5"><CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />{s}</li>)}</ul>
                    </div>
                    <div>
                      <div className="mb-1.5 text-xs font-bold uppercase tracking-wider text-danger">To improve</div>
                      <ul className="space-y-1 text-sm text-white/90">{results.weaknesses.map((s) => <li key={s} className="flex gap-1.5"><AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-danger" />{s}</li>)}</ul>
                    </div>
                  </div>
                </motion.div>

                <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 }} className="glass relative p-4">
                  <span className="absolute left-4 top-4 chip border-white/10 bg-white/5 text-text-muted">Attribute radar</span>
                  <div className="h-[380px] w-full pt-6">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart cx="50%" cy="50%" outerRadius="72%" data={radarData}>
                        <PolarGrid stroke="rgba(255,255,255,0.15)" />
                        <PolarAngleAxis dataKey="subject" tick={{ fill: "rgba(255,255,255,0.75)", fontSize: 12, fontWeight: 600 }} />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                        <Radar name={bio.name} dataKey="value" stroke="#00d9ff" strokeWidth={2.5} fill="#00d9ff" fillOpacity={0.35} isAnimationActive animationDuration={900} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                  <StaggerGrid className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                    {radarData.map((d) => (
                      <StaggerItem key={d.subject}>
                        <div className="rounded-lg bg-white/[0.04] px-3 py-2">
                          <div className="flex justify-between text-xs text-text-secondary"><span>{d.subject}</span><span className="font-bold text-white">{Math.round(d.value)}</span></div>
                          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/10"><motion.div initial={{ width: 0 }} animate={{ width: `${d.value}%` }} transition={{ duration: 0.8 }} className="h-full bg-brand" /></div>
                        </div>
                      </StaggerItem>
                    ))}
                  </StaggerGrid>
                </motion.div>
              </div>

              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass p-6">
                <h3 className="mb-3 flex items-center gap-2 text-lg font-bold text-white"><User className="h-5 w-5 text-brand" /> Scouting report</h3>
                <p className="text-[15px] leading-7 text-white/90">{results.scouting_report}</p>
                <p className="mt-3 text-xs text-text-muted">{health?.llm_available ? `Report enhanced by ${health.llm_provider}.` : "Rule-based report. Add an LLM key to the backend for a narrative written by the model."}</p>
              </motion.div>

              <div className="flex flex-wrap gap-2">
                <Button variant="secondary" icon={ArrowLeft} onClick={() => setView("input")}>Adjust inputs</Button>
                <Button variant="ghost" icon={Sparkles} onClick={() => runAssessment()}>Re-run</Button>
              </div>
            </>
          )}
        </div>
      </Page>
    );
  }

  // ── Input ───────────────────────────────────────────────────
  return (
    <Page width="max-w-6xl">
      <div className="space-y-5">
        <PageHeader
          icon={User}
          eyebrow="Advanced"
          title="Player Assessment"
          description="Build an attribute radar, infer the best tactical role and write a scouting report."
          actions={<PresetPicker items={presetItems} storageKey="spaceai.demoPlayer" onRun={(i) => loadDemo(true, i)} onLoad={(i) => loadDemo(false, i)} disabled={isLoading} footer="Stat lines come from StatsBomb events of the demo fixtures; distance and sprints are estimates." />}
        />

        <div className="grid gap-5 lg:grid-cols-[300px_1fr]">
          <GlassCard>
            <h3 className="mb-3 text-base font-bold text-white">Bio</h3>
            <div className="space-y-3">
              <L label="Name"><input className="field" value={bio.name} onChange={(e) => setBio({ ...bio, name: e.target.value })} placeholder="Player name" aria-invalid={showErrors && !bio.name.trim()} /></L>
              <div className="grid grid-cols-2 gap-3">
                <L label="Number"><input className="field" inputMode="numeric" value={bio.number} onChange={(e) => setBio({ ...bio, number: e.target.value })} placeholder="10" /></L>
                <L label="Age"><input className="field" inputMode="numeric" value={bio.age} onChange={(e) => setBio({ ...bio, age: e.target.value })} placeholder="24" /></L>
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
          </GlassCard>

          <div className="space-y-4">
            <div className="glass flex p-1">
              {MODES.map((m) => {
                const active = mode === m.id;
                return (
                  <button key={m.id} type="button" onClick={() => setMode(m.id)} className={cn("relative flex flex-1 flex-col items-center gap-0.5 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors", active ? "text-white" : "text-text-secondary hover:text-white")}>
                    {active && <motion.span layoutId="pa-tab" transition={springSoft} className="absolute inset-0 rounded-lg bg-brand/15 ring-1 ring-brand/40" />}
                    <span className="relative flex items-center gap-2"><m.icon className="h-4 w-4" />{m.label}</span>
                    <span className="relative hidden text-[11px] font-normal text-text-muted sm:block">{m.blurb}</span>
                  </button>
                );
              })}
            </div>

            <AnimatePresence mode="wait" initial={false}>
              <motion.div key={mode} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }}>
                {mode === "data" && (
                  <GlassCard>
                    <p className="mb-4 text-sm text-text-secondary">Enter raw counts. The engine converts them into a five-axis radar and infers the best role.</p>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <Pair label="Passes completed / attempted" a={stats.passes_completed} b={stats.passes_attempted} onA={(v) => { setDemoSource(null); setStats({ ...stats, passes_completed: v }); }} onB={(v) => { setDemoSource(null); setStats({ ...stats, passes_attempted: v }); }} invalid={showErrors && stats.passes_attempted < stats.passes_completed} />
                      <Pair label="Tackles / interceptions" a={stats.tackles} b={stats.interceptions} onA={(v) => setStats({ ...stats, tackles: v })} onB={(v) => setStats({ ...stats, interceptions: v })} />
                      <Pair label="Shots / dribbles" a={stats.shots} b={stats.dribbles} onA={(v) => setStats({ ...stats, shots: v })} onB={(v) => setStats({ ...stats, dribbles: v })} />
                      <Pair label="Aerial duels / sprints" a={stats.aerial_duels} b={stats.sprints} onA={(v) => setStats({ ...stats, aerial_duels: v })} onB={(v) => setStats({ ...stats, sprints: v })} />
                      <L label="Distance covered (km)"><input className="field" type="number" step="0.1" min={0} value={stats.distance_covered} onChange={(e) => setStats({ ...stats, distance_covered: Number(e.target.value) })} /></L>
                    </div>
                  </GlassCard>
                )}
                {mode === "manual" && (
                  <GlassCard>
                    <p className="mb-4 text-sm text-text-secondary">Rate the player on each attribute. Add or rename axes to suit your scouting template.</p>
                    <div className="space-y-3">
                      {Object.entries(manual).map(([k, v]) => (
                        <div key={k} className="flex items-center gap-3">
                          <span className="w-28 text-sm text-text-secondary">{k}</span>
                          <input type="range" min={0} max={100} value={v} onChange={(e) => setManual({ ...manual, [k]: Number(e.target.value) })} className="flex-1" />
                          <span className="w-8 text-right text-sm font-bold text-brand">{v}</span>
                        </div>
                      ))}
                    </div>
                  </GlassCard>
                )}
                {mode === "video" && (
                  <GlassCard className="space-y-4">
                    <p className="text-sm text-text-secondary">Upload a clip or paste a YouTube link. Phase 4 tracks movement and derives physical and positional attributes. Without the optional CV packages the backend uses a clearly labelled synthetic track.</p>
                    <input ref={fileRef} type="file" accept=".mp4,.avi,.mov,.mkv" className="hidden" onChange={(e) => pickVideo(e.target.files?.[0])} />
                    <button type="button" onClick={() => fileRef.current?.click()} className="glass flex w-full items-center justify-center gap-3 border-2 border-dashed border-white/15 p-6 text-sm text-text-secondary transition-colors hover:border-brand/40">
                      <Upload className="h-5 w-5 text-text-muted" /> {videoFile ? videoFile.name : "Choose a video file (MP4, AVI, MOV, MKV)"}
                    </button>
                    <div className="relative">
                      <Youtube className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                      <input className="field pl-9" type="url" value={youtubeUrl} onChange={(e) => { setYoutubeUrl(e.target.value); setVideoFile(undefined); setTracking(null); }} placeholder="https://www.youtube.com/watch?v=…" />
                    </div>
                    {uploading && <p className="text-xs text-brand">Uploading and tracking…</p>}
                    {tracking && <p className="text-xs text-success">Tracking ready · {String((tracking as { message?: string }).message ?? "")}</p>}
                  </GlassCard>
                )}
              </motion.div>
            </AnimatePresence>

            {showErrors && problems.length > 0 && (
              <div className="rounded-xl border border-danger/40 bg-danger/10 p-3 text-sm text-danger">
                <ul className="list-disc space-y-0.5 pl-5">{problems.map((p) => <li key={p}>{p}</li>)}</ul>
              </div>
            )}

            <Button variant="success" size="lg" block icon={Play} loading={isLoading || uploading} onClick={handleRun}>
              Run assessment
            </Button>
          </div>
        </div>
      </div>
    </Page>
  );
}

function L({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block"><span className="mb-1 block text-xs font-semibold uppercase tracking-wider text-text-secondary">{label}</span>{children}</label>;
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
