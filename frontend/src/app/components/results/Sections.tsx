/**
 * Feature-specific result renderers.  Every block is defensive about the
 * shape of the data it receives so a partial backend response still renders.
 */
import { motion } from "motion/react";
import {
  Download, Image as ImageIcon, Shield, Map, Share2, Zap, Grid3x3, Users, Lightbulb,
  FileText, Brain, CheckCircle2, XCircle, TrendingUp, AlertTriangle, Target, Sparkles,
} from "lucide-react";
import { useState } from "react";
import { base64ToImageUrl } from "../../../lib/api";
import type {
  VisualizationData, FormationResponse, SpaceControlResponse, PassNetworkResponse,
  PressResistanceResponse, PatternsResponse, RolesResponse, IntelligenceResponse,
  ExplanationResponse, SWOTItem, RecommendationItem, PatternItem, PlayerRoleItem,
} from "../../../lib/types";
import { AnimatedNumber } from "../common/AnimatedNumber";
import { Collapsible, StatTile, StaggerGrid, StaggerItem, PriorityBadge, ConfidenceBar } from "../common/Primitives";
import { cn } from "../ui/utils";

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

// ── Visualisations ──────────────────────────────────────────────

export function VizGrid({ visualizations, title = "Visualisations", defaultOpen = true }: { visualizations: VisualizationData[]; title?: string; defaultOpen?: boolean }) {
  if (!visualizations?.length) return null;
  return (
    <Collapsible title={title} subtitle={`${visualizations.length} rendered by the engine`} icon={ImageIcon} defaultOpen={defaultOpen}>
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
  const [open, setOpen] = useState(false);
  const src = base64ToImageUrl(viz.image_base64);
  const download = () => {
    const a = document.createElement("a");
    a.href = src;
    a.download = `${viz.title.replace(/\s+/g, "_")}.png`;
    a.click();
  };
  return (
    <div className="glass overflow-hidden p-3">
      <div className="mb-2 flex items-center justify-between gap-2 px-1">
        <h4 className="truncate text-sm font-semibold text-white">{viz.title}</h4>
        <button type="button" onClick={download} className="rounded-lg p-1.5 text-text-muted transition-colors hover:bg-white/10 hover:text-brand" aria-label={`Download ${viz.title}`}>
          <Download className="h-4 w-4" />
        </button>
      </div>
      {viz.description && <p className="mb-2 px-1 text-xs text-text-muted">{viz.description}</p>}
      <div className="relative overflow-hidden rounded-lg bg-black/30">
        {!loaded && <div className="absolute inset-0 animate-pulse bg-white/5" />}
        <motion.img
          src={src}
          alt={viz.title}
          onLoad={() => setLoaded(true)}
          onClick={() => setOpen(true)}
          initial={{ opacity: 0 }}
          animate={{ opacity: loaded ? 1 : 0 }}
          transition={{ duration: 0.4 }}
          className="block w-full cursor-zoom-in object-contain"
          style={{ maxHeight: 360 }}
          loading="lazy"
        />
      </div>
      {open && (
        <div className="fixed inset-0 z-[60] flex cursor-zoom-out items-center justify-center bg-black/85 p-4 backdrop-blur-sm" onClick={() => setOpen(false)} role="dialog" aria-label={viz.title}>
          <motion.img initial={{ scale: 0.92, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} src={src} alt={viz.title} className="max-h-full max-w-full rounded-lg shadow-2xl" />
        </div>
      )}
    </div>
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
    <Collapsible title="Detected formations" subtitle="Clustering on player depth, with confidence" icon={Shield}>
      <StaggerGrid className={cn("grid gap-4", teams.length > 1 && "sm:grid-cols-2")}>
        {teams.map((t) => (
          <StaggerItem key={t.name}>
            <div className="glass relative overflow-hidden p-5">
              <div className="absolute inset-x-0 top-0 h-1" style={{ background: t.color }} />
              <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-text-muted">{t.name}</div>
              <div className="text-4xl font-black tracking-tight text-white sm:text-5xl" style={{ color: t.color }}>{t.formation}</div>
              <div className="mt-3">
                <div className="mb-1 flex justify-between text-xs text-text-secondary"><span>Confidence</span><span>{fmtPct(t.conf)}</span></div>
                <ConfidenceBar value={num(t.conf) <= 1 ? num(t.conf) : num(t.conf) / 100} color={t.color} />
              </div>
              {t.method && <div className="mt-2 text-xs text-text-muted">Method: {titleCase(String(t.method))}</div>}
            </div>
          </StaggerItem>
        ))}
      </StaggerGrid>
    </Collapsible>
  );
}

// ── Space control ───────────────────────────────────────────────

export function SpaceControlSection({ data, meta }: { data: SpaceControlResponse; meta: TeamMeta }) {
  const zones = Object.entries(data.zones ?? {});
  const mid = data.midfield_control ?? {};
  return (
    <Collapsible title="Territorial control" subtitle="Voronoi share of the pitch by zone" icon={Map}>
      <div className="grid gap-4 sm:grid-cols-3">
        <StatTile label={`${meta.teamAName} control`} value={num(data.team_a_control)} suffix="%" decimals={1} tone="teamA" />
        <StatTile label={`${meta.teamBName} control`} value={num(data.team_b_control)} suffix="%" decimals={1} tone="teamB" />
        <StatTile label="Midfield" value={num(mid.team_a)} suffix="%" decimals={1} tone="brand" hint={`${meta.teamAName} share of the middle third`} />
      </div>
      {zones.length > 0 && (
        <div className="mt-5 space-y-3">
          {zones.map(([zone, z], i) => (
            <DualBar key={zone} label={titleCase(zone)} a={num(z?.team_a)} b={num(z?.team_b)} meta={meta} delay={i * 0.08} />
          ))}
        </div>
      )}
    </Collapsible>
  );
}

function DualBar({ label, a, b, meta, delay = 0 }: { label: string; a: number; b: number; meta: TeamMeta; delay?: number }) {
  const total = a + b || 1;
  const pa = (a / total) * 100;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="font-medium text-text-secondary">{label}</span>
        <span className="tabular-nums text-text-muted"><span style={{ color: meta.teamAColor }}>{a.toFixed(0)}%</span> · <span style={{ color: meta.teamBColor }}>{b.toFixed(0)}%</span></span>
      </div>
      <div className="flex h-2.5 overflow-hidden rounded-full bg-white/5">
        <motion.div initial={{ width: 0 }} animate={{ width: `${pa}%` }} transition={{ duration: 0.8, delay, ease: [0.22, 1, 0.36, 1] }} style={{ background: meta.teamAColor }} />
        <motion.div initial={{ width: 0 }} animate={{ width: `${100 - pa}%` }} transition={{ duration: 0.8, delay, ease: [0.22, 1, 0.36, 1] }} style={{ background: meta.teamBColor }} />
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
      <div className="grid gap-4 sm:grid-cols-3">
        <StatTile label="Total passes" value={num(data.total_passes)} tone="brand" />
        <div className="glass p-4">
          <div className="mb-1 text-xs font-medium uppercase tracking-wider text-text-muted">Key distributor</div>
          <div className="truncate text-xl font-black text-white">{str(kd.name)} <span className="text-sm font-semibold text-text-muted">#{str(kd.number, "")}</span></div>
          <div className="text-xs text-text-secondary">Betweenness {num(kd.betweenness).toFixed(3)}</div>
        </div>
        <div className="glass p-4">
          <div className="mb-1 text-xs font-medium uppercase tracking-wider text-text-muted">Most involved</div>
          <div className="truncate text-xl font-black text-white">{str(mi.name)} <span className="text-sm font-semibold text-text-muted">#{str(mi.number, "")}</span></div>
          <div className="text-xs text-text-secondary">{num(mi.passes_made)} made · {num(mi.passes_received)} received</div>
        </div>
      </div>

      <Collapsible title="Connections" subtitle={`${meta.teamAName} strongest links and weak spots`} icon={Share2}>
        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-text-muted">Top connections</h4>
            <StaggerGrid className="space-y-2">
              {(data.top_connections ?? []).map((c, i) => (
                <StaggerItem key={i}>
                  <div className="flex items-center justify-between rounded-lg bg-white/[0.04] px-3 py-2 text-sm">
                    <span className="text-white">{str(c.from)} <span className="text-text-muted">→</span> {str(c.to)}</span>
                    <span className="font-bold tabular-nums text-brand">{num(c.passes)}</span>
                  </div>
                </StaggerItem>
              ))}
              {!(data.top_connections ?? []).length && <p className="text-sm text-text-muted">No repeated connections yet.</p>}
            </StaggerGrid>
          </div>
          <div>
            <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-text-muted">Weak links</h4>
            {(data.weak_links ?? []).length ? (
              <StaggerGrid className="space-y-2">
                {(data.weak_links ?? []).map((w, i) => (
                  <StaggerItem key={i}>
                    <div className="flex items-center justify-between rounded-lg border border-warning/30 bg-warning/10 px-3 py-2 text-sm">
                      <span className="text-white">{str(w.name)} <span className="text-text-muted">#{str(w.number, "")}</span></span>
                      <span className="text-xs text-warning">{num(w.total_involvement)} involvements</span>
                    </div>
                  </StaggerItem>
                ))}
              </StaggerGrid>
            ) : (
              <p className="flex items-center gap-2 text-sm text-success"><CheckCircle2 className="h-4 w-4" /> Every outfield player is involved in build-up.</p>
            )}
          </div>
        </div>
      </Collapsible>

      {centrality.length > 0 && (
        <Collapsible title="Centrality metrics" subtitle="Who the network runs through" icon={TrendingUp} defaultOpen={false}>
          <DataTable
            columns={["Player", "#", "Degree", "Betweenness", "Eigenvector"]}
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
  const verdict = score >= 70 ? "Comfortable under pressure" : score >= 45 ? "Holding up, with risk" : "Struggling to play out";
  return (
    <>
      <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
        <div className="glass flex flex-col items-center justify-center p-5">
          <Gauge value={score} color={tone} />
          <div className="mt-2 text-sm font-semibold text-white">{verdict}</div>
          <div className="text-xs text-text-muted">{meta.teamAName} press resistance</div>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <StatTile label="Passes analysed" value={num(data.total_passes)} tone="neutral" />
          <StatTile label="Under pressure" value={num(data.passes_under_pressure)} tone="warning" />
          <StatTile label="Success overall" value={num(data.pass_success_overall) * 100} suffix="%" tone="brand" />
          <StatTile label="Success under press" value={num(data.pass_success_under_pressure) * 100} suffix="%" tone="brand" />
          <StatTile label="Escape rate" value={num(data.escape_rate) * 100} suffix="%" tone="success" hint="Forward passes that beat the press" className="sm:col-span-2" />
        </div>
      </div>
      <Collapsible title="Vulnerable zones" subtitle="Where passes break down under pressure" icon={Zap}>
        {(data.vulnerable_zones ?? []).length ? (
          <StaggerGrid className="grid gap-3 sm:grid-cols-2">
            {(data.vulnerable_zones ?? []).map((z, i) => (
              <StaggerItem key={i}>
                <div className="rounded-lg border border-danger/30 bg-danger/10 p-3">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">{str(z.zone)}</span>
                    <span className="text-sm font-bold text-danger">{fmtPct(z.success_rate)}</span>
                  </div>
                  <div className="text-xs text-text-secondary">{num(z.total_passes)} passes attempted here</div>
                </div>
              </StaggerItem>
            ))}
          </StaggerGrid>
        ) : (
          <p className="flex items-center gap-2 text-sm text-success"><CheckCircle2 className="h-4 w-4" /> No zone shows a dangerous drop-off in pass success.</p>
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
        <circle cx="64" cy="64" r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="10" fill="none" />
        <motion.circle
          cx="64" cy="64" r={r} stroke={color} strokeWidth="10" fill="none" strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - pct) }}
          transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-black text-white"><AnimatedNumber value={value} /></span>
        <span className="text-[10px] uppercase tracking-widest text-text-muted">/ 100</span>
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
    <Collapsible title="Tactical patterns" subtitle={`${detected} detected across ${groups.length} team${groups.length > 1 ? "s" : ""}`} icon={Grid3x3}>
      <div className={cn("grid gap-5", groups.length > 1 && "lg:grid-cols-2")}>
        {groups.map((g) => (
          <div key={g.name}>
            <div className="mb-2 flex items-center gap-2 text-sm font-bold text-white"><span className="h-2.5 w-2.5 rounded-full" style={{ background: g.color }} />{g.name}</div>
            <StaggerGrid className="space-y-2">
              {g.items.map((p, i) => <StaggerItem key={i}><PatternCard p={p} color={g.color} /></StaggerItem>)}
            </StaggerGrid>
          </div>
        ))}
      </div>
    </Collapsible>
  );
}

function PatternCard({ p, color }: { p: PatternItem; color: string }) {
  return (
    <div className={cn("rounded-lg border p-3", p.detected ? "border-white/15 bg-white/[0.05]" : "border-white/5 bg-white/[0.02] opacity-70")}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          {p.detected ? <CheckCircle2 className="h-4 w-4 text-success" /> : <XCircle className="h-4 w-4 text-text-muted" />}
          {titleCase(p.name)}
        </div>
        <span className="text-xs tabular-nums text-text-muted">{fmtPct(p.confidence)}</span>
      </div>
      {p.description && <p className="mt-1 text-xs leading-relaxed text-text-secondary">{p.description}</p>}
      {p.involved_players?.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {p.involved_players.map((n) => <span key={n} className="chip border-white/10 bg-white/5 text-[11px] text-text-secondary" style={{ borderColor: `${color}55` }}>{n}</span>)}
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
    <Collapsible title="Player roles" subtitle="Rule-based sub-role classification" icon={Users} defaultOpen={false}>
      <div className={cn("grid gap-5", groups.length > 1 && "lg:grid-cols-2")}>
        {groups.map((g) => (
          <div key={g.name}>
            <div className="mb-2 flex items-center gap-2 text-sm font-bold text-white"><span className="h-2.5 w-2.5 rounded-full" style={{ background: g.color }} />{g.name}</div>
            <div className="space-y-1.5">
              {g.items.map((r: PlayerRoleItem) => (
                <div key={`${r.number}-${r.name}`} className="flex items-center gap-3 rounded-lg bg-white/[0.04] px-3 py-2">
                  <span className="w-7 text-center text-xs font-bold tabular-nums text-text-muted">{r.number}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate text-sm font-semibold text-white">{r.name} <span className="text-xs font-normal text-text-muted">{r.position}</span></span>
                      <span className="shrink-0 text-xs font-semibold" style={{ color: g.color }}>{r.role}</span>
                    </div>
                    {r.reasoning && <div className="truncate text-[11px] text-text-muted" title={r.reasoning}>{r.reasoning}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Collapsible>
  );
}

// ── SWOT + recommendations ──────────────────────────────────────

const SWOT_META: Record<string, { label: string; icon: typeof Shield; cls: string }> = {
  strengths: { label: "Strengths", icon: CheckCircle2, cls: "border-success/30 bg-success/10 text-success" },
  weaknesses: { label: "Weaknesses", icon: AlertTriangle, cls: "border-danger/30 bg-danger/10 text-danger" },
  opportunities: { label: "Opportunities", icon: Target, cls: "border-brand/30 bg-brand/10 text-brand" },
  threats: { label: "Threats", icon: XCircle, cls: "border-warning/30 bg-warning/10 text-warning" },
};

export function SwotSection({ swot }: { swot: SWOTItem[] }) {
  if (!swot?.length) return null;
  const groups = Object.keys(SWOT_META).map((k) => ({ key: k, items: swot.filter((s) => s.category?.toLowerCase().startsWith(k.slice(0, -1))) })).filter((g) => g.items.length);
  return (
    <Collapsible title="SWOT reasoning" subtitle={`${swot.length} insights from the rule engine`} icon={Brain}>
      <StaggerGrid className="grid gap-4 sm:grid-cols-2">
        {groups.map((g) => {
          const m = SWOT_META[g.key];
          return (
            <StaggerItem key={g.key}>
              <div className={cn("h-full rounded-xl border p-4", m.cls)}>
                <div className="mb-2 flex items-center gap-2 text-sm font-bold"><m.icon className="h-4 w-4" />{m.label}</div>
                <ul className="space-y-2">
                  {g.items.map((s, i) => (
                    <li key={i} className="text-sm leading-relaxed text-white/90">
                      {s.description}
                      {s.source && <div className="mt-0.5 text-xs text-white/55">→ {s.source}</div>}
                    </li>
                  ))}
                </ul>
              </div>
            </StaggerItem>
          );
        })}
      </StaggerGrid>
    </Collapsible>
  );
}

export function RecommendationsSection({ recs, insights }: { recs: RecommendationItem[]; insights?: string[] }) {
  if (!recs?.length && !insights?.length) return null;
  return (
    <Collapsible title="Strategy recommendations" subtitle="Prioritised actions with reasoning" icon={Lightbulb}>
      <StaggerGrid className="space-y-3">
        {(recs ?? []).map((r, i) => (
          <StaggerItem key={i}>
            <div className="glass p-4">
              <div className="flex flex-wrap items-center gap-2">
                <PriorityBadge priority={r.priority} />
                <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">{r.category}</span>
              </div>
              <p className="mt-2 text-sm font-semibold text-white">{r.description}</p>
              {r.reasoning && <p className="mt-1 text-sm text-text-secondary"><span className="text-text-muted">Why:</span> {r.reasoning}</p>}
              {r.expected_impact && <p className="mt-1 text-sm text-text-secondary"><span className="text-text-muted">Impact:</span> {r.expected_impact}</p>}
            </div>
          </StaggerItem>
        ))}
        {insights && insights.length > 0 && (
          <StaggerItem>
            <div className="rounded-xl border border-violet/40 bg-violet/10 p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-bold text-white"><Sparkles className="h-4 w-4 text-violet" /> Knowledge graph</div>
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
          {data.formation_a && <span className="chip border-white/10 bg-white/5 text-text-secondary"><span className="h-2 w-2 rounded-full" style={{ background: meta.teamAColor }} />{meta.teamAName} {data.formation_a}</span>}
          {data.formation_b && <span className="chip border-white/10 bg-white/5 text-text-secondary"><span className="h-2 w-2 rounded-full" style={{ background: meta.teamBColor }} />{meta.teamBName} {data.formation_b}</span>}
          {(data.situations ?? []).map((s) => <span key={s} className="chip border-violet/40 bg-violet/15 text-violet">{titleCase(s)}</span>)}
        </div>
      )}
      <RecommendationsSection recs={data.recommendations ?? []} insights={data.knowledge_graph_insights} />
      <SwotSection swot={data.swot ?? []} />
    </>
  );
}

// ── Explanation ─────────────────────────────────────────────────

export function ExplanationSection({ data, meta }: { data: ExplanationResponse; meta: TeamMeta }) {
  const s = data.summary ?? {};
  const hasSummary = Object.keys(s).length > 0;
  return (
    <>
      {hasSummary && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatTile label={`${meta.teamAName}`} value={str(s.formation_a)} tone="teamA" hint="Formation" />
          <StatTile label={`${meta.teamBName}`} value={str(s.formation_b)} tone="teamB" hint="Formation" />
          <StatTile label="Territory" value={num(s.team_a_control)} suffix="%" decimals={1} tone="brand" hint={`${meta.teamAName} control`} />
          <StatTile label="Press resistance" value={num(s.press_resistance_score)} tone="success" hint="Score out of 100" />
        </div>
      )}
      <Collapsible title="Match report" subtitle={data.mode === "llm" ? "Written by the language model" : "Generated by the template engine"} icon={FileText}
        badge={<span className={cn("chip mr-2", data.mode === "llm" ? "border-violet/40 bg-violet/15 text-violet" : "border-white/10 bg-white/5 text-text-secondary")}>{data.mode === "llm" ? "AI" : "Template"}</span>}>
        <StaggerGrid className="space-y-4" stagger={0.1}>
          {(data.sections?.length ? data.sections : [data.text]).map((p, i) => (
            <StaggerItem key={i}>
              <p className="text-[15px] leading-7 text-white/90 first-letter:text-lg first-letter:font-bold first-letter:text-brand">{p}</p>
            </StaggerItem>
          ))}
        </StaggerGrid>
      </Collapsible>
    </>
  );
}

// ── Table helper ────────────────────────────────────────────────

export function DataTable({ columns, rows }: { columns: string[]; rows: string[][] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-white/10">
      <table className="w-full text-sm">
        <thead className="bg-white/[0.04] text-left text-xs uppercase tracking-wider text-text-muted">
          <tr>{columns.map((c) => <th key={c} className="px-3 py-2 font-semibold">{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-white/5 text-white/90 hover:bg-white/[0.03]">
              {r.map((cell, j) => <td key={j} className={cn("px-3 py-2", j > 1 && "tabular-nums text-text-secondary")}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
