/**
 * Feature-specific result renderers.  Every block is defensive about the
 * shape of the data it receives so a partial backend response still renders.
 */
import { motion, AnimatePresence } from "motion/react";
import {
  Download, Image as ImageIcon, Columns4, Map, Share2, Gauge as GaugeIcon, Waypoints, Users, ListOrdered,
  FileText, Brain, CheckCircle2, XCircle, TrendingUp, X,
} from "lucide-react";
import { Fragment, useEffect, useState, type ReactNode } from "react";
import { base64ToImageUrl } from "../../../lib/api";
import type {
  VisualizationData, FormationResponse, SpaceControlResponse, PassNetworkResponse,
  PressResistanceResponse, PatternsResponse, RolesResponse, IntelligenceResponse,
  ExplanationResponse, SWOTItem, RecommendationItem, PatternItem, PlayerRoleItem,
} from "../../../lib/types";
import { AnimatedNumber } from "../common/AnimatedNumber";
import { Markdown } from "../common/Markdown";
import { Collapsible, StatTile, StaggerGrid, StaggerItem, PriorityBadge, ConfidenceBar } from "../common/Primitives";
import { cn } from "../ui/utils";
import { EASE_OUT } from "../../../lib/motion";

export interface TeamMeta {
  teamAName: string;
  teamBName: string;
  teamAColor: string;
  teamBColor: string;
}

const fmtPct = (v: unknown, digits = 0) => (typeof v === "number" ? `${(v <= 1 ? v * 100 : v).toFixed(digits)}%` : "–");
const num = (v: unknown, fallback = 0) => (typeof v === "number" && Number.isFinite(v) ? v : fallback);
const str = (v: unknown, fallback = "–") => (typeof v === "string" && v ? v : typeof v === "number" ? String(v) : fallback);
const titleCase = (s: string) => s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
const sentence = (s: string) => { const t = s.replace(/_/g, " "); return t.charAt(0).toUpperCase() + t.slice(1); };

// ── Visualisations ──────────────────────────────────────────────

export function VizGrid({ visualizations, title = "Visualisations", defaultOpen = true }: { visualizations: VisualizationData[]; title?: string; defaultOpen?: boolean }) {
  if (!visualizations?.length) return null;
  return (
    <Collapsible title={title} subtitle={`${visualizations.length} rendered by the engine. Click one to enlarge.`} icon={ImageIcon} defaultOpen={defaultOpen}>
      <StaggerGrid className={cn("grid gap-4", visualizations.length > 1 && "md:grid-cols-2")}>
        {visualizations.map((viz, i) => (
          <StaggerItem key={`${viz.title}-${i}`}>
            <VizCard viz={viz} />
          </StaggerItem>
        ))}
      </StaggerGrid>
    </Collapsible>
  );
}

