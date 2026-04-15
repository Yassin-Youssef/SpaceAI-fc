import { motion } from "motion/react";
import { GitCompare, Play, ArrowLeft, Loader2 } from "lucide-react";
import { useState } from "react";
import { compareSimulations } from "../../lib/api";
import type { SimulationCompareResponse, SimulationCompareRequest } from "../../lib/types";

const TACTICS = ["high_press", "low_block", "wide_play", "narrow_play", "counter_attack", "possession"];

export function Compare() {
  const [showResults, setShowResults] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // States
  const [teamSize, setTeamSize] = useState(5);
  const [tacticA, setTacticA] = useState("possession");
  const [tacticB, setTacticB] = useState("low_block");
  const [tacticA2, setTacticA2] = useState("high_press");
  const [tacticB2, setTacticB2] = useState("counter_attack");
  const [runs, setRuns] = useState(3);
  const [steps, setSteps] = useState(300);

  const [results, setResults] = useState<SimulationCompareResponse | null>(null);

  const handleAnalyze = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data: SimulationCompareRequest = { 
        team_size: teamSize, 
        tactic_a: tacticA, 
        tactic_b: tacticB, 
        tactic_a2: tacticA2, 
        tactic_b2: tacticB2,
        runs,
        steps_per_run: steps
      };
      const res = await compareSimulations(data);
      setResults(res);
      setShowResults(true);
    } catch (e: any) {
      setError(e.message || "Compare failed");
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  if (showResults && results) {
    const m1 = results.matchup_1 as any;
    const m2 = results.matchup_2 as any;
    return (
      <div className="h-full overflow-y-auto">
        <div className="max-w-6xl mx-auto p-8 space-y-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-4">
            <button onClick={() => setShowResults(false)} className="p-2 rounded-lg bg-white/5 border border-white/10 text-white/60 hover:text-white hover:bg-white/10 transition-all">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h2 className="text-2xl font-bold text-white">Comparison Results</h2>
          </motion.div>

          {/* Verdict */}
          <div className="rounded-xl p-6 bg-gradient-to-r from-blue-900/40 to-purple-900/40 border border-blue-500/30 text-center">
             <h3 className="text-xl font-bold text-white leading-relaxed tracking-wide">
               {results.verdict}
             </h3>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="rounded-xl p-6 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
               <h3 className="text-lg font-bold text-cyan-400 mb-4 text-center border-b border-white/10 pb-2">
                 Matchup 1: <span className="capitalize text-white">{m1.tactic_a.replace("_"," ")}</span> vs <span className="capitalize text-white">{m1.tactic_b.replace("_"," ")}</span>
               </h3>
               <div className="space-y-4">
                 <div className="flex justify-between items-center text-sm">
                   <span className="text-white/60">Avg Goals (A vs B)</span>
                   <span className="text-white font-bold">{m1.avg_goals_a} : {m1.avg_goals_b}</span>
                 </div>
                 <div className="flex justify-between items-center text-sm">
                   <span className="text-white/60">Possession A</span>
                   <span className="text-white font-bold">{m1.avg_possession_a}%</span>
                 </div>
                 <div className="flex justify-between items-center text-sm">
                   <span className="text-white/60">Territorial Control A</span>
                   <span className="text-white font-bold">{m1.avg_territorial_control_a}%</span>
                 </div>
               </div>
            </div>

            <div className="rounded-xl p-6 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
               <h3 className="text-lg font-bold text-red-400 mb-4 text-center border-b border-white/10 pb-2">
                 Matchup 2: <span className="capitalize text-white">{m2.tactic_a.replace("_"," ")}</span> vs <span className="capitalize text-white">{m2.tactic_b.replace("_"," ")}</span>
               </h3>
               <div className="space-y-4">
                 <div className="flex justify-between items-center text-sm">
                   <span className="text-white/60">Avg Goals (A vs B)</span>
                   <span className="text-white font-bold">{m2.avg_goals_a} : {m2.avg_goals_b}</span>
                 </div>
                 <div className="flex justify-between items-center text-sm">
                   <span className="text-white/60">Possession A</span>
                   <span className="text-white font-bold">{m2.avg_possession_a}%</span>
                 </div>
                 <div className="flex justify-between items-center text-sm">
                   <span className="text-white/60">Territorial Control A</span>
                   <span className="text-white font-bold">{m2.avg_territorial_control_a}%</span>
                 </div>
               </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // --- Input Form ---
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto p-8 space-y-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="relative rounded-xl p-6 backdrop-blur-xl border border-cyan-500/30" style={{ background: "linear-gradient(135deg, rgba(0, 217, 255, 0.12) 0%, rgba(0, 217, 255, 0.05) 100%)" }}>
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_30px_rgba(0,217,255,0.4)]">
              <GitCompare className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Compare Matchups</h1>
              <p className="text-white/60">Run side-by-side tactical simulations to see which setup yields better results.</p>
            </div>
          </div>
        </motion.div>

        {error && (
          <div className="rounded-xl p-4 bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            ⚠ {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-4 rounded-xl p-6 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
            <h3 className="text-lg font-bold text-cyan-400 mb-2 border-b border-white/10 pb-2">Matchup 1</h3>
            <label className="block">
              <span className="text-sm text-white/70 font-medium block mb-2">Team A Tactic</span>
              <select value={tacticA} onChange={e => setTacticA(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-cyan-500/50">
                {TACTICS.map(t => <option key={`m1a-${t}`} value={t} className="bg-gray-900 capitalize">{t.replace("_", " ")}</option>)}
              </select>
            </label>
            <label className="block mt-4">
              <span className="text-sm text-white/70 font-medium block mb-2">Team B Tactic</span>
              <select value={tacticB} onChange={e => setTacticB(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-cyan-500/50">
                {TACTICS.map(t => <option key={`m1b-${t}`} value={t} className="bg-gray-900 capitalize">{t.replace("_", " ")}</option>)}
              </select>
            </label>
          </div>

          <div className="space-y-4 rounded-xl p-6 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
             <h3 className="text-lg font-bold text-red-400 mb-2 border-b border-white/10 pb-2">Matchup 2</h3>
            <label className="block">
              <span className="text-sm text-white/70 font-medium block mb-2">Team A Tactic</span>
              <select value={tacticA2} onChange={e => setTacticA2(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-red-400/50">
                {TACTICS.map(t => <option key={`m2a-${t}`} value={t} className="bg-gray-900 capitalize">{t.replace("_", " ")}</option>)}
              </select>
            </label>
            <label className="block mt-4">
              <span className="text-sm text-white/70 font-medium block mb-2">Team B Tactic</span>
              <select value={tacticB2} onChange={e => setTacticB2(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-red-400/50">
                {TACTICS.map(t => <option key={`m2b-${t}`} value={t} className="bg-gray-900 capitalize">{t.replace("_", " ")}</option>)}
              </select>
            </label>
          </div>
        </div>

        <div className="rounded-xl p-6 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
           <h3 className="text-lg font-bold text-white mb-4">Settings</h3>
           <div className="grid grid-cols-3 gap-6">
             <label className="block">
               <span className="text-sm text-white/70 block mb-2">Team Size ({teamSize}v{teamSize})</span>
               <input type="range" min="5" max="7" value={teamSize} onChange={e => setTeamSize(parseInt(e.target.value))} className="w-full accent-cyan-400" />
             </label>
             <label className="block">
               <span className="text-sm text-white/70 block mb-2">Runs per Matchup ({runs})</span>
               <input type="range" min="1" max="10" value={runs} onChange={e => setRuns(parseInt(e.target.value))} className="w-full accent-cyan-400" />
             </label>
             <label className="block">
               <span className="text-sm text-white/70 block mb-2">Steps per run ({steps})</span>
               <input type="range" min="100" max="1000" step="50" value={steps} onChange={e => setSteps(parseInt(e.target.value))} className="w-full accent-cyan-400" />
             </label>
           </div>
        </div>

        <motion.button onClick={handleAnalyze} disabled={isLoading} className="w-full py-4 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold text-lg hover:shadow-[0_0_40px_rgba(76,175,80,0.4)] transition-all flex items-center justify-center gap-3 disabled:opacity-70 disabled:cursor-not-allowed">
          {isLoading ? <><Loader2 className="w-6 h-6 animate-spin" /> Comparing...</> : <><Play className="w-6 h-6" /> Run Comparison</>}
        </motion.button>
      </div>
    </div>
  );
}
