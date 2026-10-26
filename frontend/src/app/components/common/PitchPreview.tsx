import { motion, useReducedMotion } from "motion/react";
import { useMemo } from "react";
import type { PassEvent, PlayerData } from "../../../lib/types";
import { EASE_OUT } from "../../../lib/motion";

interface PitchPreviewProps {
  teamA: PlayerData[];
  teamB: PlayerData[];
  teamAColor?: string;
  teamBColor?: string;
  ball?: { x: number; y: number } | null;
  /** Team A passes, drawn between the passer and receiver positions. */
  passes?: PassEvent[];
  className?: string;
  showNames?: boolean;
  /** Delay before the passes start drawing, in seconds. */
  passDelay?: number;
}

/** Black or white shirt number, whichever reads better on the kit colour. */
export function inkOn(hex: string): string {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return "#ffffff";
  const n = parseInt(m[1], 16);
  const lum = (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255;
  return lum > 0.6 ? "#0d0d0d" : "#ffffff";
}

const W = 120;
const H = 80;

/**
 * Lightweight SVG pitch (120 × 80 engine coordinates) used as a live
 * preview while players are being entered, to show what a video or
 * dataset upload resolved to, and as the Home page hero.
 */
export function PitchPreview({
  teamA,
  teamB,
  teamAColor = "#0d0d0d",
  teamBColor = "#e1061f",
  ball,
  passes,
  className,
  showNames = true,
  passDelay = 0.3,
}: PitchPreviewProps) {
  const reduce = useReducedMotion();

  // Repeated passer→receiver pairs collapse into one thicker line.
  const links = useMemo(() => {
    if (!passes?.length) return [];
    const byNumber = new Map(teamA.map((p) => [p.number, p]));
    const merged = new Map<string, { from: PlayerData; to: PlayerData; count: number; failed: number }>();
    for (const ps of passes) {
      const from = byNumber.get(ps.passer);
      const to = byNumber.get(ps.receiver);
      if (!from || !to || from === to) continue;
      const key = `${ps.passer}-${ps.receiver}`;
      const m = merged.get(key) ?? { from, to, count: 0, failed: 0 };
      m.count += 1;
      if (ps.success === false) m.failed += 1;
      merged.set(key, m);
    }
    return [...merged.values()];
  }, [passes, teamA]);

  return (
    <svg
      viewBox={`-2 -2 ${W + 4} ${H + 4}`}
      className={className}
      role="img"
      aria-label="Pitch preview of player positions"
      style={{ width: "100%", height: "auto", display: "block" }}
    >
      <rect x="-2" y="-2" width={W + 4} height={H + 4} style={{ fill: "var(--grass)" }} />
      {Array.from({ length: 6 }).map((_, i) => (
        <rect key={i} x={i * 20} y="0" width="10" height={H} style={{ fill: "var(--grass-stripe)" }} />
      ))}
      <g fill="none" style={{ stroke: "var(--pitch-line)" }} strokeWidth="0.5">
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
      <circle cx="12" cy={H / 2} r="0.5" fill="#fff" />
      <circle cx={W - 12} cy={H / 2} r="0.5" fill="#fff" />

      {links.map((l, i) => (
        <motion.line
          key={`${l.from.number}-${l.to.number}`}
          x1={l.from.x}
          y1={l.from.y}
          x2={l.to.x}
          y2={l.to.y}
          stroke={l.failed === l.count ? "#ffc61a" : "#ffffff"}
          strokeOpacity={0.8}
          strokeWidth={Math.min(1.4, 0.35 + l.count * 0.25)}
          strokeLinecap="round"
          initial={reduce ? false : { pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 0.4, delay: passDelay + i * 0.03, ease: EASE_OUT }}
        />
      ))}

      {[{ list: teamB, color: teamBColor, key: "b" }, { list: teamA, color: teamAColor, key: "a" }].map(({ list, color, key }) =>
        list.map((p, i) => (
          <motion.g
            key={`${key}-${p.number}-${i}`}
            initial={reduce ? false : { opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.25, delay: Math.min(i * 0.02, 0.2), ease: EASE_OUT }}
            style={{ transformOrigin: `${p.x}px ${p.y}px` }}
          >
            <circle cx={p.x} cy={p.y} r="2.7" fill={color} stroke="#ffffff" strokeWidth="0.45" />
            <text x={p.x} y={p.y + 0.95} textAnchor="middle" fontSize="2.7" fontWeight="800" fill={inkOn(color)} fontFamily="var(--font-sans)">
              {p.number}
            </text>
            {showNames && (
              <text x={p.x} y={p.y + 5.4} textAnchor="middle" fontSize="2.2" fontWeight="600" fill="#ffffff" fontFamily="var(--font-sans)">
                {p.name.length > 11 ? p.name.slice(0, 10) + "…" : p.name}
              </text>
            )}
          </motion.g>
        ))
      )}

      {ball && Number.isFinite(ball.x) && Number.isFinite(ball.y) && (
        <circle cx={ball.x} cy={ball.y} r="1.4" fill="#fff" stroke="#111" strokeWidth="0.3" />
      )}
    </svg>
  );
}