function VizCard({ viz }: { viz: VisualizationData }) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState(false);
  const src = base64ToImageUrl(viz.image_base64);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  const download = () => {
    const a = document.createElement("a");
    a.href = src;
    a.download = `${viz.title.replace(/\s+/g, "_")}.png`;
    a.click();
  };

  return (
    <figure className="min-w-0">
      <div className="mb-2 flex items-center justify-between gap-2">
        <figcaption className="min-w-0">
          <div className="truncate text-sm font-medium text-text-primary">{viz.title}</div>
          {viz.description && <div className="truncate text-xs text-text-muted">{viz.description}</div>}
        </figcaption>
        <button type="button" onClick={download} className="press shrink-0 rounded-md p-1.5 text-text-muted hover:bg-surface-2 hover:text-text-primary" aria-label={`Download ${viz.title}`}>
          <Download className="h-4 w-4" />
        </button>
      </div>
      <div className="relative overflow-hidden rounded-sm border border-line bg-surface-inset">
        {!loaded && !failed && <div className="skeleton absolute inset-0" />}
        {failed ? (
          <div className="flex aspect-[3/2] items-center justify-center p-4 text-sm text-text-muted">This image could not be decoded.</div>
        ) : (
          <motion.img
            src={src}
            alt={viz.title}
            onLoad={() => setLoaded(true)}
            onError={() => setFailed(true)}
            onClick={() => setOpen(true)}
            initial={{ opacity: 0 }}
            animate={{ opacity: loaded ? 1 : 0 }}
            transition={{ duration: 0.25, ease: EASE_OUT }}
            className="block max-h-[380px] min-h-[120px] w-full cursor-zoom-in object-contain"
          />
        )}
      </div>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.15 } }}
            className="fixed inset-0 z-[60] flex cursor-zoom-out items-center justify-center bg-black/85 p-4"
            onClick={() => setOpen(false)}
            role="dialog"
            aria-modal="true"
            aria-label={viz.title}
          >
            <button type="button" onClick={() => setOpen(false)} className="press absolute right-4 top-4 rounded-md bg-surface-2 p-2 text-text-primary" aria-label="Close">
              <X className="h-5 w-5" />
            </button>
            <motion.img
              initial={{ scale: 0.96, opacity: 0 }}
              animate={{ scale: 1, opacity: 1, transition: { duration: 0.2, ease: EASE_OUT } }}
              exit={{ scale: 0.98, opacity: 0, transition: { duration: 0.12 } }}
              src={src}
              alt={viz.title}
              className="max-h-full max-w-full rounded-sm"
            />
          </motion.div>
        )}
      </AnimatePresence>
    </figure>
  );
}

// ── Formation ───────────────────────────────────────────────────

export function FormationSection({ data, meta }: { data: FormationResponse; meta: TeamMeta }) {
  const teams = [
    { name: meta.teamAName, color: meta.teamAColor, formation: data.team_a_formation, conf: data.team_a_confidence, method: data.team_a_method },
    { name: meta.teamBName, color: meta.teamBColor, formation: data.team_b_formation, conf: data.team_b_confidence, method: data.team_b_method },
  ].filter((t) => t.formation);
  if (!teams.length) return null;
  return (
    <Collapsible title="Detected formations" subtitle="The average shape, read by clustering player depth" icon={Columns4}>
      <div className={cn("grid gap-4", teams.length > 1 && "sm:grid-cols-2")}>
        {teams.map((t) => (
          <div key={t.name} className="tile relative overflow-hidden p-5">
            <div className="absolute inset-x-0 top-0 h-0.5" style={{ background: t.color }} />
            <div className="text-sm text-text-muted">{t.name}</div>
            <div className="font-display text-6xl font-semibold leading-none" style={{ color: t.color }}>{t.formation}</div>
            <div className="mt-4">
              <div className="mb-1 text-xs text-text-muted">Confidence</div>
              <ConfidenceBar value={num(t.conf) <= 1 ? num(t.conf) : num(t.conf) / 100} color={t.color} />
            </div>
            {t.method && <div className="mt-2 text-xs text-text-muted">Method: {sentence(String(t.method))}</div>}
          </div>
        ))}
      </div>
    </Collapsible>
  );
}

// ── Space control ───────────────────────────────────────────────

export function SpaceControlSection({ data, meta }: { data: SpaceControlResponse; meta: TeamMeta }) {
  const zones = Object.entries(data.zones ?? {});
  const mid = data.midfield_control ?? {};
  return (
    <Collapsible title="Territorial control" subtitle="Share of each third, from the Voronoi model" icon={Map}>
      <div className="grid gap-3 sm:grid-cols-3">
        <StatTile label={meta.teamAName} value={num(data.team_a_control)} suffix="%" decimals={1} tone="teamA" hint="Of the whole pitch" />
        <StatTile label={meta.teamBName} value={num(data.team_b_control)} suffix="%" decimals={1} tone="teamB" hint="Of the whole pitch" />
        <StatTile label="Middle third" value={num(mid.team_a)} suffix="%" decimals={1} tone="section" hint={`${meta.teamAName}'s share`} />
      </div>
      {zones.length > 0 && (
        <div className="mt-6 space-y-4">
          {zones.map(([zone, z], i) => (
            <DualBar key={zone} label={sentence(zone)} a={num(z?.team_a)} b={num(z?.team_b)} meta={meta} delay={i * 0.05} />
          ))}
        </div>
      )}
    </Collapsible>
  );
}

