import { motion } from "motion/react";
import { Map, Upload, FileUp, Play, Loader2 } from "lucide-react";
import { useState, useRef } from "react";
import type { AnalysisFormData, FormPlayer } from "../../lib/types";

const emptyPlayers = (): FormPlayer[] =>
  Array(11)
    .fill(null)
    .map(() => ({ name: "", number: "", x: "", y: "", position: "Midfielder" }));

// ── El Clásico Demo Data (exact coordinates from user spec) ─────
const EL_CLASICO_TEAM_A: FormPlayer[] = [
  { name: "ter Stegen",  number: "1",  x: "5",   y: "40", position: "GK" },
  { name: "Koundé",      number: "23", x: "30",  y: "70", position: "RB" },
  { name: "Araújo",      number: "4",  x: "25",  y: "52", position: "CB" },
  { name: "Cubarsí",     number: "2",  x: "25",  y: "28", position: "CB" },
  { name: "Baldé",       number: "3",  x: "30",  y: "10", position: "LB" },
  { name: "Pedri",       number: "8",  x: "45",  y: "48", position: "CM" },
  { name: "De Jong",     number: "21", x: "45",  y: "32", position: "CM" },
  { name: "Lamine",      number: "19", x: "65",  y: "68", position: "RW" },
  { name: "Gavi",        number: "6",  x: "60",  y: "40", position: "CAM" },
  { name: "Raphinha",    number: "11", x: "65",  y: "12", position: "LW" },
  { name: "Lewandowski", number: "9",  x: "80",  y: "40", position: "ST" },
];

const EL_CLASICO_TEAM_B: FormPlayer[] = [
  { name: "Courtois",    number: "1",  x: "115", y: "40", position: "GK" },
  { name: "Carvajal",   number: "2",  x: "90",  y: "70", position: "RB" },
  { name: "Rüdiger",    number: "22", x: "93",  y: "52", position: "CB" },
  { name: "Militão",    number: "3",  x: "93",  y: "28", position: "CB" },
  { name: "Mendy",      number: "23", x: "90",  y: "10", position: "LB" },
  { name: "Tchouaméni", number: "14", x: "73",  y: "40", position: "CDM" },
  { name: "Valverde",   number: "15", x: "70",  y: "58", position: "CM" },
  { name: "Bellingham", number: "5",  x: "70",  y: "22", position: "CM" },
  { name: "Rodrygo",    number: "11", x: "55",  y: "65", position: "RW" },
  { name: "Mbappé",     number: "7",  x: "50",  y: "40", position: "ST" },
  { name: "Vinícius",   number: "20", x: "55",  y: "15", position: "LW" },
];

interface FeaturePageInputProps {
  featureId: string;
  featureName: string;
  featureDescription: string;
  icon: any;
  onAnalyze?: (data: AnalysisFormData) => void;
  isLoading?: boolean;
}

