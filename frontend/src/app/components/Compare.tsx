import { motion } from "motion/react";
import { GitCompare, Play, ArrowLeft, Sparkles, Trophy } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { compareSimulations } from "../../lib/api";
import type { SimulationCompareResponse, SimulationCompareRequest, MatchupSummary } from "../../lib/types";
import { TACTICS, COMPARE_PRESETS } from "../../lib/demo";
import { PresetPicker, type PresetItem } from "./common/PresetPicker";
import { Page, PageHeader, GlassCard, Button, ResultsSkeleton } from "./common/Primitives";
import { AnimatedNumber } from "./common/AnimatedNumber";
import { cn } from "./ui/utils";

const label = (id: string) => TACTICS.find((t) => t.id === id)?.label ?? id;

export function Compare() {
  const [view, setView] = useState<"input" | "results">("input");
  const [isLoading, setIsLoading] = useState(false);
  const [teamSize, setTeamSize] = useState(5);
  const [m1, setM1] = useState({ a: "possession", b: "low_block" });
  const [m2, setM2] = useState({ a: "high_press", b: "counter_attack" });
  const [runs, setRuns] = useState(3);
  const [steps, setSteps] = useState(300);
  const [results, setResults] = useState<SimulationCompareResponse | null>(null);

  const run = async (override?: Partial<SimulationCompareRequest>) => {
    if (!override && m1.a === m2.a && m1.b === m2.b) {
      toast.error("The two match-ups are identical", { description: "Change at least one tactic so there is something to compare." });
      return;
    }
    setIsLoading(true);
    setView("results");
    try {
      const data: SimulationCompareRequest = { team_size: teamSize, tactic_a: m1.a, tactic_b: m1.b, tactic_a2: m2.a, tactic_b2: m2.b, runs, steps_per_run: steps, ...override };
      const res = await compareSimulations(data);
      setResults(res);
      toast.success("Comparison complete");
    } catch (err) {
      toast.error("Comparison failed", { description: err instanceof Error ? err.message : undefined });
      setView("input");
    } finally {
      setIsLoading(false);
    }
  };

  const presetItems: PresetItem[] = COMPARE_PRESETS.map((p) => ({ id: p.id, title: p.title, subtitle: p.subtitle, kind: "preset", meta: `${p.runs} runs · ${p.team_size}v${p.team_size}` }));
  const applyPreset = (item: PresetItem, runIt: boolean) => {
    const p = COMPARE_PRESETS.find((x) => x.id === item.id) ?? COMPARE_PRESETS[0];
    setM1(p.m1); setM2(p.m2); setRuns(p.runs); setSteps(p.steps); setTeamSize(p.team_size);
    if (runIt) void run({ tactic_a: p.m1.a, tactic_b: p.m1.b, tactic_a2: p.m2.a, tactic_b2: p.m2.b, runs: p.runs, steps_per_run: p.steps, team_size: p.team_size });
    else toast.success(`${p.title} loaded`);
  };

  if (view === "results") {
    const winner = results ? (results.verdict.startsWith("Matchup 1") ? 1 : results.verdict.startsWith("Matchup 2") ? 2 : 0) : 0;
    return (
      <Page>
        <div className="space-y-5">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-3">
            <button type="button" onClick={() => setView("input")} className="rounded-lg border border-white/10 bg-white/5 p-2 text-text-secondary hover:bg-white/10 hover:text-white" aria-label="Back"><ArrowLeft className="h-5 w-5" /></button>
            <div>
              <div className="eyebrow">Compare</div>
              <h2 className="text-xl font-bold text-white sm:text-2xl">Side-by-side match-ups</h2>
            </div>
          </motion.div>

          {isLoading && <ResultsSkeleton message={`Averaging ${runs} runs per match-up…`} />}

          {!isLoading && results && (
            <>
              <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} className="glass-brand flex items-center gap-4 p-5">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 text-[#1a1200] shadow-[0_0_24px_rgba(255,193,7,0.4)]"><Trophy className="h-6 w-6" /></div>
                <div>
                  <div className="eyebrow">Verdict</div>
                  <div className="text-lg font-bold text-white">{results.verdict}</div>
                </div>
              </motion.div>
              <div className="grid gap-5 lg:grid-cols-2">
                <MatchupCard n={1} m={results.matchup_1} winner={winner === 1} accent="#00d9ff" />
                <MatchupCard n={2} m={results.matchup_2} winner={winner === 2} accent="#7b61ff" />
              </div>
              <div className="flex gap-2">
                <Button variant="secondary" icon={ArrowLeft} onClick={() => setView("input")}>Change match-ups</Button>
                <Button variant="ghost" icon={Sparkles} onClick={() => run()}>Re-run</Button>
              </div>
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
          icon={GitCompare}
          eyebrow="Advanced"
          title="Compare Match-ups"
          description="Simulate two tactical pairings several times each and see which setup comes out ahead."
          actions={<PresetPicker items={presetItems} storageKey="spaceai.comparePreset" onRun={(i) => applyPreset(i, true)} onLoad={(i) => applyPreset(i, false)} disabled={isLoading} footer="Each preset answers one tactical question by simulating two match-ups several times." />}
        />
        <div className="grid gap-5 md:grid-cols-2">
          <MatchupEditor n={1} accent="#00d9ff" value={m1} onChange={setM1} />
          <MatchupEditor n={2} accent="#7b61ff" value={m2} onChange={setM2} />
        </div>
        <GlassCard>
          <h3 className="mb-4 text-base font-bold text-white">Settings</h3>
          <div className="grid gap-5 sm:grid-cols-3">
            <Slider label={`Team size · ${teamSize}v${teamSize}`} min={5} max={7} value={teamSize} onChange={setTeamSize} />
            <Slider label={`Runs per match-up · ${runs}`} min={1} max={10} value={runs} onChange={setRuns} />
            <Slider label={`Steps per run · ${steps}`} min={100} max={1000} step={50} value={steps} onChange={setSteps} />
          </div>
        </GlassCard>
        <Button variant="success" size="lg" block icon={Play} loading={isLoading} onClick={() => run()}>Run comparison</Button>
      </div>
    </Page>
  );
}

function MatchupEditor({ n, accent, value, onChange }: { n: number; accent: string; value: { a: string; b: string }; onChange: (v: { a: string; b: string }) => void }) {
  return (
    <GlassCard>
      <div className="mb-3 flex items-center gap-2 text-base font-bold text-white"><span className="h-3 w-3 rounded-full" style={{ background: accent }} />Match-up {n}</div>
      <div className="space-y-3">
        <label className="block">
          <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-secondary">Team A tactic</span>
          <select className="field" value={value.a} onChange={(e) => onChange({ ...value, a: e.target.value })}>{TACTICS.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}</select>
        </label>
        <div className="text-center text-xs font-bold uppercase tracking-widest text-text-muted">vs</div>
        <label className="block">
          <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-secondary">Team B tactic</span>
          <select className="field" value={value.b} onChange={(e) => onChange({ ...value, b: e.target.value })}>{TACTICS.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}</select>
        </label>
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

function MatchupCard({ n, m, winner, accent }: { n: number; m: MatchupSummary; winner: boolean; accent: string }) {
  const rows: Array<{ label: string; a: number; b: number; suffix?: string }> = [
    { label: "Average goals", a: m.avg_goals_a, b: m.avg_goals_b },
    { label: "Possession", a: m.avg_possession_a, b: 100 - m.avg_possession_a, suffix: "%" },
    { label: "Territory", a: m.avg_territorial_control_a, b: 100 - m.avg_territorial_control_a, suffix: "%" },
  ];
  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: n * 0.08 }} className={cn("glass relative overflow-hidden p-5", winner && "ring-2 ring-warning/60")}>
      <div className="absolute inset-x-0 top-0 h-1" style={{ background: accent }} />
      {winner && <span className="absolute right-4 top-4 chip border-warning/40 bg-warning/15 text-warning"><Trophy className="h-3.5 w-3.5" /> Better</span>}
      <div className="eyebrow mb-1">Match-up {n} · {m.runs} runs</div>
      <h3 className="mb-4 text-lg font-bold text-white">{label(m.tactic_a)} <span className="text-text-muted">vs</span> {label(m.tactic_b)}</h3>
      <div className="space-y-4">
        {rows.map((r) => {
          const total = r.a + r.b || 1;
          return (
            <div key={r.label}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="text-text-secondary">{r.label}</span>
                <span className="tabular-nums text-white"><AnimatedNumber value={r.a} decimals={r.suffix ? 1 : 2} suffix={r.suffix} /> <span className="text-text-muted">·</span> <AnimatedNumber value={r.b} decimals={r.suffix ? 1 : 2} suffix={r.suffix} /></span>
              </div>
              <div className="flex h-2.5 overflow-hidden rounded-full bg-white/5">
                <motion.div initial={{ width: 0 }} animate={{ width: `${(r.a / total) * 100}%` }} transition={{ duration: 0.8 }} style={{ background: "#00d9ff" }} />
                <motion.div initial={{ width: 0 }} animate={{ width: `${(r.b / total) * 100}%` }} transition={{ duration: 0.8 }} style={{ background: "#ff5a6e" }} />
              </div>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}
