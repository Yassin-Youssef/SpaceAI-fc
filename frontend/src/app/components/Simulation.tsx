import { motion, useReducedMotion } from "motion/react";
import { MonitorPlay, Play, Pause, RefreshCw, ArrowLeft, Dices, Goal, Activity, Check } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { runSimulation } from "../../lib/api";
import type { SimulationResponse, SimulationRequest, SimulationFrame } from "../../lib/types";
import { TACTICS, SIM_PRESETS } from "../../lib/demo";
import { PresetPicker, type PresetItem } from "./common/PresetPicker";
import { Page, PageHeader, ResultsHeader, Panel, Button, StatTile, ResultsSkeleton, Collapsible, LoadSwap, EmptyState } from "./common/Primitives";
import { AnimatedNumber } from "./common/AnimatedNumber";
import { RangeField } from "./common/RangeField";
import { cn } from "./ui/utils";

const TEAM_A = "var(--team-a)";
const TEAM_B = "var(--team-b)";

export function Simulation() {
  const [view, setView] = useState<"input" | "results">("input");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [teamSize, setTeamSize] = useState(5);
  const [tacticA, setTacticA] = useState("high_press");
  const [tacticB, setTacticB] = useState("low_block");
  const [steps, setSteps] = useState(400);
  const [seed, setSeed] = useState(7);
  const [results, setResults] = useState<SimulationResponse | null>(null);

  const run = async (override?: Partial<SimulationRequest>) => {
    setIsLoading(true);
    setError(null);
    setView("results");
    try {
      const data: SimulationRequest = { team_size: teamSize, tactic_a: tacticA, tactic_b: tacticB, steps, seed, ...override };
      if (override?.seed !== undefined) setSeed(override.seed);
      const res = await runSimulation(data);
      setResults(res);
      toast.success(`Full time: ${res.tactic_a} ${res.goals_a}, ${res.tactic_b} ${res.goals_b}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "The simulation did not finish.";
      setError(message);
      setResults(null);
      toast.error("Simulation failed", { description: message });
    } finally {
      setIsLoading(false);
    }
  };

  const presetItems: PresetItem[] = SIM_PRESETS.map((p) => ({ id: p.id, title: p.title, subtitle: p.subtitle, kind: "preset", meta: `${p.team_size}v${p.team_size}, ${p.steps} steps` }));
  const applyPreset = (item: PresetItem, runIt: boolean) => {
    const p = SIM_PRESETS.find((x) => x.id === item.id) ?? SIM_PRESETS[0];
    setTeamSize(p.team_size); setTacticA(p.tactic_a); setTacticB(p.tactic_b); setSteps(p.steps); setSeed(p.seed);
    if (runIt) void run({ team_size: p.team_size, tactic_a: p.tactic_a, tactic_b: p.tactic_b, steps: p.steps, seed: p.seed });
    else toast.success(`${p.title} loaded`);
  };

  if (view === "results") {
    return (
      <Page>
        <ResultsHeader
          context="Simulation"
          title={results ? `${results.tactic_a} v ${results.tactic_b}` : "Simulating…"}
          onBack={() => setView("input")}
          right={<Button variant="ghost" icon={Dices} onClick={() => run({ seed: Math.floor(Math.random() * 10000) })} disabled={isLoading}>New random seed</Button>}
        />
        <div className="mt-6">
          <LoadSwap loading={isLoading} skeleton={<ResultsSkeleton variant="simulation" message="Simulating the agents on the pitch…" />}>
            {error || !results ? (
              <EmptyState
                icon={MonitorPlay}
                title="The simulation did not finish"
                description={error ?? "No results came back."}
                action={<div className="flex gap-2"><Button icon={RefreshCw} onClick={() => run()}>Try again</Button><Button variant="secondary" icon={ArrowLeft} onClick={() => setView("input")}>Change setup</Button></div>}
              />
            ) : (
              <div className="space-y-5">
                <Scoreboard r={results} />
                <Replay frames={results.frames} pitchW={results.pitch_width} pitchH={results.pitch_height} events={results.events} />
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <StatTile label={`${results.tactic_a} possession`} value={results.possession_a} suffix="%" decimals={1} tone="teamA" />
                  <StatTile label={`${results.tactic_b} possession`} value={results.possession_b} suffix="%" decimals={1} tone="teamB" />
                  <StatTile label={`${results.tactic_a} territory`} value={results.territorial_control_a} suffix="%" decimals={1} tone="section" hint="Average ball position up the pitch, towards Team B's goal" />
                  <StatTile label="Steps simulated" value={results.steps} tone="neutral" hint={`${results.team_size}v${results.team_size}, seed ${seed}`} />
                </div>
                <EventLog events={results.events} tacticA={results.tactic_a} tacticB={results.tactic_b} />
              </div>
            )}
          </LoadSwap>
        </div>
      </Page>
    );
  }

  return (
    <Page width="max-w-5xl">
      <PageHeader
        area="Advanced"
        title="Simulation"
        description="Play two tactics against each other in a small-sided multi-agent match, then replay it frame by frame."
        actions={<PresetPicker items={presetItems} storageKey="spaceai.simPreset" onRun={(i) => applyPreset(i, true)} onLoad={(i) => applyPreset(i, false)} disabled={isLoading} heading="Simulation presets" footer="Stylised what-ifs using each fixture's tactical identity, not replays of the real matches." />}
      />
      <div className="mt-6 grid gap-5 md:grid-cols-2">
        <TacticPicker label="Team A" color={TEAM_A} value={tacticA} onChange={setTacticA} />
        <TacticPicker label="Team B" color={TEAM_B} value={tacticB} onChange={setTacticB} />
      </div>
      <Panel className="mt-5">
        <h3 className="mb-4 text-lg text-text-primary">Match setup</h3>
        <div className="grid gap-5 sm:grid-cols-3">
          <RangeField label="Team size" display={`${teamSize}v${teamSize}`} min={5} max={7} value={teamSize} onChange={setTeamSize} />
          <RangeField label="Steps" min={100} max={1000} step={50} value={steps} onChange={setSteps} />
          <label className="block">
            <span className="label">Random seed</span>
            <input className="field" type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value) || 0)} />
          </label>
        </div>
        <p className="mt-4 text-sm text-text-muted">The same seed and settings always replay the same match.</p>
      </Panel>
      <Button size="lg" block icon={Play} loading={isLoading} onClick={() => run()} className="mt-5">Run simulation</Button>
    </Page>
  );
}

// ── Sub-components ──────────────────────────────────────────────

function TacticPicker({ label, color, value, onChange }: { label: string; color: string; value: string; onChange: (v: string) => void }) {
  return (
    <Panel>
      <div className="mb-3 flex items-center gap-2 text-lg font-display font-semibold text-text-primary"><span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />{label}</div>
      <div role="radiogroup" aria-label={`${label} tactic`} className="grid grid-cols-2 gap-2">
        {TACTICS.map((t) => {
          const active = t.id === value;
          return (
            <button
              key={t.id}
              type="button"
              role="radio"
              aria-checked={active}
              onClick={() => onChange(t.id)}
              className={cn(
                "press relative rounded-md border p-3 text-left",
                active ? "border-section bg-surface-2" : "border-line bg-surface-inset hover:border-line-strong hover:bg-surface-2/60"
              )}
            >
              <div className="flex items-center justify-between gap-2 text-sm font-medium text-text-primary">
                {t.label}
                {active && <Check className="h-3.5 w-3.5 shrink-0 text-section" />}
              </div>
              <div className="mt-0.5 text-xs text-text-muted">{t.blurb}</div>
            </button>
          );
        })}
      </div>
    </Panel>
  );
}

function Scoreboard({ r }: { r: SimulationResponse }) {
  return (
    <div className="tile grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-4 px-4 py-5 sm:px-8">
      <div className="min-w-0 text-right">
        <div className="flex items-center justify-end gap-2 text-sm text-text-muted">Team A <span className="h-2 w-2 rounded-full bg-team-a" /></div>
        <div className="truncate font-display text-xl font-semibold text-text-primary sm:text-3xl">{r.tactic_a}</div>
      </div>
      <div className="tabular flex items-center gap-3 rounded-sm bg-surface-inset px-4 py-2 font-display text-5xl font-semibold leading-none text-text-primary sm:text-6xl">
        <AnimatedNumber value={r.goals_a} /><span className="text-text-muted">–</span><AnimatedNumber value={r.goals_b} />
      </div>
      <div className="min-w-0">
        <div className="flex items-center gap-2 text-sm text-text-muted"><span className="h-2 w-2 rounded-full bg-team-b" /> Team B</div>
        <div className="truncate font-display text-xl font-semibold text-text-primary sm:text-3xl">{r.tactic_b}</div>
      </div>
    </div>
  );
}

function Replay({ frames, pitchW, pitchH, events }: { frames: SimulationFrame[]; pitchW: number; pitchH: number; events: SimulationResponse["events"] }) {
  const reduce = useReducedMotion();
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(!reduce);
  const raf = useRef<number | null>(null);
  const last = useRef<number>(0);

  useEffect(() => { setIdx(0); setPlaying(!reduce); }, [frames, reduce]);

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
  const glide = { duration: 0.07, ease: "linear" as const };

  return (
    <Collapsible title="Replay" subtitle={`Step ${frame.step} of ${frames[frames.length - 1]?.step ?? frame.step}`} icon={Activity}>
      <div className="overflow-hidden rounded-sm border border-line">
        <svg viewBox={`-2 -2 104 ${H + 4}`} className="block w-full" role="img" aria-label="Simulation replay" style={{ background: "var(--grass)" }}>
          {Array.from({ length: 5 }).map((_, i) => <rect key={i} x={i * 20} y="0" width="10" height={H} style={{ fill: "var(--grass-stripe)" }} />)}
          <g fill="none" style={{ stroke: "var(--pitch-line)" }} strokeWidth="0.4">
            <rect x="0" y="0" width="100" height={H} />
            <line x1="50" y1="0" x2="50" y2={H} />
            <circle cx="50" cy={H / 2} r={H * 0.16} />
            <rect x="0" y={H * 0.25} width="14" height={H * 0.5} />
            <rect x="86" y={H * 0.25} width="14" height={H * 0.5} />
            <rect x="-1.5" y={H * 0.4} width="1.5" height={H * 0.2} />
            <rect x="100" y={H * 0.4} width="1.5" height={H * 0.2} />
          </g>
          {frame.a.map(([x, y], i) => (
            <motion.circle key={`a${i}`} animate={{ cx: x * scale, cy: y * scale }} transition={glide} r="2.2" style={{ fill: TEAM_A }} stroke="#ffffff" strokeWidth="0.4" />
          ))}
          {frame.b.map(([x, y], i) => (
            <motion.circle key={`b${i}`} animate={{ cx: x * scale, cy: y * scale }} transition={glide} r="2.2" style={{ fill: TEAM_B }} stroke="#ffffff" strokeWidth="0.4" />
          ))}
          <motion.circle animate={{ cx: frame.ball[0] * scale, cy: frame.ball[1] * scale }} transition={glide} r="1.3" fill="#ffc61a" stroke="#0d0d0d" strokeWidth="0.35" />
        </svg>
      </div>
      <div className="mt-4 flex items-center gap-3">
        <button type="button" onClick={() => setPlaying((p) => !p)} className="press flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-section-fill text-section-on" aria-label={playing ? "Pause replay" : "Play replay"}>
          {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </button>
        <div className="relative min-w-0 flex-1 pt-3">
          <input type="range" min={0} max={frames.length - 1} value={idx} onChange={(e) => { setPlaying(false); setIdx(Number(e.target.value)); }} className="w-full" aria-label="Replay position" />
          {goalSteps.map((s) => {
            const pos = (frames.findIndex((f) => f.step >= s) / Math.max(1, frames.length - 1)) * 100;
            return <Goal key={s} className="pointer-events-none absolute -top-1 h-3.5 w-3.5 text-warning" style={{ left: `calc(${Math.max(0, Math.min(100, pos))}% - 7px)` }} aria-hidden />;
          })}
        </div>
        <span className="w-24 shrink-0 text-right text-sm text-text-muted">
          {frame.pos ? <span style={{ color: frame.pos === "A" ? TEAM_A : TEAM_B }}>Team {frame.pos} ball</span> : "Loose ball"}
        </span>
      </div>
      {goalSteps.length > 0 && <p className="mt-2 text-xs text-text-muted">Goal markers sit above the timeline.</p>}
    </Collapsible>
  );
}

function EventLog({ events, tacticA, tacticB }: { events: SimulationResponse["events"]; tacticA: string; tacticB: string }) {
  const label: Record<string, string> = { goal: "Goal", shot_saved: "Shot saved", turnover: "Turnover", tackle: "Tackle won", recovery: "Recovery" };
  return (
    <Collapsible title="Key moments" subtitle={`${events.length} logged`} icon={Goal} defaultOpen={false}>
      {events.length ? (
        <ol className="max-h-72 divide-y divide-line overflow-y-auto border-y border-line pr-1">
          {events.map((ev, i) => (
            <li key={i} className="flex items-center gap-3 py-2 text-sm">
              <span className="tabular w-14 shrink-0 text-text-muted">{ev.step}</span>
              <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: ev.team === "A" ? TEAM_A : TEAM_B }} />
              <span className={cn("shrink-0 font-medium", ev.type === "goal" ? "text-warning" : "text-text-primary")}>{label[ev.type] ?? ev.type}</span>
              <span className="truncate text-text-muted">{ev.team === "A" ? tacticA : tacticB}{ev.role ? `, ${ev.role}` : ""}{typeof ev.player === "number" ? ` (${ev.player})` : ""}</span>
            </li>
          ))}
        </ol>
      ) : (
        <p className="text-sm text-text-muted">A quiet match: no shots or turnovers were logged.</p>
      )}
    </Collapsible>
  );
}
