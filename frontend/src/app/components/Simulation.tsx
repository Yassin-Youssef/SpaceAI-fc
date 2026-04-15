import { motion } from "motion/react";
import { Gamepad2, Play, ArrowLeft, Loader2 } from "lucide-react";
import { useState } from "react";
import { runSimulation } from "../../lib/api";
import type { SimulationResponse, SimulationRequest } from "../../lib/types";

const TACTICS = ["high_press", "low_block", "wide_play", "narrow_play", "counter_attack", "possession"];

export function Simulation() {
  const [showResults, setShowResults] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // States
  const [teamSize, setTeamSize] = useState(5);
  const [tacticA, setTacticA] = useState("possession");
  const [tacticB, setTacticB] = useState("low_block");
  const [steps, setSteps] = useState(300);

  const [results, setResults] = useState<SimulationResponse | null>(null);

  const handleAnalyze = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data: SimulationRequest = { team_size: teamSize, tactic_a: tacticA, tactic_b: tacticB, steps };
      const res = await runSimulation(data);
      setResults(res);
      setShowResults(true);
    } catch (e: any) {
      setError(e.message || "Simulation failed");
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  if (showResults && results) {
    return (
      <div className="h-full overflow-y-auto">
        <div className="max-w-4xl mx-auto p-8 space-y-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-4">
            <button onClick={() => setShowResults(false)} className="p-2 rounded-lg bg-white/5 border border-white/10 text-white/60 hover:text-white hover:bg-white/10 transition-all">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h2 className="text-2xl font-bold text-white">Simulation Results</h2>
          </motion.div>

          <div className="grid grid-cols-2 gap-6">
            <div className="rounded-xl p-6 backdrop-blur-xl border border-cyan-500/30 text-center" style={{ background: "linear-gradient(135deg, rgba(0, 217, 255, 0.12) 0%, rgba(0, 217, 255, 0.05) 100%)" }}>
              <h3 className="text-xl font-bold text-cyan-400 mb-2 capitalize">{results.tactic_a.replace("_", " ")}</h3>
              <div className="text-6xl font-black text-white">{results.goals_a}</div>
              <div className="text-sm text-cyan-400/80 mt-2">Goals</div>
              <div className="mt-6 flex justify-between text-sm">
                <span className="text-white/60">Possession</span>
                <span className="text-white font-bold">{results.possession_a}%</span>
              </div>
              <div className="mt-2 flex justify-between text-sm">
                <span className="text-white/60">Territorial Control</span>
                <span className="text-white font-bold">{results.territorial_control_a}%</span>
              </div>
            </div>

            <div className="rounded-xl p-6 backdrop-blur-xl border border-red-500/30 text-center" style={{ background: "linear-gradient(135deg, rgba(255, 71, 87, 0.12) 0%, rgba(255, 71, 87, 0.05) 100%)" }}>
              <h3 className="text-xl font-bold text-red-400 mb-2 capitalize">{results.tactic_b.replace("_", " ")}</h3>
              <div className="text-6xl font-black text-white">{results.goals_b}</div>
              <div className="text-sm text-red-400/80 mt-2">Goals</div>
              <div className="mt-6 flex justify-between text-sm">
                <span className="text-white/60">Possession</span>
                <span className="text-white font-bold">{results.possession_b}%</span>
              </div>
              <div className="mt-2 flex justify-between text-sm">
                <span className="text-white/60">Territorial Control</span>
                <span className="text-white font-bold">{(100 - results.territorial_control_a).toFixed(1)}%</span>
              </div>
            </div>
          </div>

          <div className="rounded-xl p-6 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
            <h3 className="text-lg font-bold text-white mb-4">Event Log Snippet</h3>
            <div className="space-y-2 h-64 overflow-y-auto">
              {results.events.slice(0, 15).map((ev: any, i) => (
                <div key={i} className="text-sm text-white/70 bg-white/5 p-2 rounded border border-white/10">
                  Step {ev.step}: <span className="font-semibold text-white">{ev.event}</span> by Team {ev.team} Player {ev.player}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // --- Input Form ---
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto p-8 space-y-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="relative rounded-xl p-6 backdrop-blur-xl border border-cyan-500/30" style={{ background: "linear-gradient(135deg, rgba(0, 217, 255, 0.12) 0%, rgba(0, 217, 255, 0.05) 100%)" }}>
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_30px_rgba(0,217,255,0.4)]">
              <Gamepad2 className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Tactical Simulation</h1>
              <p className="text-white/60">Simulate a small-sided match with custom tactics to see hypothetical outcomes.</p>
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
            <h3 className="text-lg font-bold text-white">Team Tactics</h3>
            
            <label className="block">
              <span className="text-sm text-cyan-400 font-medium block mb-2">Team A Tactic</span>
              <select value={tacticA} onChange={e => setTacticA(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-cyan-500/50">
                {TACTICS.map(t => <option key={`a-${t}`} value={t} className="bg-gray-900 capitalize">{t.replace("_", " ")}</option>)}
              </select>
            </label>

            <label className="block mt-4">
              <span className="text-sm text-red-400 font-medium block mb-2">Team B Tactic</span>
              <select value={tacticB} onChange={e => setTacticB(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-red-400/50">
                {TACTICS.map(t => <option key={`b-${t}`} value={t} className="bg-gray-900 capitalize">{t.replace("_", " ")}</option>)}
              </select>
            </label>
          </div>

          <div className="space-y-4 rounded-xl p-6 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
            <h3 className="text-lg font-bold text-white">Simulation Setup</h3>
            
            <label className="block mt-4">
              <span className="text-sm text-white/70 block mb-2">Team Size ({teamSize}v{teamSize})</span>
              <input type="range" min="5" max="7" value={teamSize} onChange={e => setTeamSize(parseInt(e.target.value))} className="w-full accent-cyan-400" />
            </label>

            <label className="block mt-6">
              <span className="text-sm text-white/70 block mb-2">Simulation Steps ({steps})</span>
              <input type="range" min="100" max="1000" step="50" value={steps} onChange={e => setSteps(parseInt(e.target.value))} className="w-full accent-cyan-400" />
            </label>
          </div>
        </div>

        <motion.button onClick={handleAnalyze} disabled={isLoading} className="w-full py-4 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold text-lg hover:shadow-[0_0_40px_rgba(76,175,80,0.4)] transition-all flex items-center justify-center gap-3 disabled:opacity-70 disabled:cursor-not-allowed">
          {isLoading ? <><Loader2 className="w-6 h-6 animate-spin" /> Running...</> : <><Play className="w-6 h-6" /> Run Match Simulation</>}
        </motion.button>
      </div>
    </div>
  );
}
