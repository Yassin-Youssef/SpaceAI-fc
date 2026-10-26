import { motion } from "motion/react";
import { ArrowRight, Github, Clock, Database, PenLine, type LucideIcon } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type ReactNode, type RefObject } from "react";
import type { UserProfile, SavedAnalysis, DemoMatchSummary } from "../../lib/types";
import { FEATURES, SECTION_LABEL, sectionVar, type Feature } from "../../lib/features";
import { GITHUB_URL, PHASES, STACK } from "../../lib/project";
import { DEMO_TEAM_A, DEMO_TEAM_B, DEMO_PASSES, DEMO_TEAM_A_NAME, DEMO_TEAM_B_NAME, DEMO_TEAM_A_COLOR, DEMO_TEAM_B_COLOR } from "../../lib/demo";
import { toPlayerData, listDemoMatches } from "../../lib/api";
import { Page, Button, Skeleton, Band } from "./common/Primitives";
import { PitchPreview } from "./common/PitchPreview";
import { PipelineFlow } from "./common/PipelineFlow";
import { reveal, staggerContainer, staggerItem } from "../../lib/motion";

interface HomeProps {
  user?: UserProfile | null;
  recentAnalyses?: SavedAnalysis[];
  onFeatureClick: (featureId: string) => void;
  onNavigate: (view: string) => void;
  /** Run Full Match Analysis on a bundled fixture. */
  onRunMatch: (matchId: string) => void;
}

const AREA_ROLE: Record<Feature["section"], string> = {
  analysis: "What the engine sees in positions and passes.",
  intelligence: "What it concludes, and how it explains itself.",
  advanced: "Scouting, simulation and what-if comparisons.",
};

