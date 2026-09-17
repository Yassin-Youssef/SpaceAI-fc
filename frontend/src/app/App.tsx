import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion, MotionConfig } from "motion/react";
import { Menu } from "lucide-react";
import { toast } from "sonner";
import { Toaster } from "./components/ui/sonner";
import { AppSidebar } from "./components/AppSidebar";
import { Home, FEATURES } from "./components/Home";
import { About } from "./components/About";
import { FeaturePageInput } from "./components/FeaturePageInput";
import { FeaturePageResults } from "./components/FeaturePageResults";
import { AskSpaceAI } from "./components/AskSpaceAI";
import { PlayerAssessment } from "./components/PlayerAssessment";
import { Simulation } from "./components/Simulation";
import { Compare } from "./components/Compare";
import { History } from "./components/History";
import { Settings } from "./components/Settings";
import { Auth } from "./components/Auth";
import { analyzeFeature, healthCheck, type ResolvedInput } from "../lib/api";
import { onAuthStateChange, signOut, getAnalyses, getCurrentUser } from "../lib/supabase";
import { pageVariants } from "../lib/motion";
import type { UserProfile, FeatureApiResponse, AnalysisFormData, SavedAnalysis, HealthResponse } from "../lib/types";

/** Features that use the shared input → results flow. */
const POSITION_FEATURES = new Set(["full-match", "pass-network", "space-control", "formation", "press-resistance", "patterns", "strategy", "explanation"]);

const featureMeta = Object.fromEntries(FEATURES.map((f) => [f.id, f]));

const GUEST_USER: UserProfile = { id: "guest", email: "", full_name: "Guest", isGuest: true };

