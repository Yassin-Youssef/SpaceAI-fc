import { motion } from "motion/react";
import { Gamepad2, Play, ArrowLeft, Pause, RotateCcw, Sparkles, Goal, Activity } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { runSimulation } from "../../lib/api";
import type { SimulationResponse, SimulationRequest, SimulationFrame } from "../../lib/types";
import { TACTICS, SIM_PRESETS } from "../../lib/demo";
import { PresetPicker, type PresetItem } from "./common/PresetPicker";
import { Page, PageHeader, GlassCard, Button, StatTile, ResultsSkeleton, Collapsible } from "./common/Primitives";
import { AnimatedNumber } from "./common/AnimatedNumber";
import { cn } from "./ui/utils";

const TEAM_A = "#00d9ff";
const TEAM_B = "#ff5a6e";

export function Simulation() {
  const [view, setView] = useState<"input" | "results">("input");
  const [isLoading, setIsLoading] = useState(false);
  const [teamSize, setTeamSize] = useState(5);
  const [tacticA, setTacticA] = useState("high_press");
  const [tacticB, setTacticB] = useState("low_block");
  const [steps, setSteps] = useState(400);
  const [seed, setSeed] = useState(7);
  const [results, setResults] = useState<SimulationResponse | null>(null);

  const run = async (override?: Partial<SimulationRequest>) => {
    setIsLoading(true);
    setView("results");
    try {
      const data: SimulationRequest = { team_size: teamSize, tactic_a: tacticA, tactic_b: tacticB, steps, seed, ...override };
      const res = await runSimulation(data);
      setResults(res);
      toast.success(`Full time: ${res.tactic_a} ${res.goals_a} – ${res.goals_b} ${res.tactic_b}`);
    } catch (err) {
      toast.error("Simulation failed", { description: err instanceof Error ? err.message : undefined });
      setView("input");
    } finally {
      setIsLoading(false);
    }
  };

  const presetItems: PresetItem[] = SIM_PRESETS.map((p) => ({ id: p.id, title: p.title, subtitle: p.subtitle, kind: "preset", meta: `${p.team_size}v${p.team_size} · ${p.steps} steps` }));
  const applyPreset = (item: PresetItem, runIt: boolean) => {
    const p = SIM_PRESETS.find((x) => x.id === item.id) ?? SIM_PRESETS[0];
    setTeamSize(p.team_size); setTacticA(p.tactic_a); setTacticB(p.tactic_b); setSteps(p.steps); setSeed(p.seed);
    if (runIt) void run({ team_size: p.team_size, tactic_a: p.tactic_a, tactic_b: p.tactic_b, steps: p.steps, seed: p.seed });
    else toast.success(`${p.title} loaded`);
  };

  if (view === "results") {
    return (
      <Page>
        <div className="space-y-5">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-3">
            <button type="button" onClick={() => setView("input")} className="rounded-lg border border-white/10 bg-white/5 p-2 text-text-secondary hover:bg-white/10 hover:text-white" aria-label="Back"><ArrowLeft className="h-5 w-5" /></button>
            <div>
              <div className="eyebrow">Simulation</div>
              <h2 className="text-xl font-bold text-white sm:text-2xl">{results ? `${results.tactic_a} vs ${results.tactic_b}` : "Running…"}</h2>
            </div>
            <div className="ml-auto flex gap-2">
              <Button variant="ghost" size="sm" icon={RotateCcw} onClick={() => run({ seed: Math.floor(Math.random() * 10000) })} disabled={isLoading}>New seed</Button>
            </div>
          </motion.div>

          {isLoading && <ResultsSkeleton message="Simulating agents on the pitch…" />}

          {!isLoading && results && (
            <>
              <Scoreboard r={results} />
              <Replay frames={results.frames} pitchW={results.pitch_width} pitchH={results.pitch_height} events={results.events} />
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <StatTile label={`${results.tactic_a} possession`} value={results.possession_a} suffix="%" decimals={1} tone="teamA" />
                <StatTile label={`${results.tactic_b} possession`} value={results.possession_b} suffix="%" decimals={1} tone="teamB" />
                <StatTile label="Territory (A)" value={results.territorial_control_a} suffix="%" decimals={1} tone="brand" hint="Average ball position" />
                <StatTile label="Steps simulated" value={results.steps} tone="neutral" hint={`${results.team_size}v${results.team_size}`} />
              </div>
              <EventLog events={results.events} tacticA={results.tactic_a} tacticB={results.tactic_b} />
            </>
          )}
        </div>
      </Page>
    );
  }

  return (
    <Page width="max-w-5xl">
      <div className="space-y-5">
        <PageHeader
          icon={Gamepad2}
          eyebrow="Advanced"
          title="Tactical Simulation"
          description="Pit two tactical presets against each other in a multi-agent small-sided match and replay it."
          actions={<PresetPicker items={presetItems} storageKey="spaceai.simPreset" onRun={(i) => applyPreset(i, true)} onLoad={(i) => applyPreset(i, false)} disabled={isLoading} footer="Stylised what-ifs using each fixture's tactical identity — not replays of the real matches." />}
        />
        <div className="grid gap-5 md:grid-cols-2">
          <TacticPicker label="Team A" color={TEAM_A} value={tacticA} onChange={setTacticA} />
          <TacticPicker label="Team B" color={TEAM_B} value={tacticB} onChange={setTacticB} />
        </div>
        <GlassCard>
          <h3 className="mb-4 text-base font-bold text-white">Match setup</h3>
          <div className="grid gap-5 sm:grid-cols-3">
            <Slider label={`Team size · ${teamSize}v${teamSize}`} min={5} max={7} value={teamSize} onChange={setTeamSize} />
            <Slider label={`Steps · ${steps}`} min={100} max={1000} step={50} value={steps} onChange={setSteps} />
            <label className="block">
              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-secondary">Random seed</span>
              <input className="field" type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value) || 0)} />
            </label>
          </div>
        </GlassCard>
        <Button variant="success" size="lg" block icon={Play} loading={isLoading} onClick={() => run()}>Run simulation</Button>
      </div>
    </Page>
  );
}

