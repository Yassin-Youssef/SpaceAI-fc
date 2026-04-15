import { motion } from "motion/react";
import { Lightbulb, Play, ArrowLeft, Loader2 } from "lucide-react";
import { useState } from "react";
import { post } from "../../lib/api-fetch";

// We'll call the intelligence endpoint manually or ask backend directly
export function Strategy() {
  const [showResults, setShowResults] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formation, setFormation] = useState("4-3-3");
  const [situation, setSituation] = useState("against low block");
  const [recommendations, setRecommendations] = useState<any[]>([]);

  const handleAnalyze = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Direct call to /api/ask to query the Knowledge Graph since it handles standalone queries
      const res = await fetch("http://localhost:8000/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: `What is the best strategy for ${formation} ${situation}?`, team_name: "Team", opponent_name: "Opponent" })
      });
      if (!res.ok) throw new Error("Failed to fetch strategy.");
      const data = await res.json();
      
      // Parse the 'answer' into a list of points (roughly)
      const points = data.answer.split('\n').filter((l: string) => l.trim().length > 0).map((l: string) => l.replace(/^[-\*\d\.]+/, '').trim());
      setRecommendations(points);
      setShowResults(true);
    } catch (e: any) {
      setError(e.message || "Strategy generation failed");
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
            <h2 className="text-2xl font-bold text-white">Strategy Recommendations</h2>
          </motion.div>

          <div className="rounded-xl p-8 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
            <h3 className="text-xl font-bold text-cyan-400 mb-6">Strategy: {formation} {situation}</h3>
            <ul className="space-y-4">
              {recommendations.map((rec, i) => (
                <motion.li key={i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }} className="flex items-start gap-4 p-4 rounded-lg bg-white/5 border border-white/10">
                  <div className="w-8 h-8 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0 font-bold">{i + 1}</div>
                  <p className="text-white/90 leading-relaxed text-sm mt-1">{rec}</p>
                </motion.li>
              ))}
            </ul>
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
              <Lightbulb className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Strategy Recommendations</h1>
              <p className="text-white/60">Standalone recommendations based on the Football Knowledge Graph.</p>
            </div>
          </div>
        </motion.div>

        {error && (
          <div className="rounded-xl p-4 bg-red-500/10 border border-red-500/30 text-red-400 text-sm">⚠ {error}</div>
        )}

        <div className="grid grid-cols-2 gap-6">
          <div className="rounded-xl p-6 backdrop-blur-xl border border-white/10 space-y-4" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
             <label className="block">
               <span className="text-sm text-white/70 font-medium block mb-2">Team Formation</span>
               <select value={formation} onChange={e => setFormation(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-cyan-500/50">
                 {["4-3-3", "4-2-3-1", "3-5-2", "4-4-2", "3-4-2-1"].map(f => <option key={f} value={f} className="bg-gray-900">{f}</option>)}
               </select>
             </label>
          </div>
          <div className="rounded-xl p-6 backdrop-blur-xl border border-white/10 space-y-4" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
             <label className="block">
               <span className="text-sm text-white/70 font-medium block mb-2">Match Situation</span>
               <select value={situation} onChange={e => setSituation(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-cyan-500/50">
                 {["against low block", "against high press", "chasing a game", "defending a lead", "counter attacking"].map(s => <option key={s} value={s} className="bg-gray-900 capitalize">{s}</option>)}
               </select>
             </label>
          </div>
        </div>

        <motion.button onClick={handleAnalyze} disabled={isLoading} className="w-full py-4 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold text-lg hover:shadow-[0_0_40px_rgba(76,175,80,0.4)] transition-all flex items-center justify-center gap-3 disabled:opacity-70 disabled:cursor-not-allowed">
          {isLoading ? <><Loader2 className="w-6 h-6 animate-spin" /> Querying Graph...</> : <><Play className="w-6 h-6" /> Get Recommendations</>}
        </motion.button>
      </div>
    </div>
  );
}
