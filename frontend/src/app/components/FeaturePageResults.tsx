import { motion, AnimatePresence } from "motion/react";
import { Download, FileText, Save, CheckCircle, AlertTriangle, ArrowLeft, Loader2, XCircle } from "lucide-react";
import { useState } from "react";
import { base64ToImageUrl, exportDocx } from "../../lib/api";
import { saveAnalysis } from "../../lib/supabase";
import type { FeatureApiResponse, AnalysisFormData } from "../../lib/types";

interface FeaturePageResultsProps {
  featureName: string;
  teamAName?: string;
  teamBName?: string;
  results: FeatureApiResponse | null;
  error?: string | null;
  userId?: string;
  inputData?: AnalysisFormData;
  onBack?: () => void;
  onSaved?: () => void;
}

export function FeaturePageResults({
  featureName,
  teamAName = "Team A",
  teamBName = "Team B",
  results,
  error,
  userId,
  inputData,
  onBack,
  onSaved,
}: FeaturePageResultsProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saved" | "error">("idle");
  const [isExporting, setIsExporting] = useState(false);

  // ── Save to Supabase ─────────────────────────────────────────
  const handleSave = async () => {
    if (!userId || !results) return;
    setIsSaving(true);
    setSaveStatus("idle");

    const matchName = `${teamAName} vs ${teamBName}`;
    const { error: saveError } = await saveAnalysis(
      userId,
      matchName,
      featureName,
      (inputData as unknown as Record<string, unknown>) ?? {},
      results as unknown as Record<string, unknown>
    );

    setIsSaving(false);
    if (saveError) {
      setSaveStatus("error");
    } else {
      setSaveStatus("saved");
      onSaved?.();
    }
    setTimeout(() => setSaveStatus("idle"), 3000);
  };

  // ── Export DOCX ──────────────────────────────────────────────
  const handleExportDocx = async () => {
    if (!results) return;
    setIsExporting(true);
    try {
      const blob = await exportDocx({
        analysis_data: results as unknown as Record<string, unknown>,
        team_name: teamAName,
        opponent_name: teamBName,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `spaceaifc_${teamAName}_vs_${teamBName}.docx`.replace(/\s+/g, "_");
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setIsExporting(false);
    }
  };

  // ── Download a visualization image ───────────────────────────
  const handleDownloadImage = (imageBase64: string, title: string) => {
    const url = base64ToImageUrl(imageBase64);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.replace(/\s+/g, "_")}.png`;
    a.click();
  };

  // ── Derived data from API response ───────────────────────────
  const visualizations = results?.visualizations ?? [];
  const insights = results?.insights ?? [];
  const recommendations = results?.recommendations ?? [];

  // Extract zone data from space_control-style responses
  const zones: Record<string, { team_a: number; team_b: number }> =
    (results?.zones as any) ??
    (results?.data?.zones as any) ?? {};
  const zoneEntries = Object.entries(zones).slice(0, 3);

  // Extract key metrics from response data
  const teamAControl =
    (results?.team_a_control as number) ??
    (results?.data?.team_a_control as number) ?? null;
  const teamBControl =
    (results?.team_b_control as number) ??
    (results?.data?.team_b_control as number) ?? null;

  // Extract other top-level metrics dynamically
  const ignoredKeys = ["success", "visualizations", "insights", "recommendations", "data", "zones", "team_a_control", "team_b_control", "mode", "text", "sections", "team_a_roles", "team_b_roles", "team_a", "team_b", "events", "goals_a", "goals_b", "possession_a", "possession_b", "territorial_control_a", "matchup_1", "matchup_2", "verdict", "action_id", "action_name"];
  
  const extractExtraMetrics = () => {
    if (!results) return [];
    
    // Check results and results.data
    const allEntries = {
      ...results,
      ...(results.data || {})
    };
    
    return Object.entries(allEntries)
      .filter(([k, v]) => !ignoredKeys.includes(k) && (typeof v === 'number' || typeof v === 'string'))
      .slice(0, 3);
  };
  
  const extraMetrics = extractExtraMetrics();

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto p-8 space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-4">
            {onBack && (
              <button
                onClick={onBack}
                className="p-2 rounded-lg bg-white/5 border border-white/10 text-white/60 hover:text-white hover:bg-white/10 transition-all"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
            )}
            <h2 className="text-2xl font-bold text-white">Analysis Results</h2>
          </div>
          <div className="flex items-center gap-2">
            {error ? (
              <span className="text-sm text-red-400 flex items-center gap-2">
                <XCircle className="w-4 h-4" />
                Analysis Failed
              </span>
            ) : (
              <span className="text-sm text-green-400 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Analysis Complete
              </span>
            )}
          </div>
        </motion.div>

        {/* Video Simulation Banner */}
        {inputData?.inputType === "video" && !error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl p-4 bg-[#00d9ff]/10 border border-[#00d9ff]/30 flex items-center gap-3 shadow-[0_0_15px_rgba(0,217,255,0.1)]"
          >
            <AlertTriangle className="w-5 h-5 text-[#00d9ff] shrink-0" />
            <p className="text-[#00d9ff] text-sm font-medium">
              Analysis based on simulated tracking data. Full video extraction coming soon.
            </p>
          </motion.div>
        )}

        {/* Error state */}
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-xl p-6 bg-red-500/10 border border-red-500/30"
          >
            <p className="text-red-400 font-medium mb-2">⚠ Analysis Error</p>
            <p className="text-red-300/80 text-sm">{error}</p>
            <p className="text-white/40 text-xs mt-3">
              Make sure the FastAPI backend is running at{" "}
              <code className="text-cyan-400">http://localhost:8000</code>
            </p>
          </motion.div>
        )}

        {/* Visualizations — decoded from base64 */}
        {visualizations.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h3 className="text-lg font-bold text-white mb-4">Visualizations</h3>
            <div className={`grid gap-6 ${visualizations.length === 1 ? "grid-cols-1" : "grid-cols-2"}`}>
              {visualizations.map((viz, i) => (
                <div
                  key={i}
                  className="rounded-xl p-4 backdrop-blur-xl border border-white/10"
                  style={{ background: "linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%)" }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-bold text-white text-sm">{viz.title}</h4>
                    <button
                      onClick={() => handleDownloadImage(viz.image_base64, viz.title)}
                      className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                    >
                      <Download className="w-4 h-4 text-white/50 hover:text-cyan-400 transition-colors" />
                    </button>
                  </div>
                  {viz.description && (
                    <p className="text-xs text-white/40 mb-3">{viz.description}</p>
                  )}
                  <img
                    src={base64ToImageUrl(viz.image_base64)}
                    alt={viz.title}
                    className="w-full rounded-lg object-contain"
                    style={{ maxHeight: "320px" }}
                  />
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* No visualizations placeholder */}
        {!error && visualizations.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h3 className="text-lg font-bold text-white mb-4">Visualizations</h3>
            <div className="grid grid-cols-2 gap-6">
              {["Primary Analysis", "Secondary View"].map((label) => (
                <div
                  key={label}
                  className="rounded-xl p-6 backdrop-blur-xl border border-white/10 aspect-[3/2]"
                  style={{ background: "linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%)" }}
                >
                  <div className="w-full h-full bg-gradient-to-br from-cyan-900/20 to-blue-900/20 rounded-lg flex items-center justify-center border border-cyan-500/20">
                    <span className="text-white/40 text-sm">{label}</span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Key Metrics */}
        {(teamAControl !== null || teamBControl !== null) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h3 className="text-lg font-bold text-white mb-4">Key Metrics</h3>
            <div className="grid grid-cols-3 gap-4">
              {teamAControl !== null && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.3 }}
                  className="rounded-xl p-6 backdrop-blur-xl border border-white/10 text-center"
                  style={{ background: "linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)" }}
                >
                  <div className="text-sm text-white/50 mb-2">{teamAName} Control</div>
                  <div className="text-3xl font-bold mb-1" style={{ color: "#00d9ff" }}>
                    {typeof teamAControl === "number" ? `${teamAControl.toFixed(1)}%` : teamAControl}
                  </div>
                </motion.div>
              )}
              {teamBControl !== null && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.4 }}
                  className="rounded-xl p-6 backdrop-blur-xl border border-white/10 text-center"
                  style={{ background: "linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)" }}
                >
                  <div className="text-sm text-white/50 mb-2">{teamBName} Control</div>
                  <div className="text-3xl font-bold mb-1" style={{ color: "#ff4757" }}>
                    {typeof teamBControl === "number" ? `${teamBControl.toFixed(1)}%` : teamBControl}
                  </div>
                </motion.div>
              )}
              {extraMetrics.map(([key, val]) => (
                  <motion.div
                    key={key}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.5 }}
                    className="rounded-xl p-6 backdrop-blur-xl border border-white/10 text-center"
                    style={{ background: "linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)" }}
                  >
                    <div className="text-sm text-white/50 mb-2 capitalize">
                      {key.replace(/_/g, " ")}
                    </div>
                    <div className="text-xl font-bold mb-1 text-yellow-400">
                      {val}
                    </div>
                  </motion.div>
                ))}
            </div>
          </motion.div>
        )}

        {/* Zone Breakdown */}
        {zoneEntries.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="rounded-xl p-6 backdrop-blur-xl border border-white/10"
            style={{ background: "linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%)" }}
          >
            <h3 className="text-lg font-bold text-white mb-4">Zone Breakdown</h3>
            <div className="space-y-4">
              {zoneEntries.map(([zoneName, zoneData], i) => {
                const teamAPercent = typeof zoneData?.team_a === "number" ? Math.round(zoneData.team_a) : 50;
                const teamBPercent = 100 - teamAPercent;
                return (
                  <div key={zoneName}>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-white/70 capitalize">{zoneName.replace(/_/g, " ")}</span>
                      <div className="flex items-center gap-4">
                        <span className="text-cyan-400 font-medium">{teamAName}: {teamAPercent}%</span>
                        <span className="text-red-400 font-medium">{teamBName}: {teamBPercent}%</span>
                      </div>
                    </div>
                    <div className="h-3 bg-white/5 rounded-full overflow-hidden flex">
                      <motion.div className="bg-gradient-to-r from-cyan-500 to-cyan-400" initial={{ width: 0 }} animate={{ width: `${teamAPercent}%` }} transition={{ delay: 0.5 + i * 0.1, duration: 0.8 }} />
                      <motion.div className="bg-gradient-to-r from-red-400 to-red-500"  initial={{ width: 0 }} animate={{ width: `${teamBPercent}%` }} transition={{ delay: 0.5 + i * 0.1, duration: 0.8 }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* Insights */}
        {(insights.length > 0 || recommendations.length > 0) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="rounded-xl p-6 backdrop-blur-xl border border-white/10"
            style={{ background: "linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%)" }}
          >
            <h3 className="text-lg font-bold text-white mb-4">Key Insights</h3>
            <div className="space-y-3">
              {insights.map((insight, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.7 + i * 0.08 }}
                  className="flex items-start gap-3"
                >
                  <CheckCircle className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />
                  <p className="text-white/80 leading-relaxed">{insight}</p>
                </motion.div>
              ))}
              {recommendations.map((rec, i) => (
                <motion.div
                  key={`rec-${i}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.7 + (insights.length + i) * 0.08 }}
                  className="flex items-start gap-3"
                >
                  <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" />
                  <p className="text-white/80 leading-relaxed">{rec}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Action Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          className="flex items-center gap-4"
        >
          <button
            onClick={() => visualizations[0] && handleDownloadImage(visualizations[0].image_base64, featureName)}
            disabled={visualizations.length === 0}
            className="flex items-center gap-2 px-6 py-3 rounded-lg bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Download className="w-4 h-4" />
            Download PNG
          </button>

          <button
            onClick={handleExportDocx}
            disabled={isExporting || !results}
            className="flex items-center gap-2 px-6 py-3 rounded-lg bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
            {isExporting ? "Exporting..." : "Download Report (DOCX)"}
          </button>

          {userId && (
            <button
              onClick={handleSave}
              disabled={isSaving || !results || saveStatus === "saved"}
              className="flex items-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:shadow-[0_0_30px_rgba(0,217,255,0.4)] transition-all ml-auto disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isSaving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : saveStatus === "saved" ? (
                <CheckCircle className="w-4 h-4 text-green-300" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {isSaving ? "Saving..." : saveStatus === "saved" ? "Saved!" : "Save to History"}
            </button>
          )}

          {saveStatus === "error" && (
            <span className="text-sm text-red-400">Save failed — check Supabase config.</span>
          )}
        </motion.div>
      </div>
    </div>
  );
}