function DualBar({ label, a, b, meta, delay = 0 }: { label: string; a: number; b: number; meta: TeamMeta; delay?: number }) {
  const total = a + b || 1;
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-sm">
        <span className="text-text-secondary">{label}</span>
        <span className="tabular text-text-muted">
          <span style={{ color: meta.teamAColor }}>{a.toFixed(0)}%</span>
          <span className="mx-1.5">to</span>
          <span style={{ color: meta.teamBColor }}>{b.toFixed(0)}%</span>
        </span>
      </div>
      {/* Team B fills the track; Team A grows over it with scaleX. */}
      <div className="relative h-2 overflow-hidden rounded-sm" style={{ background: meta.teamBColor }}>
        <motion.div
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: a / total }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay, ease: EASE_OUT }}
          className="absolute inset-0 origin-left"
          style={{ background: meta.teamAColor }}
        />
        <div className="absolute inset-y-0 left-1/2 w-px bg-background/70" aria-hidden />
      </div>
    </div>
  );
}

// ── Pass network ────────────────────────────────────────────────

export function PassNetworkSection({ data, meta }: { data: PassNetworkResponse; meta: TeamMeta }) {
  const kd = data.key_distributor ?? {};
  const mi = data.most_involved ?? {};
  const centrality = Object.values(data.centrality ?? {}).sort((x, y) => num(y.betweenness) - num(x.betweenness));
  return (
    <>
      <div className="grid gap-3 sm:grid-cols-3">
        <StatTile label="Passes in the network" value={num(data.total_passes)} tone="section" />
        <div className="tile px-4 py-3.5">
          <div className="text-sm text-text-muted">Key distributor</div>
          <div className="mt-1 truncate font-display text-3xl font-semibold leading-none text-text-primary">{str(kd.name)} <span className="text-lg text-text-muted">{str(kd.number, "")}</span></div>
          <div className="mt-1.5 text-xs text-text-muted">Betweenness {num(kd.betweenness).toFixed(3)}</div>
        </div>
        <div className="tile px-4 py-3.5">
          <div className="text-sm text-text-muted">Most involved</div>
          <div className="mt-1 truncate font-display text-3xl font-semibold leading-none text-text-primary">{str(mi.name)} <span className="text-lg text-text-muted">{str(mi.number, "")}</span></div>
          <div className="mt-1.5 text-xs text-text-muted">{num(mi.passes_made)} made, {num(mi.passes_received)} received</div>
        </div>
      </div>

      <Collapsible title="Connections" subtitle={`${meta.teamAName}: strongest links and players left out`} icon={Share2}>
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h4 className="mb-2 text-sm font-medium text-text-secondary">Strongest links</h4>
            {(data.top_connections ?? []).length ? (
              <ol className="divide-y divide-line border-y border-line">
                {(data.top_connections ?? []).map((c, i) => (
                  <li key={i} className="flex items-center justify-between gap-3 py-2 text-sm">
                    <span className="min-w-0 truncate text-text-primary">{str(c.from)} <span className="text-text-muted">to</span> {str(c.to)}</span>
                    <span className="tabular shrink-0 font-semibold text-section">{num(c.passes)}</span>
                  </li>
                ))}
              </ol>
            ) : <p className="text-sm text-text-muted">No pair connected more than once.</p>}
          </div>
          <div>
            <h4 className="mb-2 text-sm font-medium text-text-secondary">Weak links</h4>
            {(data.weak_links ?? []).length ? (
              <ol className="divide-y divide-line border-y border-line">
                {(data.weak_links ?? []).map((w, i) => (
                  <li key={i} className="flex items-center justify-between gap-3 py-2 text-sm">
                    <span className="min-w-0 truncate text-text-primary">{str(w.name)} <span className="text-text-muted">{str(w.number, "")}</span></span>
                    <span className="shrink-0 text-warning">{num(w.total_involvement)} involvements</span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="flex items-center gap-2 text-sm text-success"><CheckCircle2 className="h-4 w-4" /> Every outfield player is involved in the build-up.</p>
            )}
          </div>
        </div>
      </Collapsible>

      {centrality.length > 0 && (
        <Collapsible title="Centrality" subtitle="Who the network runs through, by betweenness" icon={TrendingUp} defaultOpen={false}>
          <DataTable
            columns={["Player", "No.", "Degree", "Betweenness", "Eigenvector"]}
            rows={centrality.map((c) => [str(c.name), str(c.number, ""), num(c.degree).toFixed(3), num(c.betweenness).toFixed(3), num(c.eigenvector).toFixed(3)])}
          />
        </Collapsible>
      )}
    </>
  );
}

// ── Press resistance ────────────────────────────────────────────

export function PressResistanceSection({ data, meta }: { data: PressResistanceResponse; meta: TeamMeta }) {
  const score = num(data.press_resistance_score);
  const tone = score >= 70 ? "var(--success)" : score >= 45 ? "var(--warning)" : "var(--danger)";
  const verdict = score >= 70 ? "Comfortable under pressure" : score >= 45 ? "Holding up, with some risk" : "Struggling to play out";
  return (
    <>
      <div className="grid gap-4 lg:grid-cols-[260px_minmax(0,1fr)]">
        <div className="tile flex flex-col items-center justify-center p-5">
          <Gauge value={score} color={tone} />
          <div className="mt-3 font-medium text-text-primary">{verdict}</div>
          <div className="text-sm text-text-muted">{meta.teamAName}</div>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <StatTile label="Passes analysed" value={num(data.total_passes)} tone="neutral" />
          <StatTile label="Under pressure" value={num(data.passes_under_pressure)} tone="warning" />
          <StatTile label="Completed overall" value={num(data.pass_success_overall) * 100} suffix="%" tone="section" />
          <StatTile label="Completed under pressure" value={num(data.pass_success_under_pressure) * 100} suffix="%" tone="section" />
          <StatTile label="Escape rate" value={num(data.escape_rate) * 100} suffix="%" tone="success" hint="Forward passes that beat the press" className="sm:col-span-2" />
        </div>
      </div>
      <Collapsible title="Vulnerable zones" subtitle="Where passes break down under pressure" icon={GaugeIcon}>
        {(data.vulnerable_zones ?? []).length ? (
          <ul className="divide-y divide-line border-y border-line">
            {(data.vulnerable_zones ?? []).map((z, i) => (
              <li key={i} className="flex items-center justify-between gap-3 py-2.5">
                <div className="min-w-0">
                  <div className="font-medium text-text-primary">{str(z.zone)}</div>
                  <div className="text-sm text-text-muted">{num(z.total_passes)} passes attempted here</div>
                </div>
                <div className="shrink-0 text-right">
                  <div className="tabular font-display text-2xl font-semibold text-danger">{fmtPct(z.success_rate)}</div>
                  <div className="text-xs text-text-muted">completed</div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="flex items-center gap-2 text-sm text-success"><CheckCircle2 className="h-4 w-4" /> No zone shows a dangerous drop in pass completion.</p>
        )}
      </Collapsible>
    </>
  );
}

function Gauge({ value, color }: { value: number; color: string }) {
  const r = 54;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value)) / 100;
  return (
    <div className="relative h-36 w-36">
      <svg viewBox="0 0 128 128" className="h-full w-full -rotate-90">
        <circle cx="64" cy="64" r={r} stroke="var(--surface-3)" strokeWidth="8" fill="none" />
        <motion.circle
          cx="64" cy="64" r={r} stroke={color} strokeWidth="8" fill="none" strokeLinecap="butt"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          whileInView={{ strokeDashoffset: c * (1 - pct) }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, ease: EASE_OUT }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-5xl font-semibold leading-none text-text-primary"><AnimatedNumber value={value} /></span>
        <span className="text-xs text-text-muted">out of 100</span>
      </div>
    </div>
  );
}

// ── Patterns ────────────────────────────────────────────────────

export function PatternsSection({ data, meta }: { data: PatternsResponse; meta: TeamMeta }) {
  const groups = [
    { name: meta.teamAName, color: meta.teamAColor, items: data.team_a_patterns ?? [] },
    { name: meta.teamBName, color: meta.teamBColor, items: data.team_b_patterns ?? [] },
  ].filter((g) => g.items.length);
  if (!groups.length) return null;
  const detected = groups.reduce((n, g) => n + g.items.filter((p) => p.detected).length, 0);
  return (
    <Collapsible title="Tactical patterns" subtitle={`${detected} detected across ${groups.length === 1 ? "one team" : "both teams"}`} icon={Waypoints}>
      <div className={cn("grid gap-6", groups.length > 1 && "lg:grid-cols-2")}>
        {groups.map((g) => {
          // Detected patterns first, strongest first
          const items = [...g.items].sort((x, y) => Number(y.detected) - Number(x.detected) || num(y.confidence) - num(x.confidence));
          return (
            <div key={g.name} className="min-w-0">
              <div className="mb-2 flex items-center gap-2 font-medium text-text-primary"><span className="h-2.5 w-2.5 rounded-full" style={{ background: g.color }} />{g.name}</div>
              <StaggerGrid className="space-y-2">
                {items.map((p, i) => <StaggerItem key={i}><PatternCard p={p} color={g.color} /></StaggerItem>)}
              </StaggerGrid>
            </div>
          );
        })}
      </div>
    </Collapsible>
  );
}

function PatternCard({ p, color }: { p: PatternItem; color: string }) {
  return (
    <div className={cn("tile p-3.5", !p.detected && "opacity-60")}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2 font-medium text-text-primary">
          {p.detected ? <CheckCircle2 className="h-4 w-4 shrink-0 text-success" /> : <XCircle className="h-4 w-4 shrink-0 text-text-muted" />}
          <span className="truncate">{titleCase(p.name)}</span>
        </div>
        <span className="tabular shrink-0 text-sm text-text-muted">{fmtPct(p.confidence)}</span>
      </div>
      <div className="mt-2"><ConfidenceBar value={num(p.confidence) <= 1 ? num(p.confidence) : num(p.confidence) / 100} color={p.detected ? color : "var(--line-strong)"} /></div>
      {p.description && <p className="mt-2 text-sm text-text-secondary">{p.description}</p>}
      {p.involved_players?.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {p.involved_players.map((n) => <span key={n} className="chip border-line-strong text-text-secondary">{n}</span>)}
        </div>
      )}
    </div>
  );
}

// ── Roles ───────────────────────────────────────────────────────

export function RolesSection({ data, meta }: { data: RolesResponse; meta: TeamMeta }) {
  const groups = [
    { name: meta.teamAName, color: meta.teamAColor, items: data.team_a_roles ?? [] },
    { name: meta.teamBName, color: meta.teamBColor, items: data.team_b_roles ?? [] },
  ].filter((g) => g.items.length);
  if (!groups.length) return null;
  return (
    <Collapsible title="Player roles" subtitle="Rule-based sub-role for every player" icon={Users} defaultOpen={false}>
      <div className={cn("grid gap-6", groups.length > 1 && "lg:grid-cols-2")}>
        {groups.map((g) => (
          <div key={g.name} className="min-w-0">
            <div className="mb-2 flex items-center gap-2 font-medium text-text-primary"><span className="h-2.5 w-2.5 rounded-full" style={{ background: g.color }} />{g.name}</div>
            <ul className="divide-y divide-line border-y border-line">
              {g.items.map((r: PlayerRoleItem) => (
                <li key={`${r.number}-${r.name}`} className="flex items-center gap-3 py-2">
                  <span className="tabular w-7 shrink-0 text-center text-sm text-text-muted">{r.number}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate text-sm font-medium text-text-primary">{r.name} <span className="font-normal text-text-muted">{r.position}</span></span>
                      <span className="shrink-0 text-sm" style={{ color: g.color }}>{r.role}</span>
                    </div>
                    {r.reasoning && <div className="truncate text-xs text-text-muted" title={r.reasoning}>{r.reasoning}</div>}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Collapsible>
  );
}

// ── SWOT + recommendations ──────────────────────────────────────

const SWOT_META: Record<string, { label: string; color: string }> = {
  strengths: { label: "Strengths", color: "var(--success)" },
  weaknesses: { label: "Weaknesses", color: "var(--danger)" },
  opportunities: { label: "Opportunities", color: "var(--cyan)" },
  threats: { label: "Threats", color: "var(--warning)" },
};

export function SwotSection({ swot }: { swot: SWOTItem[] }) {
  if (!swot?.length) return null;
  const groups = Object.keys(SWOT_META).map((k) => ({ key: k, items: swot.filter((s) => s.category?.toLowerCase().startsWith(k.slice(0, -1))) })).filter((g) => g.items.length);
  return (
    <Collapsible title="SWOT" subtitle={`${swot.length} findings from the rule engine`} icon={Brain}>
      <div className="grid gap-x-8 gap-y-6 sm:grid-cols-2">
        {groups.map((g) => {
          const m = SWOT_META[g.key];
          return (
            <div key={g.key} className="border-l-2 pl-4" style={{ borderColor: m.color }}>
              <h4 className="mb-2 font-display text-lg font-semibold" style={{ color: m.color }}>{m.label}</h4>
              <ul className="space-y-2.5">
                {g.items.map((s, i) => (
                  <li key={i} className="text-sm text-text-primary">
                    {s.description}
                    {s.source && <div className="mt-0.5 text-xs text-text-muted">From {s.source}</div>}
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </Collapsible>
  );
}

const PRIORITY_COLOR: Record<string, string> = { high: "var(--danger)", medium: "var(--warning)", low: "var(--line-strong)" };

export function RecommendationsSection({ recs, insights }: { recs: RecommendationItem[]; insights?: string[] }) {
  if (!recs?.length && !insights?.length) return null;
  return (
    <Collapsible title="Recommendations" subtitle="Ordered by priority, each with its reasoning" icon={ListOrdered}>
      <StaggerGrid className="space-y-3">
        {(recs ?? []).map((r, i) => (
          <StaggerItem key={i}>
            <article className="tile border-l-2 p-4" style={{ borderLeftColor: PRIORITY_COLOR[r.priority?.toLowerCase()] ?? "var(--line-strong)" }}>
              <div className="flex flex-wrap items-center gap-2">
                <PriorityBadge priority={r.priority} />
                <span className="text-sm text-text-muted">{sentence(r.category ?? "")}</span>
              </div>
              <p className="mt-2 font-medium text-text-primary">{r.description}</p>
              {(r.reasoning || r.expected_impact) && (
                <dl className="mt-3 grid gap-x-4 gap-y-1.5 text-sm sm:grid-cols-[6rem_minmax(0,1fr)]">
                  {r.reasoning && <><dt className="text-text-muted">Why</dt><dd className="text-text-secondary">{r.reasoning}</dd></>}
                  {r.expected_impact && <><dt className="text-text-muted">Expected effect</dt><dd className="text-text-secondary">{r.expected_impact}</dd></>}
                </dl>
              )}
            </article>
          </StaggerItem>
        ))}
        {insights && insights.length > 0 && (
          <StaggerItem>
            <div className="border-l-2 border-section pl-4">
              <h4 className="mb-1.5 font-display text-lg font-semibold text-section">From the knowledge graph</h4>
              <ul className="space-y-1.5">
                {insights.map((s, i) => <li key={i} className="text-sm text-text-secondary">{s}</li>)}
              </ul>
            </div>
          </StaggerItem>
        )}
      </StaggerGrid>
    </Collapsible>
  );
}

export function IntelligenceSection({ data, meta }: { data: IntelligenceResponse; meta: TeamMeta }) {
  return (
    <>
      {(data.formation_a || data.situations?.length > 0) && (
        <div className="flex flex-wrap items-center gap-2">
          {data.formation_a && <span className="chip border-line-strong text-text-secondary"><span className="h-2 w-2 rounded-full" style={{ background: meta.teamAColor }} />{meta.teamAName} {data.formation_a}</span>}
          {data.formation_b && <span className="chip border-line-strong text-text-secondary"><span className="h-2 w-2 rounded-full" style={{ background: meta.teamBColor }} />{meta.teamBName} {data.formation_b}</span>}
          {(data.situations ?? []).map((s) => <span key={s} className="chip border-section/40 text-section">{sentence(s)}</span>)}
        </div>
      )}
      <RecommendationsSection recs={data.recommendations ?? []} insights={data.knowledge_graph_insights} />
      <SwotSection swot={data.swot ?? []} />
    </>
  );
}

// ── Explanation ─────────────────────────────────────────────────

/** Template reports come back as five paragraphs in a fixed order. */
const TEMPLATE_OUTLINE: Array<{ heading: string; parts: number[] }> = [
  { heading: "What is happening", parts: [0, 1] },
  { heading: "Why it matters", parts: [2] },
  { heading: "What should change", parts: [3, 4] },
];

export function ExplanationSection({ data, meta }: { data: ExplanationResponse; meta: TeamMeta }) {
  const s = data.summary ?? {};
  const hasSummary = Object.keys(s).length > 0;
  const paragraphs = data.sections?.length ? data.sections : [data.text];
  const hasHeadings = paragraphs.some((p) => /^#{1,3}\s/.test(p));

  let body: ReactNode;
  if (hasHeadings) {
    body = <Markdown text={paragraphs.join("\n\n")} className="font-serif text-lg leading-relaxed text-text-primary [&_h3]:font-sans" />;
  } else if (data.mode !== "llm" && paragraphs.length === 5) {
    body = TEMPLATE_OUTLINE.map((part) => (
      <Fragment key={part.heading}>
        <h3 className="font-display mt-8 text-2xl uppercase text-text-primary first:mt-0">{part.heading}</h3>
        {part.parts.map((i) => <p key={i} className="font-serif mt-3 text-lg leading-relaxed text-text-primary">{paragraphs[i]}</p>)}
      </Fragment>
    ));
  } else {
    body = paragraphs.map((p, i) => <p key={i} className="font-serif mt-3 text-lg leading-relaxed text-text-primary first:mt-0">{p}</p>);
  }

  return (
    <>
      {hasSummary && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatTile label={meta.teamAName} value={str(s.formation_a)} tone="teamA" hint="Detected shape" />
          <StatTile label={meta.teamBName} value={str(s.formation_b)} tone="teamB" hint="Detected shape" />
          <StatTile label="Territory" value={num(s.team_a_control)} suffix="%" decimals={1} tone="section" hint={`${meta.teamAName}'s share`} />
          <StatTile label="Press resistance" value={num(s.press_resistance_score)} tone="success" hint="Out of 100" />
        </div>
      )}
      <Collapsible
        title="Match report"
        subtitle={data.mode === "llm" ? "Written by the language model from the engine's numbers" : "Written by the template engine from the engine's numbers"}
        icon={FileText}
        badge={<span className="chip mr-2 border-line-strong text-text-secondary">{data.mode === "llm" ? "Language model" : "Template"}</span>}
      >
        <article className="max-w-[70ch]">{body}</article>
      </Collapsible>
    </>
  );
}

// ── Table helper ────────────────────────────────────────────────

export function DataTable({ columns, rows }: { columns: string[]; rows: string[][] }) {
  return (
    <div className="overflow-x-auto rounded-sm border border-line">
      <table className="w-full text-sm">
        <thead className="bg-surface-2 text-left text-text-muted">
          <tr>{columns.map((c) => <th key={c} className="px-3 py-2 font-medium">{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-line text-text-primary transition-colors hover:bg-surface-2">
              {r.map((cell, j) => <td key={j} className={cn("px-3 py-2", j > 1 && "tabular text-text-secondary")}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
