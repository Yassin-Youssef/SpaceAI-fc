import { motion } from "motion/react";
import {
  ArrowLeft, Download, FileText, Save, CheckCircle2, XCircle, RefreshCw, AlertTriangle, Film, Sparkles,
  type LucideIcon,
} from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { exportReport, downloadBlob, base64ToImageUrl, type ResolvedInput } from "../../lib/api";
import { saveAnalysis, isSupabaseConfigured } from "../../lib/supabase";
import type {
  FeatureApiResponse, AnalysisFormData, VisualizationData, FullAnalysisResponse, FormationResponse,
  SpaceControlResponse, PassNetworkResponse, PressResistanceResponse, PatternsResponse, RolesResponse,
  IntelligenceResponse, ExplanationResponse,
} from "../../lib/types";
import { Page, Button, ResultsSkeleton, EmptyState, StatTile } from "./common/Primitives";
import {
  VizGrid, FormationSection, SpaceControlSection, PassNetworkSection, PressResistanceSection,
  PatternsSection, RolesSection, IntelligenceSection, ExplanationSection, type TeamMeta,
} from "./results/Sections";

interface FeaturePageResultsProps {
  featureId: string;
  featureName: string;
  icon: LucideIcon;
  teamAName?: string;
  teamBName?: string;
  teamAColor?: string;
  teamBColor?: string;
  results: FeatureApiResponse | null;
  resolved?: ResolvedInput | null;
  error?: string | null;
  isLoading?: boolean;
  userId?: string;
  inputData?: AnalysisFormData;
  onBack: () => void;
  onRetry?: () => void;
  onSaved?: () => void;
}

