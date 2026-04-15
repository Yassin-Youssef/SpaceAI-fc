import { motion } from "motion/react";
import { useState } from "react";
import { FormationBadge } from "./FormationBadge";

interface Player {
  id: number;
  x: number;
  y: number;
  name: string;
  number: number;
  team: "home" | "away";
}

interface PassConnection {
  from: number;
  to: number;
  strength: number;
}

const mockPlayers: Player[] = [
  // Home team (4-3-3)
  { id: 1, x: 10, y: 50, name: "GK", number: 1, team: "home" },
  { id: 2, x: 25, y: 20, name: "RB", number: 2, team: "home" },
  { id: 3, x: 25, y: 40, name: "CB", number: 4, team: "home" },
  { id: 4, x: 25, y: 60, name: "CB", number: 5, team: "home" },
  { id: 5, x: 25, y: 80, name: "LB", number: 3, team: "home" },
  { id: 6, x: 45, y: 30, name: "CM", number: 8, team: "home" },
  { id: 7, x: 45, y: 50, name: "CDM", number: 6, team: "home" },
  { id: 8, x: 45, y: 70, name: "CM", number: 10, team: "home" },
  { id: 9, x: 70, y: 25, name: "RW", number: 7, team: "home" },
  { id: 10, x: 70, y: 50, name: "ST", number: 9, team: "home" },
  { id: 11, x: 70, y: 75, name: "LW", number: 11, team: "home" },
  // Away team (simplified)
  { id: 12, x: 90, y: 50, name: "GK", number: 1, team: "away" },
  { id: 13, x: 75, y: 30, name: "DF", number: 4, team: "away" },
  { id: 14, x: 75, y: 70, name: "DF", number: 5, team: "away" },
  { id: 15, x: 55, y: 35, name: "MF", number: 8, team: "away" },
  { id: 16, x: 55, y: 65, name: "MF", number: 10, team: "away" },
  { id: 17, x: 30, y: 50, name: "ST", number: 9, team: "away" },
];

const passConnections: PassConnection[] = [
  { from: 7, to: 6, strength: 0.9 },
  { from: 7, to: 8, strength: 0.85 },
  { from: 6, to: 9, strength: 0.7 },
  { from: 8, to: 11, strength: 0.75 },
  { from: 6, to: 10, strength: 0.65 },
  { from: 3, to: 7, strength: 0.8 },
  { from: 4, to: 7, strength: 0.8 },
];

