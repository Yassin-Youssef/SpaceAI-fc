import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion, MotionConfig } from "motion/react";
import { toast } from "sonner";
import { Toaster } from "./components/ui/sonner";
import { TopNav } from "./components/TopNav";
import { Home } from "./components/Home";
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
import { FEATURES, FEATURE_BY_ID, sectionOf } from "../lib/features";
import type { UserProfile, FeatureApiResponse, AnalysisFormData, SavedAnalysis, HealthResponse } from "../lib/types";

/** Features that use the shared input → results flow. */
const POSITION_FEATURES = new Set(["full-match", "pass-network", "space-control", "formation", "press-resistance", "patterns", "strategy", "explanation"]);

const featureMeta = FEATURE_BY_ID;

const GUEST_USER: UserProfile = { id: "guest", email: "", full_name: "Guest", isGuest: true };

export default function App() {
  // ── Auth ─────────────────────────────────────────────────────
  const [user, setUser] = useState<UserProfile | null>(null);
  const [authReady, setAuthReady] = useState(false);

  // ── Navigation ───────────────────────────────────────────────
  const [currentView, setCurrentView] = useState("home");
  const [showResults, setShowResults] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  // Fixture picked on Home, run as soon as Full Match Analysis opens
  const [autoDemo, setAutoDemo] = useState<string | null>(null);

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
      <div className="flex h-full items-center justify-center bg-background" aria-busy="true" aria-label="Loading">
        <span className="font-display text-2xl text-text-muted">SPACEAI FC</span>
      </div>
    );
  }
  if (!user) {
    return (
      <MotionConfig reducedMotion={reduceMotion ? "always" : "user"}>
        <Toaster position="top-right" duration={4000} closeButton offset={{ top: 72, right: 16 }} />
        <Auth onLogin={handleLogin} onGuest={() => handleLogin(GUEST_USER)} />
      </MotionConfig>
    );
  }

  const feature = featureMeta[currentView];
  const isPositionFeature = POSITION_FEATURES.has(currentView);
  const viewKey = `${currentView}:${isPositionFeature && showResults ? "results" : "input"}`;

  return (
    <MotionConfig reducedMotion={reduceMotion ? "always" : "user"}>
      <Toaster position="top-right" duration={4000} closeButton offset={{ top: 72, right: 16 }} />
      <div className="flex h-full w-full flex-col overflow-hidden bg-background" data-section={sectionOf(currentView)}>
        <TopNav
          activeItem={currentView}
          onNavigate={navigate}
          user={user}
          health={health}
          healthError={healthError}
          mobileOpen={mobileNav}
          onMobileOpen={() => setMobileNav(true)}
          onMobileClose={() => setMobileNav(false)}
        />

          <div className="relative min-h-0 flex-1">
            <AnimatePresence>
              {isLoading && (
                <motion.div key="progress" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="busy-bar pointer-events-none !top-0 !bottom-auto z-20 text-section-fill" aria-hidden />
              )}
            </AnimatePresence>
            <AnimatePresence mode="wait" initial={false}>
              <motion.div key={viewKey} variants={pageVariants} initial="initial" animate="animate" exit="exit" className="absolute inset-0">
                {currentView === "home" && (
                  <Home user={user} recentAnalyses={savedAnalyses.slice(0, 3)} onFeatureClick={navigate} onNavigate={navigate} onRunMatch={(id) => { setAutoDemo(id); navigate("full-match"); }} />
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
                    autoDemoId={currentView === "full-match" ? autoDemo : null}
                    onAutoDemoUsed={() => setAutoDemo(null)}
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