// ── Sub-components ──────────────────────────────────────────────

function TacticPicker({ label, color, value, onChange }: { label: string; color: string; value: string; onChange: (v: string) => void }) {
  return (
    <GlassCard>
      <div className="mb-3 flex items-center gap-2 text-base font-bold text-white"><span className="h-3 w-3 rounded-full" style={{ background: color }} />{label}</div>
      <div className="grid grid-cols-2 gap-2">
        {TACTICS.map((t) => {
          const active = t.id === value;
          return (
            <button key={t.id} type="button" onClick={() => onChange(t.id)} className={cn("rounded-lg border p-3 text-left transition-all", active ? "border-transparent bg-white/10 ring-2" : "border-white/10 bg-white/[0.03] hover:bg-white/[0.06]")} style={active ? { boxShadow: `0 0 0 2px ${color}` } : undefined}>
              <div className="text-sm font-semibold text-white">{t.label}</div>
              <div className="text-[11px] text-text-muted">{t.blurb}</div>
            </button>
          );
        })}
      </div>
    </GlassCard>
  );
}

function Slider({ label, min, max, step = 1, value, onChange }: { label: string; min: number; max: number; step?: number; value: number; onChange: (v: number) => void }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-secondary">{label}</span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} className="w-full" />
    </label>
  );
}

function Scoreboard({ r }: { r: SimulationResponse }) {
  return (
    <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} className="glass-brand relative overflow-hidden p-6">
      <div className="pitch-grid-bg pointer-events-none absolute inset-0 opacity-60" />
      <div className="relative grid grid-cols-[1fr_auto_1fr] items-center gap-4">
        <div className="text-right">
          <div className="text-xs font-semibold uppercase tracking-wider" style={{ color: TEAM_A }}>Team A</div>
          <div className="text-lg font-bold text-white sm:text-2xl">{r.tactic_a}</div>
        </div>
        <div className="flex items-center gap-3 rounded-2xl bg-black/30 px-5 py-3 text-4xl font-black text-white sm:text-5xl">
          <AnimatedNumber value={r.goals_a} /><span className="text-text-muted">–</span><AnimatedNumber value={r.goals_b} />
        </div>
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider" style={{ color: TEAM_B }}>Team B</div>
          <div className="text-lg font-bold text-white sm:text-2xl">{r.tactic_b}</div>
        </div>
      </div>
    </motion.div>
  );
}