export default function App() {
  // ── Auth ─────────────────────────────────────────────────────
  const [user, setUser] = useState<UserProfile | null>(null);
  const [authReady, setAuthReady] = useState(false);

  // ── Navigation ───────────────────────────────────────────────
  const [currentView, setCurrentView] = useState("home");
  const [showResults, setShowResults] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);

  // ── Analysis state (per feature) ─────────────────────────────
  const [isLoading, setIsLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisResults, setAnalysisResults] = useState<FeatureApiResponse | null>(null);
  const [resolved, setResolved] = useState<ResolvedInput | null>(null);
  const [lastFormData, setLastFormData] = useState<AnalysisFormData | null>(null);
  const [formCache, setFormCache] = useState<Record<string, AnalysisFormData>>({});

  // ── Backend health / history / prefs ─────────────────────────
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState(false);
  const [savedAnalyses, setSavedAnalyses] = useState<SavedAnalysis[]>([]);
  const [lastContext, setLastContext] = useState<Record<string, unknown> | null>(null);
  const [reduceMotion, setReduceMotion] = useState<boolean>(() => {
    try { return localStorage.getItem("spaceai.reduceMotion") === "1"; } catch { return false; }
  });

  const refreshHealth = useCallback(async () => {
    try {
      const h = await healthCheck();
      setHealth(h);
      setHealthError(false);
    } catch {
      setHealth(null);
      setHealthError(true);
    }
  }, []);

  useEffect(() => {
    void refreshHealth();
    const id = window.setInterval(refreshHealth, 30000);
    return () => window.clearInterval(id);
  }, [refreshHealth]);

  useEffect(() => {
    try { localStorage.setItem("spaceai.reduceMotion", reduceMotion ? "1" : "0"); } catch { /* ignore */ }
  }, [reduceMotion]);

  const loadAnalyses = useCallback(async (userId: string) => {
    const { data } = await getAnalyses(userId);
    setSavedAnalyses(data);
  }, []);

  // Restore Supabase session on mount
  useEffect(() => {
    let cancelled = false;
    getCurrentUser().then((u) => {
      if (cancelled) return;
      if (u) { setUser(u); void loadAnalyses(u.id); }
      setAuthReady(true);
    });
    const unsubscribe = onAuthStateChange((authUser) => {
      if (authUser) {
        setUser(authUser);
        void loadAnalyses(authUser.id);
      } else {
        setUser((prev) => (prev?.isGuest ? prev : null));
        setSavedAnalyses([]);
      }
    });
    return () => { cancelled = true; unsubscribe(); };
  }, [loadAnalyses]);

  // ── Handlers ─────────────────────────────────────────────────
  const handleLogin = (authUser: UserProfile) => {
    setUser(authUser);
    setCurrentView("home");
    if (!authUser.isGuest) void loadAnalyses(authUser.id);
    toast.success(authUser.isGuest ? "Continuing as guest" : `Welcome, ${authUser.full_name ?? authUser.email}`);
  };

  const handleLogout = async () => {
    if (!user?.isGuest) await signOut();
    setUser(null);
    setCurrentView("home");
    setShowResults(false);
    setAnalysisResults(null);
    setSavedAnalyses([]);
  };

  const navigate = (id: string) => {
    if (id === "logout") { void handleLogout(); return; }
    setCurrentView(id);
    setShowResults(false);
    setAnalysisError(null);
  };

  const runAnalysis = async (featureId: string, formData: AnalysisFormData) => {
    setIsLoading(true);
    setAnalysisError(null);
    setAnalysisResults(null);
    setLastFormData(formData);
    setFormCache((c) => ({ ...c, [featureId]: formData }));
    setShowResults(true);
    try {
      const { results, resolved: res } = await analyzeFeature(featureId, formData);
      setAnalysisResults(results);
      setResolved(res);
      setLastContext({
        ...summariseForChat(featureId, results),
        team_a_name: formData.teamAName?.trim() || "Team A",
        team_b_name: formData.teamBName?.trim() || "Team B",
        ...(formData.demoMatch ? { match: formData.demoMatch.title, match_context: formData.demoMatch.subtitle } : {}),
      });
      toast.success(`${featureMeta[featureId]?.name ?? "Analysis"} complete`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Analysis failed.";
      setAnalysisError(message);
      setResolved(null);
      toast.error("Analysis failed", { description: message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToInput = () => {
    setShowResults(false);
    setAnalysisError(null);
  };

  const handleLoadSaved = (analysis: SavedAnalysis) => {
    const featureId = FEATURES.find((f) => f.name === analysis.feature)?.id ?? "full-match";
    if (!POSITION_FEATURES.has(featureId)) {
      toast.info("This saved analysis type can only be re-run from its page.");
      setCurrentView(featureId);
      return;
    }
    const input = analysis.input_data as unknown as AnalysisFormData;
    setCurrentView(featureId);
    setLastFormData(input);
    setAnalysisResults(analysis.results as unknown as FeatureApiResponse);
    setResolved(null);
    setAnalysisError(null);
    setShowResults(true);
  };

  // ── Auth gate ────────────────────────────────────────────────
  if (!authReady) {
    return (
      <div className="flex h-full items-center justify-center bg-background">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-brand/30 border-t-brand" aria-label="Loading" />
      </div>
    );
  }
  if (!user) {
    return (
      <MotionConfig reducedMotion={reduceMotion ? "always" : "user"}>
        <Toaster position="top-right" richColors closeButton />
        <Auth onLogin={handleLogin} onGuest={() => handleLogin(GUEST_USER)} />
      </MotionConfig>
    );
  }

  const feature = featureMeta[currentView];
  const isPositionFeature = POSITION_FEATURES.has(currentView);
  const viewKey = `${currentView}:${isPositionFeature && showResults ? "results" : "input"}`;

  return (
    <MotionConfig reducedMotion={reduceMotion ? "always" : "user"}>
      <Toaster position="top-right" richColors closeButton />
      <div className="relative flex h-full w-full overflow-hidden bg-background">
        {/* Ambient background */}
        <div className="pointer-events-none absolute inset-0" aria-hidden>
          <div className="absolute inset-0" style={{ background: "radial-gradient(ellipse at top, rgba(0,217,255,0.08) 0%, transparent 55%), radial-gradient(ellipse at bottom right, rgba(123,97,255,0.07) 0%, transparent 50%)" }} />
          <div className="absolute inset-0 opacity-[0.08]" style={{ backgroundImage: "radial-gradient(circle at 20% 30%, #00d9ff 1px, transparent 1px), radial-gradient(circle at 60% 70%, #00d9ff 1px, transparent 1px), radial-gradient(circle at 80% 20%, #00d9ff 1px, transparent 1px)", backgroundSize: "100px 100px, 120px 120px, 90px 90px" }} />
        </div>

        <AppSidebar
          activeItem={currentView}
          onNavigate={navigate}
          user={user}
          health={health}
          healthError={healthError}
          mobileOpen={mobileNav}
          onMobileClose={() => setMobileNav(false)}
        />

        <div className="relative z-10 flex min-w-0 flex-1 flex-col">
          {/* Mobile top bar */}
          <div className="flex items-center gap-3 border-b border-white/10 bg-surface-1/80 px-4 py-3 backdrop-blur-xl lg:hidden">
            <button type="button" onClick={() => setMobileNav(true)} className="rounded-lg p-2 text-white hover:bg-white/5" aria-label="Open menu">
              <Menu className="h-5 w-5" />
            </button>
            <div className="font-bold text-white">Space<span className="text-brand">AI</span> FC</div>
            <div className="ml-auto truncate text-xs text-text-muted">{feature?.name ?? (currentView === "home" ? "Dashboard" : currentView)}</div>
          </div>

          <div className="relative min-h-0 flex-1">
            <AnimatePresence mode="wait" initial={false}>
              <motion.div key={viewKey} variants={pageVariants} initial="initial" animate="animate" exit="exit" className="absolute inset-0">
                {currentView === "home" && (
                  <Home user={user} recentAnalyses={savedAnalyses.slice(0, 3)} onFeatureClick={navigate} onNavigate={navigate} />
                )}
                {currentView === "about" && <About onFeatureClick={navigate} />}
                {currentView === "ask-ai" && <AskSpaceAI health={health} context={lastContext} />}
                {currentView === "player-assessment" && <PlayerAssessment health={health} />}
                {currentView === "simulation" && <Simulation />}
                {currentView === "compare" && <Compare />}
                {currentView === "history" && (
                  <History user={user} savedAnalyses={savedAnalyses} onLoadAnalysis={handleLoadSaved} onDeleted={() => !user.isGuest && loadAnalyses(user.id)} onNavigate={navigate} />
                )}
                {currentView === "settings" && (
                  <Settings user={user} health={health} healthError={healthError} onRefreshHealth={refreshHealth} reduceMotion={reduceMotion} onReduceMotion={setReduceMotion} />
                )}

                {feature && isPositionFeature && !showResults && (
                  <FeaturePageInput
                    key={currentView}
                    featureId={currentView}
                    featureName={feature.name}
                    featureDescription={feature.description}
                    icon={feature.icon}
                    onAnalyze={(data) => runAnalysis(currentView, data)}
                    isLoading={isLoading}
                    initial={formCache[currentView] ?? null}
                  />
                )}

                {feature && isPositionFeature && showResults && (
                  <FeaturePageResults
                    featureId={currentView}
                    featureName={feature.name}
                    icon={feature.icon}
                    teamAName={lastFormData?.teamAName?.trim() || "Team A"}
                    teamBName={lastFormData?.teamBName?.trim() || "Team B"}
                    teamAColor={lastFormData?.teamAColor}
                    teamBColor={lastFormData?.teamBColor}
                    results={analysisResults}
                    resolved={resolved}
                    error={analysisError}
                    isLoading={isLoading}
                    userId={user.isGuest ? undefined : user.id}
                    inputData={lastFormData ?? undefined}
                    onBack={handleBackToInput}
                    onRetry={lastFormData ? () => runAnalysis(currentView, lastFormData) : undefined}
                    onSaved={() => !user.isGuest && loadAnalyses(user.id)}
                  />
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </MotionConfig>
  );
}

/** Compact context handed to Ask SpaceAI so answers can reference the last run. */
function summariseForChat(featureId: string, results: FeatureApiResponse): Record<string, unknown> {
  const r = results as Record<string, unknown>;
  const pick = (obj: unknown, keys: string[]) => {
    if (!obj || typeof obj !== "object") return undefined;
    const o = obj as Record<string, unknown>;
    const out: Record<string, unknown> = {};
    for (const k of keys) if (k in o) out[k] = o[k];
    return Object.keys(out).length ? out : undefined;
  };
  const ctx: Record<string, unknown> = { feature: featureId };
  const formation = pick(r.formation ?? r, ["team_a_formation", "team_b_formation", "team_a_confidence", "team_b_confidence"]);
  const space = pick(r.space_control ?? r, ["team_a_control", "team_b_control", "zones"]);
  const press = pick(r.press_resistance ?? r, ["press_resistance_score", "escape_rate", "pass_success_under_pressure"]);
  const passes = pick(r.pass_network ?? r, ["total_passes", "key_distributor", "weak_links"]);
  if (formation) ctx.formation = formation;
  if (space) ctx.space_control = space;
  if (press) ctx.press_resistance = press;
  if (passes) ctx.pass_network = passes;
  if (r.formation_a) ctx.formation_a = r.formation_a;
  if (r.formation_b) ctx.formation_b = r.formation_b;
  const intel = (r.intelligence ?? r) as Record<string, unknown>;
  if (Array.isArray(intel.recommendations)) ctx.recommendations = (intel.recommendations as Array<Record<string, unknown>>).slice(0, 5).map((x) => x.description);
  if (Array.isArray(intel.swot)) ctx.swot = (intel.swot as Array<Record<string, unknown>>).slice(0, 8).map((x) => `${x.category}: ${x.description}`);
  return ctx;
}
