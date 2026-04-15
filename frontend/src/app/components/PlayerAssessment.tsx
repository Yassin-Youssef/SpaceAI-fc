import { motion } from "motion/react";
import { User, Play, ArrowLeft, Loader2, Video, Database, SlidersHorizontal } from "lucide-react";
import { useState } from "react";
import { assessPlayer } from "../../lib/api";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";

export function PlayerAssessment() {
  const [showResults, setShowResults] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Tabs: "video" | "data" | "manual"
  const [inputType, setInputType] = useState<"video" | "data" | "manual">("data");

  // Basic Bio
  const [name, setName] = useState("Lamine Yamal");
  const [number, setNumber] = useState("19");
  const [age, setAge] = useState("16");
  const [foot, setFoot] = useState("Left");
  const [height, setHeight] = useState("180cm");
  const [weight, setWeight] = useState("72kg");

  // Video Mode
  const [youtubeUrl, setYoutubeUrl] = useState("https://youtube.com/watch?v=abcd");

  // Data Mode
  const [stats, setStats] = useState({
    passes_completed: 45,
    passes_attempted: 52,
    tackles: 3,
    interceptions: 2,
    shots: 4,
    dribbles: 7,
    aerial_duels: 1,
    distance_covered: 10.5,
    sprints: 22
  });

  // Manual Mode Fallback
  const [speed, setSpeed] = useState(88);
  const [acceleration, setAcceleration] = useState(92);
  const [stamina, setStamina] = useState(80);
  const [passing, setPassing] = useState(85);
  const [dribbling, setDribbling] = useState(94);
  const [shooting, setShooting] = useState(82);

  // Results
  const [role, setRole] = useState("Unknown");
  const [scoutingReport, setScoutingReport] = useState("");
  const [strengths, setStrengths] = useState<string[]>([]);
  const [weaknesses, setWeaknesses] = useState<string[]>([]);
  const [radarData, setRadarData] = useState<any[]>([]);

  const handleAnalyze = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload: any = {
        name,
        number: parseInt(number) || 0,
        age: parseInt(age) || 0,
        preferred_foot: foot,
        height,
        weight,
        input_type: inputType
      };

      if (inputType === "video") {
        payload.youtube_url = youtubeUrl;
      } else if (inputType === "data") {
        payload.stats = stats;
      } else {
        payload.manual_attributes = {
          Speed: speed,
          Acceleration: acceleration,
          Stamina: stamina,
          Passing: passing,
          Dribbling: dribbling,
          Shooting: shooting
        };
      }

      const res = await assessPlayer(payload);
      
      setRole(res.recommended_role || "Unknown Role");
      setScoutingReport(res.scouting_report || "Report generation failed.");
      setStrengths(res.strengths || []);
      setWeaknesses(res.weaknesses || []);

      if (res.radar_data) {
        const mappedRadar = Object.entries(res.radar_data).map(([k, v]) => ({
          subject: k, A: v, fullMark: 100
        }));
        setRadarData(mappedRadar);
      }
      
      setShowResults(true);
    } catch (e: any) {
      console.error(e);
      setError(e.message || "Assessment Engine failed.");
    } finally {
      setIsLoading(false);
    }
  };

  if (showResults) {
    return (
      <div className="h-full overflow-y-auto w-full">
        <div className="max-w-7xl mx-auto p-8 space-y-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-4">
            <button onClick={() => setShowResults(false)} className="p-2 rounded-lg bg-white/5 border border-white/10 text-white/60 hover:text-white hover:bg-white/10 transition-all">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h2 className="text-2xl font-bold text-white">Scouting & Tactical Profile</h2>
          </motion.div>

          {/* Results Grid */}
          <div className="grid grid-cols-3 gap-6">
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="col-span-1 rounded-xl p-6 backdrop-blur-xl border border-cyan-500/30" style={{ background: "linear-gradient(135deg, rgba(0, 217, 255, 0.12) 0%, rgba(0, 217, 255, 0.05) 100%)" }}>
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-4xl font-bold text-white mb-4 mx-auto border-4 border-white/10 shadow-[0_0_20px_rgba(0,217,255,0.3)]">
                {number}
              </div>
              <h3 className="text-2xl font-bold text-white text-center mb-1">{name}</h3>
              <p className="text-cyan-400 font-medium text-center mb-6">{role}</p>
              
              <div className="space-y-3 text-sm">
                <div className="flex justify-between border-b border-white/10 pb-2"><span className="text-white/50">Age</span><span className="text-white font-medium">{age}</span></div>
                <div className="flex justify-between border-b border-white/10 pb-2"><span className="text-white/50">Build</span><span className="text-white font-medium">{height} / {weight}</span></div>
                <div className="flex justify-between border-b border-white/10 pb-2"><span className="text-white/50">Foot</span><span className="text-white font-medium">{foot}</span></div>
                <div className="flex justify-between border-b border-white/10 pb-2"><span className="text-white/50">Input Source</span><span className="text-white font-bold capitalize">{inputType} Analysis</span></div>
              </div>

              {strengths.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-white font-bold mb-2 text-sm uppercase tracking-wider text-green-400">Key Strengths</h4>
                  <ul className="space-y-1">
                    {strengths.map((s, i) => <li key={i} className="text-white/80 text-sm flex gap-2"><span className="text-green-500">•</span> {s}</li>)}
                  </ul>
                </div>
              )}
               {weaknesses.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-white font-bold mb-2 text-sm uppercase tracking-wider text-red-400">Areas to Improve</h4>
                  <ul className="space-y-1">
                    {weaknesses.map((w, i) => <li key={i} className="text-white/80 text-sm flex gap-2"><span className="text-red-500">•</span> {w}</li>)}
                  </ul>
                </div>
              )}
            </motion.div>

            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 }} className="col-span-2 rounded-xl p-6 backdrop-blur-xl border border-white/10 flex items-center justify-center relative overflow-hidden" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
               {/* Radar Chart dynamically generated by backend algorithm */}
               <div className="absolute top-4 left-4 text-white/50 text-xs font-mono uppercase tracking-widest px-3 py-1 bg-white/5 rounded-full border border-white/10">Dynamic Assessment Output</div>
               <div className="w-full aspect-[4/3] max-h-[400px]">
                 <ResponsiveContainer width="100%" height="100%">
                   <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                     <PolarGrid stroke="rgba(255,255,255,0.2)" />
                     <PolarAngleAxis dataKey="subject" tick={{ fill: "rgba(255,255,255,0.7)", fontSize: 13, fontWeight: 500 }} />
                     <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                     <Radar name={name} dataKey="A" stroke="#00d9ff" strokeWidth={3} fill="#00d9ff" fillOpacity={0.4} />
                   </RadarChart>
                 </ResponsiveContainer>
               </div>
            </motion.div>
          </div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="rounded-xl p-8 backdrop-blur-xl border border-white/10 shadow-2xl" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-3"><User className="w-6 h-6 text-cyan-400" /> Professional Scouting Report</h3>
            <p className="text-white/80 leading-relaxed font-serif text-lg">{scoutingReport}</p>
          </motion.div>
        </div>
      </div>
    );
  }

  // --- Input Form ---
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto p-8 space-y-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="relative rounded-xl p-6 backdrop-blur-xl border border-cyan-500/30 overflow-hidden" style={{ background: "linear-gradient(135deg, rgba(0, 217, 255, 0.12) 0%, rgba(0, 217, 255, 0.05) 100%)" }}>
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_30px_rgba(0,217,255,0.4)]">
              <User className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Player Assessment</h1>
              <p className="text-white/60">Provide raw video or match data, and the tactical engine will extract the player\'s optimum role.</p>
            </div>
          </div>
        </motion.div>

        {error && (
          <div className="rounded-xl p-4 bg-red-500/10 border border-red-500/30 text-red-400 text-sm">⚠ {error}</div>
        )}

        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-1 space-y-4 rounded-xl p-6 backdrop-blur-xl border border-white/10" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
            <h3 className="text-lg font-bold text-white mb-4">Bio</h3>
            <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Player Name" className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-white/40 focus:outline-none focus:border-cyan-500/50" />
            <input type="number" value={number} onChange={e => setNumber(e.target.value)} placeholder="Number (e.g. 10)" className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-cyan-500/50" />
            <div className="grid grid-cols-2 gap-3">
              <input type="number" value={age} onChange={e => setAge(e.target.value)} placeholder="Age" className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-cyan-500/50" />
              <select value={foot} onChange={e => setFoot(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-cyan-500/50">
                 <option value="Right">Right</option>
                 <option value="Left">Left</option>
                 <option value="Both">Both</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
               <input type="text" value={height} onChange={e => setHeight(e.target.value)} placeholder="180cm" className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-2 text-white focus:border-cyan-500/50 text-sm" />
               <input type="text" value={weight} onChange={e => setWeight(e.target.value)} placeholder="75kg" className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-2 text-white focus:border-cyan-500/50 text-sm" />
            </div>
          </div>

          <div className="col-span-2 space-y-4 rounded-xl p-0 backdrop-blur-xl border border-white/10 flex flex-col" style={{ background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)" }}>
            {/* Tab navigation */}
            <div className="flex border-b border-white/10">
              <button onClick={() => setInputType("video")} className={`flex-1 py-4 flex items-center justify-center gap-2 font-bold transition-all ${inputType === "video" ? "text-cyan-400 border-b-2 border-cyan-400 bg-white/5" : "text-white/50 hover:text-white/80"}`}><Video className="w-5 h-5"/> Video CV</button>
              <button onClick={() => setInputType("data")} className={`flex-1 py-4 flex items-center justify-center gap-2 font-bold transition-all ${inputType === "data" ? "text-cyan-400 border-b-2 border-cyan-400 bg-white/5" : "text-white/50 hover:text-white/80"}`}><Database className="w-5 h-5"/> Match Data</button>
              <button onClick={() => setInputType("manual")} className={`flex-1 py-4 flex items-center justify-center gap-2 font-bold transition-all ${inputType === "manual" ? "text-cyan-400 border-b-2 border-cyan-400 bg-white/5" : "text-white/50 hover:text-white/80"}`}><SlidersHorizontal className="w-5 h-5"/> Manual Setup</button>
            </div>

            <div className="p-6 flex-1">
              {inputType === "video" && (
                <div className="space-y-4 text-sm text-white/70">
                  <p>Provide a YouTube URL of the player\'s highlights. Deepmind YOLOv8 models will track movement and heatmaps automatically to gauge their tactical role.</p>
                  <label className="block mt-4">
                     <span className="text-sm font-bold text-white mb-2 block">YouTube Analysis URL</span>
                     <input type="text" value={youtubeUrl} onChange={e => setYoutubeUrl(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-500/50 font-mono" />
                  </label>
                  <div className="rounded-xl p-4 bg-yellow-500/10 border border-yellow-500/30 text-yellow-400/80">
                     Phase 4 Tracking is computationally intensive. Analysis may take up to 60 seconds depending on frame resolution.
                  </div>
                </div>
              )}

              {inputType === "data" && (
                <div className="space-y-4">
                  <p className="text-sm text-white/70 pb-2 border-b border-white/10 mb-4">Input raw statistical counts. The Knowledge Graph will categorize player profiles objectively.</p>
                  <div className="grid grid-cols-2 gap-4">
                    <label className="flex flex-col"><span className="text-xs text-white/50 mb-1">Passes Completed / Attempted</span>
                     <div className="flex gap-2"><input type="number" value={stats.passes_completed} onChange={e => setStats({...stats, passes_completed: +e.target.value})} className="w-full bg-white/5 border border-white/10 rounded px-3 py-1 text-white"/> <span className="text-white/30 pt-1">/</span> <input type="number" value={stats.passes_attempted} onChange={e => setStats({...stats, passes_attempted: +e.target.value})} className="w-full bg-white/5 border border-white/10 rounded px-3 py-1 text-white"/></div>
                    </label>
                    <label className="flex flex-col"><span className="text-xs text-white/50 mb-1">Tackles / Interceptions</span>
                     <div className="flex gap-2"><input type="number" value={stats.tackles} onChange={e => setStats({...stats, tackles: +e.target.value})} className="w-full bg-white/5 border border-white/10 rounded px-3 py-1 text-white"/> <span className="text-white/30 pt-1">/</span> <input type="number" value={stats.interceptions} onChange={e => setStats({...stats, interceptions: +e.target.value})} className="w-full bg-white/5 border border-white/10 rounded px-3 py-1 text-white"/></div>
                    </label>
                    <label className="flex flex-col"><span className="text-xs text-white/50 mb-1">Shots / Dribbles</span>
                     <div className="flex gap-2"><input type="number" value={stats.shots} onChange={e => setStats({...stats, shots: +e.target.value})} className="w-full bg-white/5 border border-white/10 rounded px-3 py-1 text-white"/> <span className="text-white/30 pt-1">/</span> <input type="number" value={stats.dribbles} onChange={e => setStats({...stats, dribbles: +e.target.value})} className="w-full bg-white/5 border border-white/10 rounded px-3 py-1 text-white"/></div>
                    </label>
                    <label className="flex flex-col"><span className="text-xs text-white/50 mb-1">Distance (km) / Sprints</span>
                     <div className="flex gap-2"><input type="number" step="0.1" value={stats.distance_covered} onChange={e => setStats({...stats, distance_covered: +e.target.value})} className="w-full bg-white/5 border border-white/10 rounded px-3 py-1 text-white"/> <span className="text-white/30 pt-1">&</span> <input type="number" value={stats.sprints} onChange={e => setStats({...stats, sprints: +e.target.value})} className="w-full bg-white/5 border border-white/10 rounded px-3 py-1 text-white"/></div>
                    </label>
                  </div>
                </div>
              )}

              {inputType === "manual" && (
                <div className="space-y-4">
                  <p className="text-sm text-white/70 mb-4 pb-2 border-b border-white/10">Legacy sliding scale fallback for quick hypothetical player generation.</p>
                  {[
                    { label: "Speed", value: speed, setter: setSpeed },
                    { label: "Acceleration", value: acceleration, setter: setAcceleration },
                    { label: "Stamina", value: stamina, setter: setStamina },
                    { label: "Passing", value: passing, setter: setPassing },
                    { label: "Dribbling", value: dribbling, setter: setDribbling },
                    { label: "Shooting", value: shooting, setter: setShooting },
                  ].map(attr => (
                    <div key={attr.label} className="flex items-center gap-4">
                      <span className="w-24 text-sm text-white/70">{attr.label}</span>
                      <input type="range" min="0" max="100" value={attr.value} onChange={e => attr.setter(parseInt(e.target.value))} className="flex-1 accent-cyan-400" />
                      <span className="w-8 text-right text-sm text-cyan-400 font-bold">{attr.value}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <motion.button
          onClick={handleAnalyze}
          disabled={isLoading}
          className="w-full py-4 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold text-lg hover:shadow-[0_0_40px_rgba(76,175,80,0.4)] transition-all flex items-center justify-center gap-3 disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {isLoading ? <><Loader2 className="w-6 h-6 animate-spin" /> Autonomous Assessment Running...</> : <><Play className="w-6 h-6" /> Run Tactical Diagnostics</>}
        </motion.button>
      </div>
    </div>
  );
}