export function FeaturePageInput({
  featureId,
  featureName,
  featureDescription,
  icon: Icon,
  onAnalyze,
  isLoading = false,
}: FeaturePageInputProps) {
  const [activeTab, setActiveTab] = useState<"manual" | "video" | "dataset">("manual");
  const [teamAPlayers, setTeamAPlayers] = useState<FormPlayer[]>(emptyPlayers());
  const [teamBPlayers, setTeamBPlayers] = useState<FormPlayer[]>(emptyPlayers());
  const [teamAName, setTeamAName] = useState("");
  const [teamBName, setTeamBName] = useState("");
  const [teamAColor, setTeamAColor] = useState("#00d9ff");
  const [teamBColor, setTeamBColor] = useState("#ff4757");
  const [ballX, setBallX] = useState("");
  const [ballY, setBallY] = useState("");
  const [passesText, setPassesText] = useState("");
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [videoFile, setVideoFile] = useState<File | undefined>();
  const [datasetFile, setDatasetFile] = useState<File | undefined>();

  // Feature specific states
  const [minPasses, setMinPasses] = useState("2");
  const [vizMode, setVizMode] = useState<"Both" | "Influence" | "Voronoi">("Both");
  const [pressureRadius, setPressureRadius] = useState("10");
  const [analyzeTeam, setAnalyzeTeam] = useState<"Both" | "Team A" | "Team B">("Both");

  const videoInputRef = useRef<HTMLInputElement>(null);
  const datasetInputRef = useRef<HTMLInputElement>(null);

  const loadDemoData = () => {
    setTeamAName("Barcelona");
    setTeamAPlayers(EL_CLASICO_TEAM_A);
    
    if (featureId !== "formation" && featureId !== "pass-network") {
      setTeamBName("Real Madrid");
      setTeamBPlayers(EL_CLASICO_TEAM_B);
    }
    
    if (featureId === "space-control" || featureId === "full-match") {
      setBallX("60");
      setBallY("40");
    }
    
    if (featureId === "press-resistance") {
      setPassesText("4->8->1, 8->19->1, 19->9->0, 21->8->1");
    } else if (featureId === "pass-network" || featureId === "full-match") {
      setPassesText("4->8, 8->19, 19->9, 21->8, 8->11, 11->9, 23->19, 3->11, 9->6, 6->8, 4->2, 2->21, 21->6, 6->11, 11->3, 8->23, 19->23, 23->8, 4->1, 1->2, 2->8");
    }
  };

  const handleAnalyze = () => {
    if (isLoading) return;
    onAnalyze?.({
      inputType: activeTab,
      teamAPlayers,
      teamBPlayers,
      teamAName,
      teamBName,
      teamAColor,
      teamBColor,
      ballX,
      ballY,
      passesText,
      videoFile,
      youtubeUrl,
      datasetFile,
      minPasses: parseInt(minPasses) || 2,
      vizMode,
      pressureRadius: parseInt(pressureRadius) || 10,
      analyzeTeam,
    });
  };

  const showTeamB = featureId !== "pass-network" && featureId !== "formation";
  const showBall = featureId === "full-match" || featureId === "space-control";
  const showPasses = featureId === "full-match" || featureId === "pass-network" || featureId === "press-resistance";

  const updatePlayerA = (i: number, field: keyof FormPlayer, value: string) => {
    const next = [...teamAPlayers];
    next[i] = { ...next[i], [field]: value };
    setTeamAPlayers(next);
  };

  const updatePlayerB = (i: number, field: keyof FormPlayer, value: string) => {
    const next = [...teamBPlayers];
    next[i] = { ...next[i], [field]: value };
    setTeamBPlayers(next);
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto p-8 space-y-6">
        {/* Feature Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative rounded-xl p-6 backdrop-blur-xl border border-cyan-500/30 overflow-hidden"
          style={{
            background: "linear-gradient(135deg, rgba(0, 217, 255, 0.12) 0%, rgba(0, 217, 255, 0.05) 100%)",
          }}
        >
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_30px_rgba(0,217,255,0.4)]">
              <Icon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">{featureName}</h1>
              <p className="text-white/60">{featureDescription}</p>
            </div>
          </div>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-white/10">
          {[
            { id: "manual", label: "Manual Entry" },
            { id: "video", label: "Video / YouTube" },
            { id: "dataset", label: "Dataset Upload" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-6 py-3 text-sm font-medium transition-all relative ${
                activeTab === tab.id ? "text-cyan-400" : "text-white/60 hover:text-white"
              }`}
            >
              {tab.label}
              {activeTab === tab.id && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-cyan-400 shadow-[0_0_10px_rgba(0,217,255,0.6)]"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
            </button>
          ))}
        </div>

        {/* ── Manual Entry Tab ── */}
        {activeTab === "manual" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <div className={`grid gap-6 ${showTeamB ? 'grid-cols-2' : 'max-w-xl'}`}>
              {/* Team A */}
              <div
                className="rounded-xl p-6 backdrop-blur-xl border border-white/10"
                style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}
              >
                <div className="flex items-center gap-4 mb-4">
                  <input
                    type="text"
                    value={teamAName}
                    onChange={(e) => setTeamAName(e.target.value)}
                    placeholder="Team A Name"
                    className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-white/40 focus:outline-none focus:border-cyan-500/50"
                  />
                  <input
                    type="color"
                    value={teamAColor}
                    onChange={(e) => setTeamAColor(e.target.value)}
                    className="w-12 h-10 rounded-lg cursor-pointer"
                  />
                </div>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {teamAPlayers.map((player, i) => (
                    <div key={i} className="grid grid-cols-5 gap-2">
                      <input type="text" value={player.name}   onChange={(e) => updatePlayerA(i, "name", e.target.value)}   placeholder="Name" className="col-span-2 bg-white/5 border border-white/10 rounded px-2 py-1.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50" />
                      <input type="text" value={player.number} onChange={(e) => updatePlayerA(i, "number", e.target.value)} placeholder="#"    className="bg-white/5 border border-white/10 rounded px-2 py-1.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50" />
                      <input type="text" value={player.x}      onChange={(e) => updatePlayerA(i, "x", e.target.value)}      placeholder="X"    className="bg-white/5 border border-white/10 rounded px-2 py-1.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50" />
                      <input type="text" value={player.y}      onChange={(e) => updatePlayerA(i, "y", e.target.value)}      placeholder="Y"    className="bg-white/5 border border-white/10 rounded px-2 py-1.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50" />
                    </div>
                  ))}
                </div>
              </div>

               {/* Team B */}
              {showTeamB && (
                <div
                  className="rounded-xl p-6 backdrop-blur-xl border border-white/10"
                  style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}
                >
                  <div className="flex items-center gap-4 mb-4">
                    <input
                      type="text"
                      value={teamBName}
                      onChange={(e) => setTeamBName(e.target.value)}
                      placeholder="Team B Name"
                      className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-white/40 focus:outline-none focus:border-cyan-500/50"
                    />
                    <input
                      type="color"
                      value={teamBColor}
                      onChange={(e) => setTeamBColor(e.target.value)}
                      className="w-12 h-10 rounded-lg cursor-pointer"
                    />
                  </div>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {teamBPlayers.map((player, i) => (
                      <div key={i} className="grid grid-cols-5 gap-2">
                        <input type="text" value={player.name}   onChange={(e) => updatePlayerB(i, "name", e.target.value)}   placeholder="Name" className="col-span-2 bg-white/5 border border-white/10 rounded px-2 py-1.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50" />
                        <input type="text" value={player.number} onChange={(e) => updatePlayerB(i, "number", e.target.value)} placeholder="#"    className="bg-white/5 border border-white/10 rounded px-2 py-1.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50" />
                        <input type="text" value={player.x}      onChange={(e) => updatePlayerB(i, "x", e.target.value)}      placeholder="X"    className="bg-white/5 border border-white/10 rounded px-2 py-1.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50" />
                        <input type="text" value={player.y}      onChange={(e) => updatePlayerB(i, "y", e.target.value)}      placeholder="Y"    className="bg-white/5 border border-white/10 rounded px-2 py-1.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Additional Settings & Demo Button */}
            <div className={`grid gap-6 ${showBall || showPasses || featureId !== 'formation' ? 'grid-cols-2' : 'max-w-xl'}`}>
              
              {(showBall || showPasses || featureId === "space-control" || featureId === "pass-network" || featureId === "press-resistance" || featureId === "patterns") && (
                <div
                  className="rounded-xl p-4 backdrop-blur-xl border border-white/10 flex flex-col justify-center"
                  style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}
                >
                  {showBall && (
                    <div className="flex items-center gap-4 mb-4">
                      <span className="text-sm font-medium text-white min-w-32">Ball Position:</span>
                      <input type="text" value={ballX} onChange={(e) => setBallX(e.target.value)} placeholder="X" className="w-24 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white placeholder-white/40 focus:outline-none focus:border-cyan-500/50" />
                      <input type="text" value={ballY} onChange={(e) => setBallY(e.target.value)} placeholder="Y" className="w-24 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white placeholder-white/40 focus:outline-none focus:border-cyan-500/50" />
                    </div>
                  )}
                  
                  {showPasses && (
                    <div className="mb-4">
                      <span className="text-sm font-medium text-white block mb-2">
                        {featureId === "press-resistance" ? "Pass Events (passer->receiver->1|0):" : "Pass Events (from_number->to_number):"}
                      </span>
                      <textarea
                        value={passesText}
                        onChange={(e) => setPassesText(e.target.value)}
                        placeholder={featureId === "press-resistance" ? "e.g. 4->8->1, 10->9->0" : "e.g. 4->8, 8->10, 10->9"}
                        rows={2}
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white placeholder-white/40 focus:outline-none focus:border-cyan-500/50"
                      />
                    </div>
                  )}

                  {featureId === "pass-network" && (
                    <div className="flex items-center gap-4 mb-2 mt-2">
                      <span className="text-sm font-medium text-white min-w-32">Min Passes:</span>
                      <input type="range" min="1" max="5" value={minPasses} onChange={(e) => setMinPasses(e.target.value)} className="flex-1 accent-cyan-500" />
                      <span className="text-sm text-cyan-400 font-bold w-4">{minPasses}</span>
                    </div>
                  )}

                  {featureId === "space-control" && (
                    <div className="flex items-center gap-4 mb-2 mt-2">
                      <span className="text-sm font-medium text-white min-w-32">Viz Mode:</span>
                      <select value={vizMode} onChange={(e) => setVizMode(e.target.value as any)} className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500/50">
                        <option value="Both">Both</option>
                        <option value="Voronoi">Voronoi Only</option>
                        <option value="Influence">Influence Only</option>
                      </select>
                    </div>
                  )}

                  {featureId === "press-resistance" && (
                     <div className="flex items-center gap-4 mb-2 mt-2">
                      <span className="text-sm font-medium text-white min-w-32">Pressure Radius:</span>
                      <input type="range" min="5" max="20" value={pressureRadius} onChange={(e) => setPressureRadius(e.target.value)} className="flex-1 accent-cyan-500" />
                      <span className="text-sm text-cyan-400 font-bold w-8">{pressureRadius}m</span>
                    </div>
                  )}

                  {featureId === "patterns" && (
                    <div className="flex items-center gap-4 mb-2 mt-2">
                      <span className="text-sm font-medium text-white min-w-32">Analyze Team:</span>
                      <select value={analyzeTeam} onChange={(e) => setAnalyzeTeam(e.target.value as any)} className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500/50">
                        <option value="Both">Both Teams</option>
                        <option value="Team A">Team A Only</option>
                        <option value="Team B">Team B Only</option>
                      </select>
                    </div>
                  )}
                </div>
              )}

              <div className="flex flex-col justify-center gap-4 items-center rounded-xl p-4 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
                <button
                  onClick={loadDemoData}
                  className="w-full max-w-xs px-6 py-3 rounded-lg bg-gradient-to-r from-yellow-500 to-orange-500 text-white font-medium hover:shadow-[0_0_30px_rgba(255,193,7,0.4)] transition-all"
                >
                  ⚡ Load El Clásico Demo
                </button>
                <p className="text-xs text-white/40 text-center">Auto-fills required data for {featureName}.</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* ── Video Tab ── */}
        {activeTab === "video" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            {/* Hidden real file input */}
            <input
              ref={videoInputRef}
              type="file"
              accept="video/mp4,video/avi,video/quicktime,.mp4,.avi,.mov"
              className="hidden"
              onChange={(e) => setVideoFile(e.target.files?.[0])}
            />
            <div
              onClick={() => videoInputRef.current?.click()}
              className="rounded-xl p-12 backdrop-blur-xl border-2 border-dashed border-white/20 text-center cursor-pointer hover:border-cyan-500/40 transition-all"
              style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.02) 0%, rgba(255, 255, 255, 0.01) 100%)" }}
            >
              <Upload className="w-16 h-16 text-white/40 mx-auto mb-4" />
              {videoFile ? (
                <h3 className="text-lg font-medium text-cyan-400 mb-2">✓ {videoFile.name}</h3>
              ) : (
                <>
                  <h3 className="text-lg font-medium text-white mb-2">Drop video file here</h3>
                  <p className="text-sm text-white/50">or click to browse (MP4, AVI, MOV)</p>
                </>
              )}
            </div>

            <div className="text-center text-white/40 font-medium">OR</div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">YouTube URL</label>
              <input
                type="text"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://youtube.com/watch?v=..."
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-white/40 focus:outline-none focus:border-cyan-500/50"
              />
            </div>
          </motion.div>
        )}

        {/* ── Dataset Tab ── */}
        {activeTab === "dataset" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            {/* Hidden real file input */}
            <input
              ref={datasetInputRef}
              type="file"
              accept=".csv,.json,text/csv,application/json"
              className="hidden"
              onChange={(e) => setDatasetFile(e.target.files?.[0])}
            />
            <div
              onClick={() => datasetInputRef.current?.click()}
              className="rounded-xl p-12 backdrop-blur-xl border-2 border-dashed border-white/20 text-center cursor-pointer hover:border-cyan-500/40 transition-all"
              style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.02) 0%, rgba(255, 255, 255, 0.01) 100%)" }}
            >
              <FileUp className="w-16 h-16 text-white/40 mx-auto mb-4" />
              {datasetFile ? (
                <h3 className="text-lg font-medium text-cyan-400 mb-2">✓ {datasetFile.name}</h3>
              ) : (
                <>
                  <h3 className="text-lg font-medium text-white mb-2">Drop dataset file here</h3>
                  <p className="text-sm text-white/50">or click to browse (CSV, JSON)</p>
                </>
              )}
            </div>
          </motion.div>
        )}

        {/* ── Analyze Button ── */}
        <motion.button
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          onClick={handleAnalyze}
          disabled={isLoading}
          className="w-full py-4 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold text-lg hover:shadow-[0_0_40px_rgba(76,175,80,0.4)] transition-all flex items-center justify-center gap-3 group disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Play className="w-6 h-6 group-hover:scale-110 transition-transform" />
              Analyze
            </>
          )}
        </motion.button>
      </div>
    </div>
  );
}
