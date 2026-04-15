import { motion } from "motion/react";
import { FileText, Play, ArrowLeft, Loader2 } from "lucide-react";
import { useState } from "react";
import { analyzeFeature } from "../../lib/api";

export function Explanation() {
  const [showResults, setShowResults] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // States
  const [teamName, setTeamName] = useState("FC Barcelona");
  const [opponentName, setOpponentName] = useState("Real Madrid");
  const [mode, setMode] = useState<"template" | "llm">("llm");
  
  // Results
  const [reportText, setReportText] = useState("");

  const handleAnalyze = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Re-use analyzeFeature structure but we intercept the payload inside it, Or just call /api/explanation!
      // To strictly follow the backend let's use fetch directly for our custom payload if api.ts differs
      const res = await fetch("http://localhost:8000/api/explanation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode,
          match_info: { score: "2-1", possession: "60%" },
          report_data: { xG: "1.5 vs 0.8", shots: 15 },
          swot_results: { strengths: ["High press"], weaknesses: ["Vulnerable to counters"] },
          recommendations: ["Maintain high line", "Drop CDM deeper"],
          team_name: teamName,
          opponent_name: opponentName,
        })
      });
      if (!res.ok) throw new Error("Explanation request failed");
      const data = await res.json();
      
      setReportText(data.text || data.sections?.join("\n\n") || "No explanation generated.");
      setShowResults(true);
    } catch (e: any) {
      setError(e.message || "Explanation failed");
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  if (showResults) {
    return (
      <div className="h-full overflow-y-auto">
        <div className="max-w-4xl mx-auto p-8 space-y-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-4">
            <button onClick={() => setShowResults(false)} className="p-2 rounded-lg bg-white/5 border border-white/10 text-white/60 hover:text-white hover:bg-white/10 transition-all">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h2 className="text-2xl font-bold text-white">Tactical Explanation</h2>
          </motion.div>

          <div className="rounded-xl p-8 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
             <h3 className="text-xl font-bold text-cyan-400 mb-6">Generated Report ({mode.toUpperCase()} Mode)</h3>
             <div className="text-white/90 leading-relaxed whitespace-pre-wrap font-serif text-lg">
               {reportText}
             </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto p-8 space-y-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="relative rounded-xl p-6 backdrop-blur-xl border border-cyan-500/30" style={{ background: "linear-gradient(135deg, rgba(0, 217, 255, 0.12) 0%, rgba(0, 217, 255, 0.05) 100%)" }}>
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_30px_rgba(0,217,255,0.4)]">
              <FileText className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Tactical Explanation</h1>
              <p className="text-white/60">Generate natural language match reports using LLMs or templates.</p>
            </div>
          </div>
        </motion.div>

        {error && (
          <div className="rounded-xl p-4 bg-red-500/10 border border-red-500/30 text-red-400 text-sm">⚠ {error}</div>
        )}

        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-4 rounded-xl p-6 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
             <h3 className="text-lg font-bold text-white mb-2 pb-2 border-b border-white/10">Match Info</h3>
             <label className="block">
               <span className="text-sm text-cyan-400 font-medium block mb-2">Your Team</span>
               <input type="text" value={teamName} onChange={e => setTeamName(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-cyan-500/50" />
             </label>
             <label className="block mt-4">
               <span className="text-sm text-red-400 font-medium block mb-2">Opponent</span>
               <input type="text" value={opponentName} onChange={e => setOpponentName(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-red-400/50" />
             </label>
          </div>

          <div className="space-y-4 rounded-xl p-6 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
             <h3 className="text-lg font-bold text-white mb-2 pb-2 border-b border-white/10">Engine Settings</h3>
             <label className="block">
               <span className="text-sm text-white/70 font-medium block mb-2">Explanation Mode</span>
               <select value={mode} onChange={e => setMode(e.target.value as any)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-cyan-500/50">
                 <option value="llm" className="bg-gray-900">LLM Mode (OpenRouter)</option>
                 <option value="template" className="bg-gray-900">Template Mode (Offline)</option>
               </select>
             </label>
             <div className="mt-4 text-xs text-white/40">
               If an OPENROUTER_API_KEY is detected inside the engine, LLM mode will provide a rich, narrative explanation. Template mode generates deterministic summaries without needing AI.
             </div>
          </div>
        </div>

        <motion.button onClick={handleAnalyze} disabled={isLoading} className="w-full py-4 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold text-lg hover:shadow-[0_0_40px_rgba(76,175,80,0.4)] transition-all flex items-center justify-center gap-3 disabled:opacity-70 disabled:cursor-not-allowed">
          {isLoading ? <><Loader2 className="w-6 h-6 animate-spin" /> Generating...</> : <><Play className="w-6 h-6" /> Generate Explanation</>}
        </motion.button>
      </div>
    </div>
  );
}