export function FeaturePageResults({
  featureId,
  featureName,
  icon: Icon,
  teamAName = "Team A",
  teamBName = "Team B",
  teamAColor = "#00d9ff",
  teamBColor = "#ff5a6e",
  results,
  resolved,
  error,
  isLoading = false,
  userId,
  inputData,
  onBack,
  onRetry,
  onSaved,
}: FeaturePageResultsProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [exporting, setExporting] = useState<"docx" | "pdf" | null>(null);

  const meta: TeamMeta = { teamAName, teamBName, teamAColor, teamBColor };
  const visualizations = useMemo(() => collectVisualizations(results), [results]);
  const isVideo = inputData?.inputType === "video";
  const isSynthetic = isVideo && /synthetic/i.test(resolved?.note ?? "");
  const canSave = Boolean(userId) && isSupabaseConfigured();

  // ── Actions ─────────────────────────────────────────────────
  const handleSave = async () => {
    if (!userId || !results) return;
    setIsSaving(true);
    const { error: saveError } = await saveAnalysis(
      userId,
      `${teamAName} vs ${teamBName}`,
      featureName,
      stripFiles(inputData),
      results as unknown as Record<string, unknown>
    );
    setIsSaving(false);
    if (saveError) {
      toast.error("Could not save analysis", { description: saveError });
    } else {
      setSaved(true);
      toast.success("Saved to your history");
      onSaved?.();
    }
  };

  const handleExport = async (format: "docx" | "pdf") => {
    if (!results) return;
    setExporting(format);
    try {
      const blob = await exportReport(
        {
          analysis_data: results as unknown as Record<string, unknown>,
          match_info: inputData?.matchInfo as Record<string, unknown> | undefined,
          team_name: teamAName,
          opponent_name: teamBName,
          team_a_color: teamAColor,
          team_b_color: teamBColor,
          team_a: resolved?.teamA,
          team_b: resolved?.teamB,
          passes: resolved?.passes,
          ball_x: Number(inputData?.ballX) || 60,
          ball_y: Number(inputData?.ballY) || 40,
          feature: featureId,
        },
        format
      );
      downloadBlob(blob, `spaceaifc_${teamAName}_vs_${teamBName}.${format}`.replace(/\s+/g, "_"));
      toast.success(`${format.toUpperCase()} report downloaded`);
    } catch (err) {
      toast.error("Export failed", { description: err instanceof Error ? err.message : undefined });
    } finally {
      setExporting(null);
    }
  };

  const handleDownloadAll = () => {
    if (!visualizations.length) return;
    visualizations.forEach((viz, i) => {
      setTimeout(() => {
        const a = document.createElement("a");
        a.href = base64ToImageUrl(viz.image_base64);
        a.download = `${featureName}_${viz.title}.png`.replace(/\s+/g, "_");
        a.click();
      }, i * 250);
    });
    toast.success(`Downloading ${visualizations.length} image${visualizations.length > 1 ? "s" : ""}`);
  };

  // ── Render ──────────────────────────────────────────────────
  return (
    <Page>
      <div className="space-y-5">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <button type="button" onClick={onBack} className="rounded-lg border border-white/10 bg-white/5 p-2 text-text-secondary transition-colors hover:bg-white/10 hover:text-white" aria-label="Back to inputs">
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-[0_0_24px_rgba(0,217,255,0.35)]">
              <Icon className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="eyebrow">{featureName}</div>
              <h2 className="text-xl font-bold text-white sm:text-2xl">
                {teamAName}{needsOpponent(featureId, results) ? <span className="text-text-muted"> vs </span> : ""}{needsOpponent(featureId, results) ? teamBName : ""}
              </h2>
            </div>
          </div>
          <StatusChip loading={isLoading} error={error} />
        </motion.div>

        {inputData?.demoMatch && (
          <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} className="glass flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2.5 text-sm">
            <span className="font-semibold text-white">{inputData.demoMatch.title}</span>
            <span className="text-text-muted">{inputData.demoMatch.subtitle}</span>
            {(inputData.demoMatch.formationA || inputData.demoMatch.formationB) && (
              <span className="chip border-white/10 bg-white/5 text-text-secondary" title="Formations named in the official line-ups. The engine detects the average shape, which often differs.">
                Line-ups {inputData.demoMatch.formationA || "?"} v {inputData.demoMatch.formationB || "?"}
              </span>
            )}
            <span className={`chip ml-auto ${inputData.demoMatch.sourceKind === "statsbomb" ? "border-success/40 bg-success/10 text-success" : inputData.demoMatch.sourceKind === "sample" ? "border-white/10 bg-white/5 text-text-secondary" : "border-warning/40 bg-warning/10 text-warning"}`} title={inputData.demoMatch.note}>
              {inputData.demoMatch.sourceKind === "statsbomb" ? "StatsBomb open data" : inputData.demoMatch.sourceKind === "sample" ? "Sample data" : "Reconstructed line-ups"}
            </span>
          </motion.div>
        )}

        {isLoading && <ResultsSkeleton message={`Running ${featureName.toLowerCase()} on the tactical engine…`} />}

        {!isLoading && error && (
          <EmptyState
            icon={XCircle}
            title="Analysis failed"
            description={error}
            action={
              <div className="flex flex-wrap justify-center gap-2">
                {onRetry && <Button icon={RefreshCw} onClick={onRetry}>Try again</Button>}
                <Button variant="secondary" icon={ArrowLeft} onClick={onBack}>Edit inputs</Button>
              </div>
            }
          />
        )}

        {!isLoading && !error && !results && (
          <EmptyState icon={Sparkles} title="No results yet" description="Run an analysis to see visualisations and insights here." action={<Button icon={ArrowLeft} onClick={onBack}>Go to inputs</Button>} />
        )}

        {!isLoading && !error && results && (
          <>
            {isVideo && (
              <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} className={`flex items-start gap-3 rounded-xl border p-4 text-sm ${isSynthetic ? "border-warning/40 bg-warning/10 text-warning" : "border-brand/40 bg-brand/10 text-brand"}`}>
                {isSynthetic ? <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /> : <Film className="mt-0.5 h-4 w-4 shrink-0" />}
                <div>
                  <div className="font-semibold">{isSynthetic ? "Synthetic tracking snapshot" : "Positions extracted from video"}</div>
                  <div className="text-xs opacity-90">{resolved?.note ?? "Player positions were derived from the video pipeline."}</div>
                </div>
              </motion.div>
            )}

            <FeatureBody featureId={featureId} results={results} meta={meta} visualizations={visualizations} />

            {/* Action bar */}
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass flex flex-wrap items-center gap-2 p-3">
              <Button variant="secondary" icon={Download} onClick={handleDownloadAll} disabled={!visualizations.length}>
                PNG{visualizations.length > 1 ? ` (${visualizations.length})` : ""}
              </Button>
              <Button variant="secondary" icon={FileText} loading={exporting === "docx"} onClick={() => handleExport("docx")}>Word report</Button>
              <Button variant="secondary" icon={FileText} loading={exporting === "pdf"} onClick={() => handleExport("pdf")}>PDF summary</Button>
              <div className="flex-1" />
              {onRetry && <Button variant="ghost" icon={RefreshCw} onClick={onRetry}>Re-run</Button>}
              {canSave ? (
                <Button icon={saved ? CheckCircle2 : Save} loading={isSaving} disabled={saved} onClick={handleSave}>
                  {saved ? "Saved" : "Save to history"}
                </Button>
              ) : (
                <span className="text-xs text-text-muted">Sign in with Supabase configured to save history</span>
              )}
            </motion.div>
          </>
        )}
      </div>
    </Page>
  );
}

// ── Feature bodies ──────────────────────────────────────────────