export function Home({ recentAnalyses = [], onFeatureClick, onNavigate, onRunMatch }: HomeProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const teamA = useMemo(() => toPlayerData(DEMO_TEAM_A), []);
  const teamB = useMemo(() => toPlayerData(DEMO_TEAM_B), []);
  const [matches, setMatches] = useState<DemoMatchSummary[] | null>(null);

  useEffect(() => {
    let off = false;
    listDemoMatches().then((m) => { if (!off) setMatches(m); }).catch(() => { if (!off) setMatches([]); });
    return () => { off = true; };
  }, []);

  return (
    <Page scrollRef={scrollRef}>
      {/* ── Hero ── */}
      <section className="grid items-end gap-10 pb-12 pt-2 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] lg:gap-12 lg:pt-6">
        <motion.div variants={staggerContainer(0.06)} initial="hidden" animate="show" className="min-w-0">
          <motion.h1 variants={staggerItem} className="text-5xl text-text-primary sm:text-7xl xl:text-8xl">
            Read the game from where the players stand.
          </motion.h1>
          <motion.p variants={staggerItem} className="mt-6 max-w-xl text-lg text-text-secondary">
            Give SpaceAI FC eleven positions and the passes between them. It finds both formations, maps who
            controls each zone, scores how well a side plays through pressure, and tells the coaching staff what
            to change and why.
          </motion.p>
          <motion.div variants={staggerItem} className="mt-8 flex flex-wrap gap-3">
            <Button size="lg" onClick={() => onFeatureClick("full-match")}>Start an analysis</Button>
            <Button size="lg" variant="secondary" onClick={() => onNavigate("about")}>How it works</Button>
          </motion.div>
        </motion.div>

        <motion.figure
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1, ease: [0.23, 1, 0.32, 1] }}
          className="min-w-0"
        >
          <PitchPreview teamA={teamA} teamB={teamB} teamAColor={DEMO_TEAM_A_COLOR} teamBColor={DEMO_TEAM_B_COLOR} passes={DEMO_PASSES} showNames={false} passDelay={0.45} />
          <figcaption className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-text-secondary">
            <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ background: DEMO_TEAM_A_COLOR }} />{DEMO_TEAM_A_NAME}, with its passes drawn</span>
            <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ background: DEMO_TEAM_B_COLOR }} />{DEMO_TEAM_B_NAME}</span>
          </figcaption>
        </motion.figure>
      </section>

      {/* ── Pick a match: a broadcast band of real fixtures ── */}
      <Band className="py-12">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-3xl uppercase text-text-primary sm:text-5xl">Pick a match</h2>
            <p className="mt-2 text-text-secondary">Real fixtures, ready to analyse. One click runs every phase of the engine.</p>
          </div>
        </div>
        <div className="mt-8 grid gap-px bg-line sm:grid-cols-2 xl:grid-cols-3">
          {matches === null
            ? Array.from({ length: 3 }).map((_, i) => <div key={i} className="bg-band p-5"><Skeleton className="h-24" /></div>)
            : matches.length === 0
            ? <p className="bg-band p-5 text-text-secondary">The engine is offline, so the fixture list is unavailable. Full Match Analysis still has a built-in sample.</p>
            : matches.map((m) => <MatchCard key={m.id} m={m} onClick={() => onRunMatch(m.id)} />)}
        </div>
      </Band>

      {recentAnalyses.length > 0 && (
        <Reveal root={scrollRef} className="pt-12">
          <div className="mb-3 flex items-baseline justify-between">
            <h2 className="text-2xl text-text-primary">Pick up where you left off</h2>
            <button type="button" onClick={() => onNavigate("history")} className="text-sm font-semibold underline underline-offset-4 hover:text-section">All saved analyses</button>
          </div>
          <div className="grid gap-px border border-line bg-line sm:grid-cols-3">
            {recentAnalyses.slice(0, 3).map((a) => (
              <button key={a.id} type="button" onClick={() => onNavigate("history")} className="flex items-center gap-3 bg-surface-1 px-4 py-3 text-left transition-colors hover:bg-surface-2">
                <Clock className="h-4 w-4 shrink-0 text-text-muted" />
                <span className="min-w-0">
                  <span className="block truncate font-semibold text-text-primary">{a.match_name}</span>
                  <span className="block truncate text-sm text-text-muted">{a.feature}, {formatDate(a.created_at)}</span>
                </span>
              </button>
            ))}
          </div>
        </Reveal>
      )}

      {/* ── Feature index ── */}
      <Reveal root={scrollRef} className="py-16">
        <SectionHead title="Twelve tools, three areas" text="Each area keeps its colour throughout the app, so you always know what kind of answer you are reading." />
        <div className="mt-10 grid gap-8 lg:grid-cols-3 lg:gap-6">
          {(Object.keys(SECTION_LABEL) as Feature["section"][]).map((area) => (
            <div key={area} style={sectionVar(area)}>
              <div className="bg-section-fill px-4 py-3 text-section-on">
                <div className="font-display text-2xl uppercase">{SECTION_LABEL[area]}</div>
                <p className="text-sm font-medium opacity-80">{AREA_ROLE[area]}</p>
              </div>
              <ul className="border-x border-b border-line bg-surface-1">
                {FEATURES.filter((f) => f.section === area).map((f) => (
                  <li key={f.id} className="border-t border-line first:border-t-0">
                    <FeatureRow icon={f.icon} name={f.name} description={f.description} onClick={() => onFeatureClick(f.id)} />
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Reveal>

      {/* ── Pipeline ── */}
      <Reveal root={scrollRef} className="border-t-2 border-text-primary py-16">
        <SectionHead title="One loop behind every feature" text="SpaceAI FC is modelled on a robot's cognitive pipeline. Each feature runs part of this loop; Full Match Analysis runs all of it." />
        <div className="mt-10">
          <PipelineFlow container={scrollRef} />
        </div>
      </Reveal>

      {/* ── Engine phases ── */}
      <Reveal root={scrollRef} className="grid gap-10 border-t-2 border-text-primary py-16 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
        <SectionHead title="Four engine phases" text="Stateless Python modules. An orchestrator passes each phase's output to the next, and the API exposes every phase on its own." />
        <ol className="divide-y divide-line border-y border-line">
          {PHASES.map((p, i) => (
            <li key={p.name} className="grid grid-cols-[3.5rem_minmax(0,1fr)] gap-4 py-6">
              <span className="font-num text-6xl leading-none text-text-primary">{i + 1}</span>
              <div className="min-w-0">
                <h3 className="text-xl text-text-primary">{p.name}</h3>
                <p className="mt-1 text-text-secondary">{p.text}</p>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {p.modules.map((m) => <code key={m} className="bg-surface-2 px-1.5 py-0.5 text-xs text-text-secondary">{m}.py</code>)}
                </div>
              </div>
            </li>
          ))}
        </ol>
      </Reveal>

      {/* ── Stack ── */}
      <Reveal root={scrollRef} className="grid gap-10 border-t-2 border-text-primary py-16 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
        <SectionHead title="Built with" text="No API key needed: without one, answers come from the knowledge graph and templates." />
        <dl className="divide-y divide-line border-y border-line">
          {STACK.map((s) => (
            <div key={s.group} className="grid gap-1 py-4 sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-4">
              <dt className="font-bold text-text-primary">{s.group}</dt>
              <dd className="text-text-secondary">{s.items.join(", ")}</dd>
            </div>
          ))}
        </dl>
      </Reveal>

      {/* ── Credit ── */}
      <Band className="-mb-16 py-12">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="font-display text-3xl uppercase text-text-primary">Built by Yassin Youssef</div>
          <p className="mt-1 text-text-secondary">Engine, API and interface, designed and written end to end.</p>
        </div>
        <a
          href={GITHUB_URL}
          target="_blank"
          rel="noreferrer"
          className="press inline-flex h-12 items-center gap-2 self-start rounded-md bg-white px-5 font-bold text-band hover:bg-green-fill"
        >
          <Github className="h-4 w-4" /> Source on GitHub
        </a>
        </div>
      </Band>
    </Page>
  );
}

function MatchCard({ m, onClick }: { m: DemoMatchSummary; onClick: () => void }) {
  const real = m.source_kind === "statsbomb";
  return (
    <button type="button" onClick={onClick} className="group flex flex-col gap-4 bg-band p-5 text-left transition-colors duration-150 hover:bg-surface-1">
      <div className="flex items-center justify-between gap-3 text-sm text-text-muted">
        <span className="truncate">{m.competition}</span>
        <span className="shrink-0">{formatYear(m.date)}</span>
      </div>
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1">
        <span className="font-display truncate text-2xl uppercase text-text-primary">{m.team_a}</span>
        <span className="font-num text-4xl leading-none text-text-primary">{m.score.a}</span>
        <span className="font-display truncate text-2xl uppercase text-text-primary">{m.team_b}</span>
        <span className="font-num text-4xl leading-none text-text-primary">{m.score.b}</span>
      </div>
      <div className="flex items-center justify-between gap-3">
        <span className={`chip ${real ? "border-success/60 text-success" : "border-warning/60 text-warning"}`}>
          {real ? <Database className="h-3 w-3" /> : <PenLine className="h-3 w-3" />}
          {real ? "StatsBomb data" : "Reconstructed"}
        </span>
        <span className="flex items-center gap-1.5 text-sm font-bold text-green-fill">
          Analyse <ArrowRight className="h-4 w-4 transition-transform duration-150 group-hover:translate-x-1" />
        </span>
      </div>
    </button>
  );
}

function Reveal({ root, className, children }: { root: RefObject<HTMLElement | null>; className?: string; children: ReactNode }) {
  return (
    <motion.section variants={reveal} initial="hidden" whileInView="show" viewport={{ once: true, root, amount: 0.15 }} className={className}>
      {children}
    </motion.section>
  );
}

function SectionHead({ title, text }: { title: string; text: string }) {
  return (
    <div className="max-w-2xl">
      <h2 className="text-3xl uppercase text-text-primary sm:text-5xl">{title}</h2>
      <p className="mt-3 text-text-secondary">{text}</p>
    </div>
  );
}

function FeatureRow({ icon: Icon, name, description, onClick }: { icon: LucideIcon; name: string; description: string; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} className="group flex w-full items-start gap-3 px-4 py-4 text-left transition-colors duration-150 hover:bg-surface-2">
      <Icon className="mt-1 h-5 w-5 shrink-0 text-section" strokeWidth={2} />
      <span className="min-w-0 flex-1">
        <span className="font-display block text-lg text-text-primary">{name}</span>
        <span className="mt-0.5 block text-sm text-text-secondary">{description}</span>
      </span>
      <ArrowRight className="mt-1.5 h-4 w-4 shrink-0 -translate-x-1 text-text-primary opacity-0 transition-[opacity,transform] duration-150 group-hover:translate-x-0 group-hover:opacity-100 group-focus-visible:opacity-100" />
    </button>
  );
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { day: "2-digit", month: "short" });
  } catch {
    return iso.slice(0, 10);
  }
}

function formatYear(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}
