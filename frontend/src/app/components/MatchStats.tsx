import { motion } from "motion/react";
import { AreaChart, Area, ResponsiveContainer } from "recharts";

interface StatCardProps {
  label: string;
  homeValue: number;
  awayValue: number;
  unit?: string;
  trend?: number[];
}

const possessionData = [
  { value: 52 },
  { value: 54 },
  { value: 51 },
  { value: 56 },
  { value: 58 },
  { value: 57 },
  { value: 59 },
  { value: 61 },
];

function StatCard({ label, homeValue, awayValue, unit = "", trend }: StatCardProps) {
  const homePercentage = (homeValue / (homeValue + awayValue)) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative"
    >
      <div
        className="rounded-lg p-3 backdrop-blur-xl border border-white/10"
        style={{
          background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)",
        }}
      >
        {/* Label */}
        <div className="text-[10px] uppercase tracking-wider text-white/50 font-bold mb-2">{label}</div>

        {/* Values */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-lg font-bold text-cyan-400">
            {homeValue}
            {unit}
          </span>
          <span className="text-lg font-bold text-red-400">
            {awayValue}
            {unit}
          </span>
        </div>

        {/* Bar */}
        <div className="relative h-1.5 bg-white/5 rounded-full overflow-hidden">
          <motion.div
            className="absolute left-0 top-0 h-full bg-gradient-to-r from-cyan-500 to-cyan-400 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${homePercentage}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            style={{
              boxShadow: "0 0 10px rgba(0, 217, 255, 0.5)",
            }}
          />
        </div>

        {/* Trend chart */}
        {trend && (
          <div className="mt-2 h-8 -mx-1">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trend.map((value) => ({ value }))}>
                <defs>
                  <linearGradient id={`gradient-${label}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#00d9ff" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#00d9ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#00d9ff"
                  strokeWidth={2}
                  fill={`url(#gradient-${label})`}
                  isAnimationActive={true}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export function MatchStats() {
  return (
    <div className="w-full p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Live Match Statistics</h2>
          <p className="text-sm text-white/50">Real-time data • 67:42</p>
        </div>
        <div className="flex items-center gap-4 px-4 py-2 rounded-lg bg-white/5 border border-white/10">
          <div className="text-center">
            <div className="text-2xl font-bold text-cyan-400">2</div>
            <div className="text-[10px] text-white/50 uppercase">Home</div>
          </div>
          <div className="text-white/30 text-2xl">-</div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-400">1</div>
            <div className="text-[10px] text-white/50 uppercase">Away</div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Possession" homeValue={61} awayValue={39} unit="%" trend={possessionData} />
        <StatCard label="Shots on Target" homeValue={7} awayValue={4} />
        <StatCard label="Pass Accuracy" homeValue={87} awayValue={79} unit="%" />
        <StatCard label="Tackles Won" homeValue={12} awayValue={18} />
        <StatCard label="Final Third Entries" homeValue={34} awayValue={21} />
        <StatCard label="Expected Goals (xG)" homeValue={2.3} awayValue={1.1} />
      </div>
    </div>
  );
}
