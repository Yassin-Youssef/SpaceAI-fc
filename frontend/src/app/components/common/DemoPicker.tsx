import { useEffect, useState } from "react";
import { listDemoMatches } from "../../../lib/api";
import type { DemoMatchSummary } from "../../../lib/types";
import { PresetPicker, type PresetItem } from "./PresetPicker";

/** Fallback entry when the backend can't be reached. */
const BUILTIN_DEMO: DemoMatchSummary = {
  id: "builtin",
  title: "FC Barcelona 2-1 Real Madrid",
  subtitle: "Built-in sample line-ups (works offline)",
  date: "2026-04-07",
  competition: "Sample fixture",
  team_a: "FC Barcelona",
  team_b: "Real Madrid",
  score: { a: 2, b: 1 },
  source_kind: "sample",
  players: 22,
  passes: 30,
};

interface DemoPickerProps {
  /** Run the analysis immediately with this fixture. */
  onRun: (match: DemoMatchSummary) => void;
  /** Only fill the form with this fixture. */
  onLoad: (match: DemoMatchSummary) => void;
  disabled?: boolean;
  busyId?: string | null;
}

/** "Try demo" menu of every bundled real match, built on PresetPicker. */
export function DemoPicker({ onRun, onLoad, disabled, busyId }: DemoPickerProps) {
  const [matches, setMatches] = useState<DemoMatchSummary[]>([BUILTIN_DEMO]);

  useEffect(() => {
    let cancelled = false;
    listDemoMatches()
      .then((list) => { if (!cancelled && list.length) setMatches(list); })
      .catch(() => { /* keep the built-in fixture */ });
    return () => { cancelled = true; };
  }, []);

  const items: PresetItem[] = matches.map((m) => ({
    id: m.id,
    title: m.title,
    subtitle: m.subtitle,
    kind: m.source_kind,
    meta: `${m.passes} passes${m.formation_a ? `, line-ups ${m.formation_a} v ${m.formation_b}` : ""}`,
  }));
  const byId = (item: PresetItem) => matches.find((m) => m.id === item.id) ?? BUILTIN_DEMO;

  return (
    <PresetPicker
      items={items}
      storageKey="spaceai.demoMatch"
      onRun={(i) => onRun(byId(i))}
      onLoad={(i) => onLoad(byId(i))}
      disabled={disabled}
      busyId={busyId}
      heading="Demo fixtures"
      footer="Real fixtures use StatsBomb open data: each starter's median position and the real passes. Play runs the analysis; the pencil only fills the form."
    />
  );
}