function FeatureBody({ featureId, results, meta, visualizations }: { featureId: string; results: FeatureApiResponse; meta: TeamMeta; visualizations: VisualizationData[] }) {
  const r = results as unknown;
  switch (featureId) {
    case "full-match": {
      const d = r as FullAnalysisResponse;
      const fm = d.formation, sc = d.space_control, pr = d.press_resistance, pn = d.pass_network;
      return (
        <div className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile label={meta.teamAName} value={fm?.team_a_formation ?? "–"} tone="teamA" hint="Formation" />
            <StatTile label={meta.teamBName} value={fm?.team_b_formation ?? "–"} tone="teamB" hint="Formation" />
            <StatTile label="Territory" value={sc?.team_a_control ?? 0} suffix="%" decimals={1} tone="brand" hint={`${meta.teamAName} control`} />
            <StatTile label="Press resistance" value={pr?.press_resistance_score ?? 0} tone="success" hint={`${pn?.total_passes ?? 0} passes analysed`} />
          </div>
          <VizGrid visualizations={visualizations} title="All visualisations" />
          {fm && <FormationSection data={fm} meta={meta} />}
          {sc && <SpaceControlSection data={sc} meta={meta} />}
          {pn && <PassNetworkSection data={{ ...pn, visualizations: [] }} meta={meta} />}
          {pr && <PressResistanceSection data={pr} meta={meta} />}
          {d.patterns && <PatternsSection data={d.patterns} meta={meta} />}
          {d.roles && <RolesSection data={d.roles} meta={meta} />}
          {d.intelligence && <IntelligenceSection data={d.intelligence} meta={meta} />}
          {d.explanation && <ExplanationSection data={{ ...d.explanation, summary: {} }} meta={meta} />}
        </div>
      );
    }
    case "pass-network":
      return (
        <div className="space-y-5">
          <PassNetworkSection data={r as PassNetworkResponse} meta={meta} />
          <VizGrid visualizations={visualizations} />
        </div>
      );
    case "space-control":
      return (
        <div className="space-y-5">
          <SpaceControlSection data={r as SpaceControlResponse} meta={meta} />
          <VizGrid visualizations={visualizations} />
        </div>
      );
    case "formation":
      return (
        <div className="space-y-5">
          <FormationSection data={r as FormationResponse} meta={meta} />
          <VizGrid visualizations={visualizations} />
        </div>
      );
    case "press-resistance":
      return (
        <div className="space-y-5">
          <PressResistanceSection data={r as PressResistanceResponse} meta={meta} />
          <VizGrid visualizations={visualizations} />
        </div>
      );
    case "patterns":
      return (
        <div className="space-y-5">
          <PatternsSection data={r as PatternsResponse} meta={meta} />
          <VizGrid visualizations={visualizations} />
        </div>
      );
    case "roles":
      return (
        <div className="space-y-5">
          <RolesSection data={r as RolesResponse} meta={meta} />
          <VizGrid visualizations={visualizations} />
        </div>
      );
    case "strategy":
      return (
        <div className="space-y-5">
          <IntelligenceSection data={r as IntelligenceResponse} meta={meta} />
          <VizGrid visualizations={visualizations} title="Supporting analysis" defaultOpen={false} />
        </div>
      );
    case "explanation":
      return (
        <div className="space-y-5">
          <ExplanationSection data={r as ExplanationResponse} meta={meta} />
          <VizGrid visualizations={visualizations} title="Supporting analysis" defaultOpen={false} />
        </div>
      );
    default:
      return <VizGrid visualizations={visualizations} />;
  }
}

// ── Helpers ─────────────────────────────────────────────────────

function StatusChip({ loading, error }: { loading: boolean; error?: string | null }) {
  if (loading) return <span className="chip border-brand/40 bg-brand/10 text-brand"><span className="h-2 w-2 animate-pulse rounded-full bg-brand" /> Analysing</span>;
  if (error) return <span className="chip border-danger/40 bg-danger/10 text-danger"><XCircle className="h-3.5 w-3.5" /> Failed</span>;
  return <span className="chip border-success/40 bg-success/10 text-success"><CheckCircle2 className="h-3.5 w-3.5" /> Complete</span>;
}

function needsOpponent(featureId: string, results: FeatureApiResponse | null): boolean {
  if (["pass-network", "formation"].includes(featureId)) {
    const r = results as { team_b_formation?: unknown } | null;
    return Boolean(r?.team_b_formation);
  }
  return true;
}

/** Gather every visualisation in a (possibly nested) response, de-duplicated. */
function collectVisualizations(results: FeatureApiResponse | null): VisualizationData[] {
  if (!results) return [];
  const out: VisualizationData[] = [];
  const seen = new Set<string>();
  const push = (v: VisualizationData) => {
    // PNG headers are identical, so key on the full payload rather than a prefix
    const key = v.image_base64 ? `${v.image_base64.length}:${v.image_base64.slice(-120)}` : "";
    if (!key || seen.has(key)) return;
    seen.add(key);
    out.push(v);
  };
  (results.visualizations ?? []).forEach(push);
  for (const value of Object.values(results)) {
    if (value && typeof value === "object" && Array.isArray((value as { visualizations?: unknown }).visualizations)) {
      ((value as { visualizations: VisualizationData[] }).visualizations).forEach(push);
    }
  }
  return out;
}

function stripFiles(data?: AnalysisFormData): Record<string, unknown> {
  if (!data) return {};
  const { videoFile, datasetFile, ...rest } = data;
  return { ...rest, videoFileName: videoFile?.name, datasetFileName: datasetFile?.name };
}
