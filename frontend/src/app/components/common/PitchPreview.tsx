import { motion } from "motion/react";
import type { PlayerData } from "../../../lib/types";

interface PitchPreviewProps {
  teamA: PlayerData[];
  teamB: PlayerData[];
  teamAColor?: string;
  teamBColor?: string;
  ball?: { x: number; y: number } | null;
  className?: string;
  showNames?: boolean;
}

/**
 * Lightweight SVG pitch (120 × 80 engine coordinates) used as a live
 * preview while players are being entered, and to show what a video or
 * dataset upload resolved to.
 */
export function PitchPreview({
  teamA,
  teamB,
  teamAColor = "#00d9ff",
  teamBColor = "#ff5a6e",
  ball,
  className,
  showNames = true,
}: PitchPreviewProps) {
  const W = 120;
  const H = 80;
  return (
    <svg
      viewBox={`-2 -2 ${W + 4} ${H + 4}`}
      className={className}
      role="img"
      aria-label="Pitch preview of player positions"
      style={{ width: "100%", height: "auto", display: "block" }}
    >
      <defs>
        <linearGradient id="pp-grass" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0f3d2e" />
          <stop offset="1" stopColor="#0b2e23" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width={W} height={H} rx="1.5" fill="url(#pp-grass)" />
      {/* mowing stripes */}
      {Array.from({ length: 6 }).map((_, i) => (
        <rect key={i} x={i * 20} y="0" width="10" height={H} fill="rgba(255,255,255,0.025)" />
      ))}
      <g fill="none" stroke="rgba(255,255,255,0.45)" strokeWidth="0.6">
        <rect x="0" y="0" width={W} height={H} />
        <line x1={W / 2} y1="0" x2={W / 2} y2={H} />
        <circle cx={W / 2} cy={H / 2} r="9.15" />
        <rect x="0" y={H / 2 - 22} width="18" height="44" />
        <rect x={W - 18} y={H / 2 - 22} width="18" height="44" />
        <rect x="0" y={H / 2 - 10} width="6" height="20" />
        <rect x={W - 6} y={H / 2 - 10} width="6" height="20" />
        <rect x="-1.5" y={H / 2 - 3.7} width="1.5" height="7.4" />
        <rect x={W} y={H / 2 - 3.7} width="1.5" height="7.4" />
      </g>
      <circle cx="12" cy={H / 2} r="0.5" fill="rgba(255,255,255,0.5)" />
      <circle cx={W - 12} cy={H / 2} r="0.5" fill="rgba(255,255,255,0.5)" />

      {[{ list: teamB, color: teamBColor, key: "b" }, { list: teamA, color: teamAColor, key: "a" }].map(({ list, color, key }) =>
        list.map((p, i) => (
          <motion.g
            key={`${key}-${p.number}-${i}`}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 22, delay: i * 0.02 }}
            style={{ transformOrigin: `${p.x}px ${p.y}px` }}
          >
            <circle cx={p.x} cy={p.y} r="2.6" fill={color} stroke="rgba(0,0,0,0.6)" strokeWidth="0.4" />
            <text x={p.x} y={p.y + 0.9} textAnchor="middle" fontSize="2.6" fontWeight="700" fill="#0a0e27">
              {p.number}
            </text>
            {showNames && (
              <text x={p.x} y={p.y + 5.2} textAnchor="middle" fontSize="2.2" fill="rgba(255,255,255,0.85)">
                {p.name.length > 11 ? p.name.slice(0, 10) + "…" : p.name}
              </text>
            )}
          </motion.g>
        ))
      )}

      {ball && Number.isFinite(ball.x) && Number.isFinite(ball.y) && (
        <motion.circle
          cx={ball.x}
          cy={ball.y}
          r="1.4"
          fill="#fff"
          stroke="#111"
          strokeWidth="0.3"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          style={{ transformOrigin: `${ball.x}px ${ball.y}px` }}
        />
      )}
    </svg>
  );
}
