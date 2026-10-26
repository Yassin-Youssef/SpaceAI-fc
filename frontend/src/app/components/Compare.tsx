import { motion } from "motion/react";
import { ArrowLeftRight, Play, ArrowLeft, RefreshCw, Trophy, Scale } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { compareSimulations } from "../../lib/api";
import type { SimulationCompareResponse, SimulationCompareRequest, MatchupSummary } from "../../lib/types";
import { TACTICS, COMPARE_PRESETS } from "../../lib/demo";
import { PresetPicker, type PresetItem } from "./common/PresetPicker";
import { Page, PageHeader, ResultsHeader, Panel, Button, ResultsSkeleton, LoadSwap, EmptyState } from "./common/Primitives";
import { AnimatedNumber } from "./common/AnimatedNumber";
import { Markdown } from "./common/Markdown";
import { RangeField } from "./common/RangeField";
import { cn } from "./ui/utils";
import { EASE_OUT } from "../../lib/motion";

const label = (id: string) => TACTICS.find((t) => t.id === id)?.label ?? id;

export function Compare() {
  const [view, setView] = useState<"input" | "results">("input");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
    setError(null);
    setView("results");
    try {
      const data: SimulationCompareRequest = { team_size: teamSize, tactic_a: m1.a, tactic_b: m1.b, tactic_a2: m2.a, tactic_b2: m2.b, runs, steps_per_run: steps, ...override };
      const res = await compareSimulations(data);
      setResults(res);
      toast.success("Comparison finished");
    } catch (err) {
      const message = err instanceof Error ? err.message : "The comparison did not finish.";
      setError(message);
      setResults(null);
      toast.error("Comparison failed", { description: message });
    } finally {
      setIsLoading(false);
    }
  };

  const presetItems: PresetItem[] = COMPARE_PRESETS.map((p) => ({ id: p.id, title: p.title, subtitle: p.subtitle, kind: "preset", meta: `${p.runs} runs each, ${p.team_size}v${p.team_size}` }));
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
        <ResultsHeader
          context="Compare"
          title={`Two match-ups, ${results?.matchup_1.runs ?? runs} runs each`}
          onBack={() => setView("input")}
          right={<Button variant="ghost" icon={RefreshCw} onClick={() => run()} disabled={isLoading}>Run again</Button>}
        />
        <div className="mt-6">
          <LoadSwap loading={isLoading} skeleton={<ResultsSkeleton variant="compare" message={`Simulating each match-up ${runs} times…`} />}>
            {error || !results ? (
              <EmptyState
                icon={ArrowLeftRight}
                title="The comparison did not finish"
                description={error ?? "No results came back."}
                action={<div className="flex gap-2"><Button icon={RefreshCw} onClick={() => run()}>Try again</Button><Button variant="secondary" icon={ArrowLeft} onClick={() => setView("input")}>Change match-ups</Button></div>}
              />
            ) : (
              <div className="space-y-6">
                <div className="tile flex items-start gap-4 border-l-2 border-l-section p-5">
                  {winner ? <Trophy className="mt-1 h-5 w-5 shrink-0 text-section" /> : <Scale className="mt-1 h-5 w-5 shrink-0 text-section" />}
                  <div>
                    <div className="text-sm text-text-muted">Verdict</div>
                    <div className="font-display text-2xl font-semibold text-text-primary">{readableVerdict(results.verdict)}</div>
                  </div>
                </div>

                <div className="grid gap-5 lg:grid-cols-2">
                  <MatchupCard n={1} m={results.matchup_1} winner={winner === 1} />
                  <MatchupCard n={2} m={results.matchup_2} winner={winner === 2} />
                </div>

                {results.insights && (
                  <Panel>
                    <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
                      <h2 className="text-2xl text-text-primary">What the numbers say</h2>
                      <span className="chip border-line-strong text-text-secondary">{results.insights_mode === "template" ? "Template, from the numbers" : "Language model"}</span>
                    </div>
                    <Markdown text={results.insights} className="font-serif max-w-[70ch] text-lg text-text-primary" />
                  </Panel>
                )}

                <div className="flex flex-wrap gap-2 border-t border-line pt-5">
                  <Button variant="secondary" icon={ArrowLeft} onClick={() => setView("input")}>Change match-ups</Button>
                </div>
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
        title="Compare"
        description="Simulate two tactical match-ups several times each and see which setup comes out ahead, and why."
        actions={<PresetPicker items={presetItems} storageKey="spaceai.comparePreset" onRun={(i) => applyPreset(i, true)} onLoad={(i) => applyPreset(i, false)} disabled={isLoading} heading="Comparison presets" footer="Each preset answers one tactical question by simulating two match-ups several times." />}
      />
      <div className="mt-6 grid gap-5 md:grid-cols-2">
        <MatchupEditor n={1} value={m1} onChange={setM1} />
        <MatchupEditor n={2} value={m2} onChange={setM2} />
      </div>
      <Panel className="mt-5">
        <h3 className="mb-4 text-lg text-text-primary">Simulation settings</h3>
        <div className="grid gap-5 sm:grid-cols-3">
          <RangeField label="Team size" display={`${teamSize}v${teamSize}`} min={5} max={7} value={teamSize} onChange={setTeamSize} />
          <RangeField label="Runs per match-up" min={1} max={10} value={runs} onChange={setRuns} />
          <RangeField label="Steps per run" min={100} max={1000} step={50} value={steps} onChange={setSteps} />
        </div>
        <p className="mt-4 text-sm text-text-muted">More runs smooth out randomness. Ten runs of 1,000 steps can take around a minute.</p>
      </Panel>
      <Button size="lg" block icon={Play} loading={isLoading} onClick={() => run()} className="mt-5">Run comparison</Button>
    </Page>
  );
}

