import {
  ArrowLeft, Download, FileText, Save, CheckCircle2, XCircle, RefreshCw, AlertTriangle, Film,
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
import { Page, Button, ResultsSkeleton, EmptyState, StatTile, ResultsHeader, LoadSwap, Band, type SkeletonVariant } from "./common/Primitives";
import { FEATURE_BY_ID, SECTION_LABEL } from "../../lib/features";
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
  teamAName = "Team A",
  teamBName = "Team B",
  teamAColor = "#0d0d0d",
  teamBColor = "#e1061f",
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
  const showOpponent = needsOpponent(featureId, results);
  return (
    <Page>
      <ResultsHeader
        context={SECTION_LABEL[FEATURE_BY_ID[featureId]?.section ?? "analysis"]}
        title={featureName}
        onBack={onBack}
        right={<StatusChip loading={isLoading} error={error} />}
      />

      {/* Broadcast band: who is playing, and for Full Match the headline numbers */}
      <Band className="mt-6 py-7">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <TeamName name={teamAName} color={teamAColor} />
          {showOpponent && <>
            <span className="font-num text-3xl text-text-muted">v</span>
            <TeamName name={teamBName} color={teamBColor} />
          </>}
        </div>
        {inputData?.demoMatch && (
          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 text-sm">
            <span className="font-semibold text-text-primary">{inputData.demoMatch.title}</span>
            <span className="text-text-muted">{inputData.demoMatch.subtitle}</span>
            {(inputData.demoMatch.formationA || inputData.demoMatch.formationB) && (
              <span className="chip border-line-strong text-text-secondary" title="Formations named in the official line-ups. The engine detects the average shape, which often differs.">
                Named line-ups {inputData.demoMatch.formationA || "?"} v {inputData.demoMatch.formationB || "?"}
              </span>
            )}
            <span
              className={`chip ${inputData.demoMatch.sourceKind === "statsbomb" ? "border-success/60 text-success" : inputData.demoMatch.sourceKind === "sample" ? "border-line-strong text-text-secondary" : "border-warning/60 text-warning"}`}
              title={inputData.demoMatch.note}
            >
              {inputData.demoMatch.sourceKind === "statsbomb" ? "StatsBomb open data" : inputData.demoMatch.sourceKind === "sample" ? "Built-in sample" : "Reconstructed line-ups"}
            </span>
          </div>
        )}
        {featureId === "full-match" && results && !isLoading && !error && <HeadlineNumbers results={results} meta={meta} />}
      </Band>

      <div className="mt-6">
        <LoadSwap loading={isLoading} skeleton={<ResultsSkeleton variant={SKELETON[featureId] ?? "overview"} message={`Running ${featureName.toLowerCase()}…`} />}>
          {error ? (
            <EmptyState
              icon={XCircle}
              title="The analysis did not finish"
              description={error}
              action={
                <div className="flex flex-wrap gap-2">
                  {onRetry && <Button icon={RefreshCw} onClick={onRetry}>Try again</Button>}
                  <Button variant="secondary" icon={ArrowLeft} onClick={onBack}>Edit inputs</Button>
                </div>
              }
            />
          ) : !results ? (
            <EmptyState icon={FileText} title="No results yet" description="Go back to the inputs, load a demo fixture or enter positions, and run the analysis." action={<Button icon={ArrowLeft} onClick={onBack}>Go to inputs</Button>} />
          ) : (
            <div className="space-y-5">
              {isVideo && (
                <div className={`flex items-start gap-3 rounded-md border p-4 text-sm ${isSynthetic ? "border-warning/50 bg-warning/5" : "border-line-strong bg-surface-1"}`}>
                  {isSynthetic ? <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" /> : <Film className="mt-0.5 h-4 w-4 shrink-0 text-section" />}
                  <div>
                    <div className={`font-medium ${isSynthetic ? "text-warning" : "text-text-primary"}`}>{isSynthetic ? "Synthetic tracking snapshot" : "Positions extracted from video"}</div>
                    <div className="text-text-secondary">{resolved?.note ?? "Player positions were derived from the video pipeline."}</div>
                  </div>
                </div>
              )}

              <FeatureBody featureId={featureId} results={results} meta={meta} visualizations={visualizations} />

              {/* Action bar */}
              <div className="flex flex-wrap items-center gap-2 border-t border-line pt-5">
                <Button variant="secondary" icon={Download} onClick={handleDownloadAll} disabled={!visualizations.length}>
                  {visualizations.length > 1 ? `Images (${visualizations.length})` : "Image"}
                </Button>
                <Button variant="secondary" icon={FileText} loading={exporting === "docx"} onClick={() => handleExport("docx")}>Word report</Button>
                <Button variant="secondary" icon={FileText} loading={exporting === "pdf"} onClick={() => handleExport("pdf")}>PDF summary</Button>
                <div className="hidden flex-1 sm:block" />
                {onRetry && <Button variant="ghost" icon={RefreshCw} onClick={onRetry}>Run again</Button>}
                {canSave ? (
                  <Button icon={saved ? CheckCircle2 : Save} loading={isSaving} disabled={saved} onClick={handleSave}>
                    {saved ? "Saved" : "Save to history"}
                  </Button>
                ) : (
                  <span className="text-sm text-text-muted">Sign in to save analyses to your history</span>
                )}
              </div>
            </div>
          )}
        </LoadSwap>
      </div>
    </Page>
  );
}

const SKELETON: Record<string, SkeletonVariant> = {
  "full-match": "overview",
  "pass-network": "network",
  "space-control": "space",
  formation: "formation",
  "press-resistance": "press",
  patterns: "patterns",
  strategy: "strategy",
  explanation: "report",
};

// ── Feature bodies ──────────────────────────────────────────────

function FeatureBody({ featureId, results, meta, visualizations }: { featureId: string; results: FeatureApiResponse; meta: TeamMeta; visualizations: VisualizationData[] }) {
  const r = results as unknown;
  switch (featureId) {
    case "full-match": {
      const d = r as FullAnalysisResponse;
      const fm = d.formation, sc = d.space_control, pr = d.press_resistance, pn = d.pass_network;
      return (
        <div className="space-y-5">
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

function TeamName({ name, color }: { name: string; color: string }) {
  return (
    <span className="flex min-w-0 items-center gap-3">
      <span className="h-8 w-2 shrink-0 sm:h-10" style={{ background: color === "#0d0d0d" ? "#ffffff" : color }} />
      <span className="font-display truncate text-3xl uppercase text-text-primary sm:text-5xl">{name}</span>
    </span>
  );
}

function HeadlineNumbers({ results, meta }: { results: FeatureApiResponse; meta: TeamMeta }) {
  const d = results as unknown as FullAnalysisResponse;
  const fm = d.formation, sc = d.space_control, pr = d.press_resistance, pn = d.pass_network;
  return (
    <div className="mt-6 grid grid-cols-2 gap-px bg-line lg:grid-cols-4">
      <StatTile className="border-0" label={`${meta.teamAName} shape`} value={fm?.team_a_formation ?? "–"} tone="neutral" />
      <StatTile className="border-0" label={`${meta.teamBName} shape`} value={fm?.team_b_formation ?? "–"} tone="neutral" />
      <StatTile className="border-0" label={`${meta.teamAName} territory`} value={sc?.team_a_control ?? 0} suffix="%" decimals={1} tone="section" />
      <StatTile className="border-0" label="Press resistance" value={pr?.press_resistance_score ?? 0} tone="section" hint={`${pn?.total_passes ?? 0} passes analysed`} />
    </div>
  );
}

function StatusChip({ loading, error }: { loading: boolean; error?: string | null }) {
  if (loading) return <span className="chip border-section/50 text-section">Analysing</span>;
  if (error) return <span className="chip border-danger/50 text-danger"><XCircle className="h-3.5 w-3.5" /> Failed</span>;
  return <span className="chip border-success/50 text-success"><CheckCircle2 className="h-3.5 w-3.5" /> Complete</span>;
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
