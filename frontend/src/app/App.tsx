import { useState, useEffect } from "react";
import { AppSidebar } from "./components/AppSidebar";
import { Home } from "./components/Home";
import { FeaturePageInput } from "./components/FeaturePageInput";
import { FeaturePageResults } from "./components/FeaturePageResults";
import { AskSpaceAI } from "./components/AskSpaceAI";
import { PlayerAssessment } from "./components/PlayerAssessment";
import { Simulation } from "./components/Simulation";
import { Compare } from "./components/Compare";
import { Strategy } from "./components/Strategy";
import { Explanation } from "./components/Explanation";
import { History } from "./components/History";
import { Auth } from "./components/Auth";
import {
  Map,
  BarChart3,
  Share2,
  Shield,
  Zap,
  Grid3x3,
  Lightbulb,
  User,
  MessageSquare,
  GitCompare,
  Gamepad2,
  FileText,
} from "lucide-react";

// Lib
import { analyzeFeature } from "../lib/api";
import { onAuthStateChange, signOut } from "../lib/supabase";
import { getAnalyses } from "../lib/supabase";
import type { UserProfile, FeatureApiResponse, AnalysisFormData, SavedAnalysis } from "../lib/types";

const featureConfig: Record<string, { name: string; description: string; icon: any }> = {
  "full-match": { name: "Full Match Analysis", description: "Complete tactical breakdown", icon: BarChart3 },
  "pass-network": { name: "Pass Network", description: "Passing structure & key distributors", icon: Share2 },
  "space-control": { name: "Space Control", description: "Territorial dominance mapping", icon: Map },
  formation: { name: "Formation Detection", description: "Identify team shape & structure", icon: Shield },
  "press-resistance": { name: "Press Resistance", description: "Measure pressing survival", icon: Zap },
  patterns: { name: "Tactical Patterns", description: "Detect overlaps, blocks, overloads", icon: Grid3x3 },
  strategy: { name: "Strategy Recommendations", description: "AI-powered tactical suggestions", icon: Lightbulb },
  "player-assessment": { name: "Player Assessment", description: "Scouting reports & radar charts", icon: User },
  "ask-ai": { name: "Ask SpaceAI", description: "Tactical Q&A with AI", icon: MessageSquare },
  compare: { name: "Compare", description: "Side-by-side tactical comparison", icon: GitCompare },
  simulation: { name: "Simulation", description: "What-if tactical testing", icon: Gamepad2 },
  explanation: { name: "Tactical Explanation", description: "Full match analysis report", icon: FileText },
};