export function TacticalPitch() {
  const [selectedPlayer, setSelectedPlayer] = useState<number | null>(null);
  const [showVoronoi, setShowVoronoi] = useState(true);
  const [showPassNetwork, setShowPassNetwork] = useState(true);

  const getPlayerById = (id: number) => mockPlayers.find((p) => p.id === id);

  return (
    <div className="relative w-full h-full flex items-center justify-center p-8">
      {/* Pitch Container with 3D perspective */}
      <div className="relative w-full max-w-6xl aspect-[1.5/1]">
        {/* Formation Badge */}
        <FormationBadge formation="4-3-3" style="Attacking" />
        {/* Pitch Background */}
        <div
          className="absolute inset-0 rounded-xl overflow-hidden"
          style={{
            background: `
              linear-gradient(180deg,
                rgba(0, 255, 136, 0.15) 0%,
                rgba(0, 255, 136, 0.08) 50%,
                rgba(0, 255, 136, 0.15) 100%
              ),
              repeating-linear-gradient(
                0deg,
                transparent,
                transparent 10%,
                rgba(0, 255, 136, 0.03) 10%,
                rgba(0, 255, 136, 0.03) 20%
              ),
              #0d1f1a
            `,
            boxShadow: `
              inset 0 0 100px rgba(0, 255, 136, 0.1),
              0 20px 60px rgba(0, 0, 0, 0.5)
            `,
          }}
        >
          {/* Pitch Lines */}
          <svg className="absolute inset-0 w-full h-full" style={{ filter: "drop-shadow(0 0 2px rgba(0, 255, 136, 0.3))" }}>
            {/* Outer boundary */}
            <rect x="5%" y="5%" width="90%" height="90%" fill="none" stroke="rgba(255, 255, 255, 0.4)" strokeWidth="2" />
            {/* Center line */}
            <line x1="50%" y1="5%" x2="50%" y2="95%" stroke="rgba(255, 255, 255, 0.4)" strokeWidth="2" />
            {/* Center circle */}
            <circle cx="50%" cy="50%" r="10%" fill="none" stroke="rgba(255, 255, 255, 0.4)" strokeWidth="2" />
            {/* Penalty areas */}
            <rect x="5%" y="30%" width="15%" height="40%" fill="none" stroke="rgba(255, 255, 255, 0.4)" strokeWidth="2" />
            <rect x="80%" y="30%" width="15%" height="40%" fill="none" stroke="rgba(255, 255, 255, 0.4)" strokeWidth="2" />
          </svg>

          {/* Voronoi Space Control Overlay */}
          {showVoronoi && (
            <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ mixBlendMode: "screen" }}>
              <defs>
                <radialGradient id="voronoi-home">
                  <stop offset="0%" stopColor="#00d9ff" stopOpacity="0.15" />
                  <stop offset="100%" stopColor="#00d9ff" stopOpacity="0.02" />
                </radialGradient>
              </defs>
              {mockPlayers
                .filter((p) => p.team === "home")
                .map((player) => (
                  <motion.circle
                    key={`voronoi-${player.id}`}
                    cx={`${player.x}%`}
                    cy={`${player.y}%`}
                    r="12%"
                    fill="url(#voronoi-home)"
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: player.id * 0.05, duration: 0.6 }}
                  />
                ))}
            </svg>
          )}

          {/* Pass Network Lines */}
          {showPassNetwork && (
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              {passConnections.map((conn, i) => {
                const from = getPlayerById(conn.from);
                const to = getPlayerById(conn.to);
                if (!from || !to) return null;

                return (
                  <motion.line
                    key={`pass-${i}`}
                    x1={`${from.x}%`}
                    y1={`${from.y}%`}
                    x2={`${to.x}%`}
                    y2={`${to.y}%`}
                    stroke="#00d9ff"
                    strokeWidth={conn.strength * 3}
                    strokeOpacity={0.4}
                    initial={{ pathLength: 0, opacity: 0 }}
                    animate={{ pathLength: 1, opacity: 0.4 }}
                    transition={{ delay: 0.5 + i * 0.1, duration: 0.8 }}
                    style={{
                      filter: "drop-shadow(0 0 4px rgba(0, 217, 255, 0.6))",
                    }}
                  />
                );
              })}
            </svg>
          )}

          {/* Players */}
          {mockPlayers.map((player, index) => (
            <motion.div
              key={player.id}
              className="absolute cursor-pointer group"
              style={{
                left: `${player.x}%`,
                top: `${player.y}%`,
                transform: "translate(-50%, -50%)",
              }}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05, duration: 0.4 }}
              onClick={() => setSelectedPlayer(player.id === selectedPlayer ? null : player.id)}
            >
              {/* Player Node */}
              <div
                className={`relative w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                  player.team === "home"
                    ? "bg-cyan-500 shadow-[0_0_20px_rgba(0,217,255,0.6)]"
                    : "bg-red-500 shadow-[0_0_20px_rgba(255,71,87,0.6)]"
                } ${selectedPlayer === player.id ? "scale-125 ring-4 ring-white/40" : "group-hover:scale-110"}`}
              >
                <span className="text-xs font-bold text-white">{player.number}</span>

                {/* Glow effect */}
                <div
                  className={`absolute inset-0 rounded-full blur-lg opacity-60 ${
                    player.team === "home" ? "bg-cyan-400" : "bg-red-400"
                  }`}
                />
              </div>

              {/* Player Label */}
              <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                <div className="bg-black/80 backdrop-blur-sm px-2 py-1 rounded text-xs font-medium text-white border border-white/20">
                  {player.name}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Controls */}
        <div className="absolute top-4 right-4 flex gap-2">
          <button
            onClick={() => setShowVoronoi(!showVoronoi)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium backdrop-blur-xl transition-all ${
              showVoronoi
                ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 shadow-[0_0_20px_rgba(0,217,255,0.3)]"
                : "bg-white/5 text-white/60 border border-white/10 hover:bg-white/10"
            }`}
          >
            Space Control
          </button>
          <button
            onClick={() => setShowPassNetwork(!showPassNetwork)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium backdrop-blur-xl transition-all ${
              showPassNetwork
                ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 shadow-[0_0_20px_rgba(0,217,255,0.3)]"
                : "bg-white/5 text-white/60 border border-white/10 hover:bg-white/10"
            }`}
          >
            Pass Network
          </button>
        </div>
      </div>
    </div>
  );
}