function Replay({ frames, pitchW, pitchH, events }: { frames: SimulationFrame[]; pitchW: number; pitchH: number; events: SimulationResponse["events"] }) {
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(true);
  const raf = useRef<number | null>(null);
  const last = useRef<number>(0);

  useEffect(() => { setIdx(0); setPlaying(true); }, [frames]);

  useEffect(() => {
    if (!playing || frames.length === 0) return;
    const tick = (t: number) => {
      if (t - last.current > 70) {
        last.current = t;
        setIdx((i) => (i + 1) % frames.length);
      }
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => { if (raf.current) cancelAnimationFrame(raf.current); };
  }, [playing, frames]);

  const frame = frames[idx];
  const goalSteps = useMemo(() => events.filter((e) => e.type === "goal").map((e) => e.step), [events]);
  if (!frame) return null;

  const scale = 100 / pitchW;
  const H = pitchH * scale;

  return (
    <Collapsible title="Match replay" subtitle={`Step ${frame.step} · ${frames.length} frames`} icon={Activity}>
      <div className="overflow-hidden rounded-xl bg-[#0b2e23]">
        <svg viewBox={`-2 -2 104 ${H + 4}`} className="block w-full" role="img" aria-label="Simulation replay">
          <rect x="0" y="0" width="100" height={H} fill="#0f3d2e" rx="1" />
          <g fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="0.5">
            <rect x="0" y="0" width="100" height={H} />
            <line x1="50" y1="0" x2="50" y2={H} />
            <circle cx="50" cy={H / 2} r={H * 0.16} />
            <rect x="0" y={H * 0.25} width="14" height={H * 0.5} />
            <rect x="86" y={H * 0.25} width="14" height={H * 0.5} />
            <rect x="-1.5" y={H * 0.4} width="1.5" height={H * 0.2} />
            <rect x="100" y={H * 0.4} width="1.5" height={H * 0.2} />
          </g>
          {frame.a.map(([x, y], i) => (
            <motion.circle key={`a${i}`} animate={{ cx: x * scale, cy: y * scale }} transition={{ duration: 0.07, ease: "linear" }} r="2.2" fill={TEAM_A} stroke="#062" strokeWidth="0.3" />
          ))}
          {frame.b.map(([x, y], i) => (
            <motion.circle key={`b${i}`} animate={{ cx: x * scale, cy: y * scale }} transition={{ duration: 0.07, ease: "linear" }} r="2.2" fill={TEAM_B} stroke="#400" strokeWidth="0.3" />
          ))}
          <motion.circle animate={{ cx: frame.ball[0] * scale, cy: frame.ball[1] * scale }} transition={{ duration: 0.07, ease: "linear" }} r="1.2" fill="#fff" stroke="#000" strokeWidth="0.3" />
        </svg>
      </div>
      <div className="mt-3 flex items-center gap-3">
        <button type="button" onClick={() => setPlaying((p) => !p)} className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand text-[#0a0e27]" aria-label={playing ? "Pause" : "Play"}>
          {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </button>
        <div className="relative flex-1">
          <input type="range" min={0} max={frames.length - 1} value={idx} onChange={(e) => { setPlaying(false); setIdx(Number(e.target.value)); }} className="w-full" aria-label="Replay position" />
          {goalSteps.map((s) => {
            const pos = (frames.findIndex((f) => f.step >= s) / Math.max(1, frames.length - 1)) * 100;
            return <Goal key={s} className="pointer-events-none absolute -top-4 h-3.5 w-3.5 text-warning" style={{ left: `calc(${Math.max(0, Math.min(100, pos))}% - 7px)` }} />;
          })}
        </div>
        <span className="w-24 text-right text-xs tabular-nums text-text-muted">
          {frame.pos ? <span style={{ color: frame.pos === "A" ? TEAM_A : TEAM_B }}>Team {frame.pos} ball</span> : "Loose ball"}
        </span>
      </div>
    </Collapsible>
  );
}

function EventLog({ events, tacticA, tacticB }: { events: SimulationResponse["events"]; tacticA: string; tacticB: string }) {
  const label: Record<string, string> = { goal: "GOAL", shot_saved: "Shot saved", turnover: "Turnover", tackle: "Tackle won", recovery: "Recovery" };
  return (
    <Collapsible title="Event log" subtitle={`${events.length} key moments`} icon={Goal} defaultOpen={false}>
      {events.length ? (
        <div className="max-h-72 space-y-1.5 overflow-y-auto pr-1">
          {events.map((ev, i) => (
            <div key={i} className={cn("flex items-center gap-3 rounded-lg px-3 py-2 text-sm", ev.type === "goal" ? "bg-warning/10 text-warning" : "bg-white/[0.04] text-text-secondary")}>
              <span className="w-14 text-xs tabular-nums text-text-muted">#{ev.step}</span>
              <span className="h-2 w-2 rounded-full" style={{ background: ev.team === "A" ? TEAM_A : TEAM_B }} />
              <span className="font-semibold text-white">{label[ev.type] ?? ev.type}</span>
              <span className="truncate">{ev.team === "A" ? tacticA : tacticB}{ev.role ? ` · ${ev.role}` : ""}{typeof ev.player === "number" ? ` #${ev.player}` : ""}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-text-muted">A quiet match — no shots or turnovers were logged.</p>
      )}
    </Collapsible>
  );
}