export default function App() {
  // Auth state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<UserProfile | null>(null);

  // Navigation state
  const [currentView, setCurrentView] = useState("home");
  const [showResults, setShowResults] = useState(false);

  // Analysis state
  const [isLoading, setIsLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisResults, setAnalysisResults] = useState<FeatureApiResponse | null>(null);
  const [lastFormData, setLastFormData] = useState<AnalysisFormData | null>(null);

  // History (loaded from Supabase)
  const [savedAnalyses, setSavedAnalyses] = useState<SavedAnalysis[]>([]);

  // ── Auth: restore session on mount ────────────────────────────
  useEffect(() => {
    const unsubscribe = onAuthStateChange((authUser) => {
      if (authUser) {
        setUser(authUser);
        setIsAuthenticated(true);
        loadAnalyses(authUser.id);
      } else {
        setUser(null);
        setIsAuthenticated(false);
        setSavedAnalyses([]);
      }
    });
    return unsubscribe;
  }, []);

  const loadAnalyses = async (userId: string) => {
    const { data } = await getAnalyses(userId);
    setSavedAnalyses(data);
  };

  // ── Auth handlers ─────────────────────────────────────────────
  const handleLogin = (authUser: UserProfile) => {
    setUser(authUser);
    setIsAuthenticated(true);
    setCurrentView("home");
    loadAnalyses(authUser.id);
  };

  const handleLogout = async () => {
    await signOut();
    setIsAuthenticated(false);
    setUser(null);
    setCurrentView("home");
    setShowResults(false);
    setAnalysisResults(null);
    setSavedAnalyses([]);
  };

  // ── Navigation ────────────────────────────────────────────────
  const handleNavigate = (id: string) => {
    if (id === "logout") {
      handleLogout();
      return;
    }
    setCurrentView(id);
    setShowResults(false);
    setAnalysisResults(null);
    setAnalysisError(null);
  };

  const handleFeatureClick = (featureId: string) => {
    setCurrentView(featureId);
    setShowResults(false);
    setAnalysisResults(null);
    setAnalysisError(null);
  };

  // ── Analysis ──────────────────────────────────────────────────
  const handleAnalyze = async (formData: AnalysisFormData) => {
    setIsLoading(true);
    setAnalysisError(null);
    setLastFormData(formData);

    try {
      const results = await analyzeFeature(currentView, formData);
      setAnalysisResults(results);
      setShowResults(true);

      // Refresh history in background after saving
      if (user) {
        setTimeout(() => loadAnalyses(user.id), 1500);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Analysis failed.";
      setAnalysisError(message);
      // Still show results panel so the error is displayed there
      setShowResults(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToInput = () => {
    setShowResults(false);
    setAnalysisResults(null);
    setAnalysisError(null);
  };

  const handleHistorySaved = () => {
    if (user) loadAnalyses(user.id);
  };

  // ── Load a saved analysis from History ────────────────────────
  const handleLoadAnalysis = (analysis: SavedAnalysis) => {
    // Navigate to the feature's results page with saved data
    const featureId = Object.keys(featureConfig).find(
      (k) => featureConfig[k].name === analysis.feature
    ) ?? "full-match";
    setCurrentView(featureId);
    setAnalysisResults(analysis.results as unknown as FeatureApiResponse);
    setShowResults(true);
  };

  // ── Auth gate ─────────────────────────────────────────────────
  if (!isAuthenticated) {
    return <Auth onLogin={handleLogin} />;
  }

  const teamAName = lastFormData?.teamAName || "Team A";
  const teamBName = lastFormData?.teamBName || "Team B";

  return (
    <div className="relative size-full overflow-hidden">
      {/* UCL Background */}
      <div
        className="absolute inset-0"
        style={{
          background: `
            radial-gradient(ellipse at top, rgba(0, 217, 255, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at bottom right, rgba(123, 97, 255, 0.06) 0%, transparent 50%),
            #0a0e27
          `,
        }}
      >
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `
              radial-gradient(circle at 20% 30%, #00d9ff 1px, transparent 1px),
              radial-gradient(circle at 60% 70%, #00d9ff 1px, transparent 1px),
              radial-gradient(circle at 80% 20%, #00d9ff 1px, transparent 1px),
              radial-gradient(circle at 30% 80%, #00d9ff 1px, transparent 1px)
            `,
            backgroundSize: "100px 100px, 120px 120px, 90px 90px, 110px 110px",
          }}
        />
      </div>

      {/* Main Layout */}
      <div className="relative z-10 size-full flex">
        {/* Sidebar */}
        <AppSidebar activeItem={currentView} onNavigate={handleNavigate} user={user} />

        {/* Main Content */}
        <div className="flex-1 overflow-hidden">
          {currentView === "home" && (
            <Home
              onFeatureClick={handleFeatureClick}
              user={user}
              recentAnalyses={savedAnalyses.slice(0, 3)}
            />
          )}

          {currentView === "ask-ai" && <AskSpaceAI />}
          
          {currentView === "player-assessment" && <PlayerAssessment />}
          
          {currentView === "simulation" && <Simulation />}
          
          {currentView === "compare" && <Compare />}
          
          {currentView === "strategy" && <Strategy />}
          
          {currentView === "explanation" && <Explanation />}

          {currentView === "history" && (
            <History
              userId={user?.id}
              savedAnalyses={savedAnalyses}
              onLoadAnalysis={handleLoadAnalysis}
              onDeleted={handleHistorySaved}
            />
          )}

          {/* Feature input pages */}
          {featureConfig[currentView] && !showResults && !["ask-ai", "player-assessment", "simulation", "compare", "strategy", "explanation"].includes(currentView) && (
            <FeaturePageInput
              featureId={currentView}
              featureName={featureConfig[currentView].name}
              featureDescription={featureConfig[currentView].description}
              icon={featureConfig[currentView].icon}
              onAnalyze={handleAnalyze}
              isLoading={isLoading}
            />
          )}

          {/* Feature results pages */}
          {featureConfig[currentView] && showResults && !["ask-ai", "player-assessment", "simulation", "compare", "strategy", "explanation"].includes(currentView) && (
            <FeaturePageResults
              featureName={featureConfig[currentView].name}
              teamAName={teamAName}
              teamBName={teamBName}
              results={analysisResults}
              error={analysisError}
              userId={user?.id}
              inputData={lastFormData ?? undefined}
              onBack={handleBackToInput}
              onSaved={handleHistorySaved}
            />
          )}

          {/* Settings placeholder */}
          {currentView === "settings" && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">⚙️</div>
                <h2 className="text-2xl font-bold text-white mb-2">Settings</h2>
                <p className="text-white/50">Configure your SpaceAI FC experience</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}