function readableVerdict(v: string): string {
  return v.replace(/^Matchup (\d)/, "Match-up $1").replace("Both matchups", "Both match-ups");
}

function MatchupEditor({ n, value, onChange }: { n: number; value: { a: string; b: string }; onChange: (v: { a: string; b: string }) => void }) {
  return (
    <Panel>
      <div className="mb-4 flex items-baseline gap-3">
        <span className="font-display text-4xl font-semibold leading-none text-section">{n}</span>
        <h3 className="text-lg text-text-primary">Match-up {n}</h3>
      </div>
      <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-end gap-2">
        <label className="block min-w-0">
          <span className="label">Side A</span>
          <select className="field" value={value.a} onChange={(e) => onChange({ ...value, a: e.target.value })}>{TACTICS.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}</select>
        </label>
        <span className="pb-2.5 text-sm text-text-muted">v</span>
        <label className="block min-w-0">
          <span className="label">Side B</span>
          <select className="field" value={value.b} onChange={(e) => onChange({ ...value, b: e.target.value })}>{TACTICS.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}</select>
        </label>
      </div>
      <p className="mt-3 text-sm text-text-muted">
        {TACTICS.find((t) => t.id === value.a)?.blurb}. Against: {TACTICS.find((t) => t.id === value.b)?.blurb.toLowerCase()}.
      </p>
    </Panel>
  );
}

function MatchupCard({ n, m, winner }: { n: number; m: MatchupSummary; winner: boolean }) {
  const shares: Array<{ label: string; a: number }> = [
    { label: "Possession", a: m.avg_possession_a },
    { label: "Territory", a: m.avg_territorial_control_a },
  ];
  return (
    <article className={cn("tile relative p-5", winner && "border-section/60")}>
      {winner && <span className="chip absolute right-4 top-4 border-section/60 text-section"><Trophy className="h-3 w-3" /> Comes out ahead</span>}
      <div className="text-sm text-text-muted">Match-up {n}, {m.runs} runs</div>
      <h3 className="mt-0.5 pr-36 text-xl text-text-primary">{label(m.tactic_a)} <span className="text-text-muted">v</span> {label(m.tactic_b)}</h3>

      <div className="mt-5 flex items-end gap-4">
        <div>
          <div className="text-xs text-text-muted">Average goals</div>
          <div className="font-display text-5xl font-semibold leading-none text-text-primary">
            <span className="text-team-a"><AnimatedNumber value={m.avg_goals_a} decimals={2} /></span>
            <span className="mx-2 text-text-muted">–</span>
            <span className="text-team-b"><AnimatedNumber value={m.avg_goals_b} decimals={2} /></span>
          </div>
        </div>
      </div>

      <div className="mt-6 space-y-4">
        {shares.map((r) => (
          <div key={r.label}>
            <div className="mb-1.5 flex items-center justify-between text-sm">
              <span className="text-text-secondary">{r.label}</span>
              <span className="tabular text-text-muted">
                <span className="text-team-a">{r.a.toFixed(1)}%</span><span className="mx-1.5">to</span><span className="text-team-b">{(100 - r.a).toFixed(1)}%</span>
              </span>
            </div>
            <div className="relative h-2 overflow-hidden rounded-sm bg-team-b">
              <motion.div
                initial={{ scaleX: 0 }}
                animate={{ scaleX: r.a / 100 }}
                transition={{ duration: 0.5, ease: EASE_OUT }}
                className="absolute inset-0 origin-left bg-team-a"
              />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex gap-4 text-xs text-text-muted">
        <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-team-a" />{label(m.tactic_a)}</span>
        <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-team-b" />{label(m.tactic_b)}</span>
      </div>
    </article>
  );
}
