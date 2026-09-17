/**
 * SpaceAI FC — El Clásico demo data
 * ==================================
 * Shared by every feature's "Try Demo" button so users can see results
 * without typing anything.  Coordinates use the engine's pitch
 * (x 0–120, y 0–80).
 */

import type { FormPlayer, PassEvent, MatchInfo } from "./types";

export const DEMO_TEAM_A_NAME = "FC Barcelona";
export const DEMO_TEAM_B_NAME = "Real Madrid";
export const DEMO_TEAM_A_COLOR = "#00d9ff";
export const DEMO_TEAM_B_COLOR = "#ff5a6e";

export const DEMO_TEAM_A: FormPlayer[] = [
  { name: "ter Stegen",  number: "1",  x: "5",  y: "40", position: "GK" },
  { name: "Koundé",      number: "23", x: "30", y: "70", position: "RB" },
  { name: "Araújo",      number: "4",  x: "25", y: "52", position: "CB" },
  { name: "Cubarsí",     number: "2",  x: "25", y: "28", position: "CB" },
  { name: "Baldé",       number: "3",  x: "30", y: "10", position: "LB" },
  { name: "Pedri",       number: "8",  x: "45", y: "48", position: "CM" },
  { name: "De Jong",     number: "21", x: "45", y: "32", position: "CM" },
  { name: "Lamine",      number: "19", x: "65", y: "68", position: "RW" },
  { name: "Gavi",        number: "6",  x: "60", y: "40", position: "CAM" },
  { name: "Raphinha",    number: "11", x: "65", y: "12", position: "LW" },
  { name: "Lewandowski", number: "9",  x: "80", y: "40", position: "ST" },
];

export const DEMO_TEAM_B: FormPlayer[] = [
  { name: "Courtois",   number: "1",  x: "115", y: "40", position: "GK" },
  { name: "Carvajal",   number: "2",  x: "90",  y: "70", position: "RB" },
  { name: "Rüdiger",    number: "22", x: "93",  y: "52", position: "CB" },
  { name: "Militão",    number: "3",  x: "93",  y: "28", position: "CB" },
  { name: "Mendy",      number: "23", x: "90",  y: "10", position: "LB" },
  { name: "Tchouaméni", number: "14", x: "78",  y: "40", position: "CDM" },
  { name: "Valverde",   number: "15", x: "70",  y: "55", position: "CM" },
  { name: "Bellingham", number: "5",  x: "70",  y: "25", position: "CM" },
  { name: "Rodrygo",    number: "11", x: "55",  y: "65", position: "RW" },
  { name: "Mbappé",     number: "7",  x: "50",  y: "40", position: "ST" },
  { name: "Vinícius",   number: "20", x: "55",  y: "15", position: "LW" },
];

/** Barcelona build-up passes (passer → receiver, success flag). */
export const DEMO_PASSES: PassEvent[] = [
  { passer: 1,  receiver: 4,  success: true },
  { passer: 1,  receiver: 2,  success: true },
  { passer: 4,  receiver: 8,  success: true },
  { passer: 4,  receiver: 21, success: true },
  { passer: 4,  receiver: 23, success: true },
  { passer: 2,  receiver: 21, success: true },
  { passer: 2,  receiver: 3,  success: true },
  { passer: 23, receiver: 19, success: true },
  { passer: 23, receiver: 8,  success: true },
  { passer: 3,  receiver: 11, success: true },
  { passer: 3,  receiver: 21, success: true },
  { passer: 8,  receiver: 6,  success: true },
  { passer: 8,  receiver: 19, success: true },
  { passer: 8,  receiver: 21, success: true },
  { passer: 8,  receiver: 9,  success: true },
  { passer: 8,  receiver: 11, success: true },
  { passer: 21, receiver: 8,  success: true },
  { passer: 21, receiver: 6,  success: true },
  { passer: 21, receiver: 11, success: true },
  { passer: 6,  receiver: 9,  success: true },
  { passer: 6,  receiver: 19, success: true },
  { passer: 6,  receiver: 8,  success: true },
  { passer: 6,  receiver: 11, success: false },
  { passer: 19, receiver: 9,  success: true },
  { passer: 19, receiver: 6,  success: true },
  { passer: 19, receiver: 8,  success: false },
  { passer: 11, receiver: 9,  success: true },
  { passer: 11, receiver: 6,  success: true },
  { passer: 9,  receiver: 6,  success: true },
  { passer: 9,  receiver: 19, success: true },
];

/** Pass list in the text-area format ("passer->receiver->success"). */
export const DEMO_PASSES_TEXT = DEMO_PASSES.map(
  (p) => `${p.passer}->${p.receiver}->${p.success === false ? 0 : 1}`
).join(", ");

export const DEMO_MATCH_INFO: MatchInfo = {
  home_team: DEMO_TEAM_A_NAME,
  away_team: DEMO_TEAM_B_NAME,
  score_home: 2,
  score_away: 1,
  minute: 65,
  competition: "La Liga",
  date: "2026-04-07",
};

export const POSITIONS = ["GK", "CB", "RB", "LB", "RWB", "LWB", "CDM", "CM", "CAM", "RW", "LW", "ST", "CF"];

export const SITUATIONS: Array<{ id: string; label: string }> = [
  { id: "", label: "Auto-detect from positions" },
  { id: "low_block", label: "Opponent sits in a low block" },
  { id: "high_press", label: "Opponent presses high" },
  { id: "counter_attack", label: "Opponent counter-attacks" },
  { id: "possession_play", label: "Opponent dominates possession" },
  { id: "midfield_overload", label: "Opponent overloads midfield" },
  { id: "wide_play", label: "Opponent attacks through wide areas" },
  { id: "park_the_bus", label: "Opponent parks the bus" },
  { id: "high_line", label: "Opponent plays a high line" },
  { id: "transition_moment", label: "Transition moment" },
];

export const TACTICS: Array<{ id: string; label: string; blurb: string }> = [
  { id: "high_press",     label: "High Press",     blurb: "Win the ball high, accept space in behind" },
  { id: "low_block",      label: "Low Block",      blurb: "Compact, deep, patient" },
  { id: "wide_play",      label: "Wide Play",      blurb: "Stretch the pitch with width" },
  { id: "narrow_play",    label: "Narrow Play",    blurb: "Overload the centre" },
  { id: "counter_attack", label: "Counter-Attack", blurb: "Fast, direct transitions" },
  { id: "possession",     label: "Possession",     blurb: "Slow tempo, control the ball" },
];

export const emptyPlayers = (): FormPlayer[] =>
  Array.from({ length: 11 }, () => ({ name: "", number: "", x: "", y: "", position: "CM" }));

/** Simulation presets themed after the demo fixtures (stylised what-ifs, not replays). */
export const SIM_PRESETS = [
  { id: "anfield-2023", title: "Anfield 2023 · High Press v Counter", subtitle: "Liverpool 7-0 Man Utd: Klopp's press against a transition side", tactic_a: "high_press", tactic_b: "counter_attack", team_size: 5, steps: 400, seed: 7 },
  { id: "istanbul-2005", title: "Istanbul 2005 · Possession v Low Block", subtitle: "Milan's control against a deep Liverpool block", tactic_a: "possession", tactic_b: "low_block", team_size: 7, steps: 500, seed: 2005 },
  { id: "lusail-2022", title: "Lusail 2022 · Possession v Counter", subtitle: "Argentina's control against France's transitions", tactic_a: "possession", tactic_b: "counter_attack", team_size: 7, steps: 500, seed: 2022 },
  { id: "wembley-2011", title: "Wembley 2011 · Possession v Narrow Block", subtitle: "Barcelona's tiki-taka against United's compact midfield", tactic_a: "possession", tactic_b: "narrow_play", team_size: 5, steps: 400, seed: 2011 },
  { id: "montjuic-2025", title: "Montjuïc 2025 · High Line v Counter", subtitle: "Flick's high press against Mbappé's transitions", tactic_a: "high_press", tactic_b: "counter_attack", team_size: 5, steps: 400, seed: 43 },
];

/** Compare presets: two match-ups side by side. */
export const COMPARE_PRESETS = [
  { id: "press-vs-sit", title: "Press or sit deep?", subtitle: "High Press v Counter (Anfield 2023) against Low Block v Counter", m1: { a: "high_press", b: "counter_attack" }, m2: { a: "low_block", b: "counter_attack" }, runs: 3, steps: 400, team_size: 5 },
  { id: "possession-tests", title: "Possession v Low Block or v Press?", subtitle: "Istanbul 2005 style against a pressing opponent", m1: { a: "possession", b: "low_block" }, m2: { a: "possession", b: "high_press" }, runs: 3, steps: 400, team_size: 7 },
  { id: "width-vs-narrow", title: "Wide play or narrow?", subtitle: "Stretch the pitch against a low block, or overload the centre", m1: { a: "wide_play", b: "low_block" }, m2: { a: "narrow_play", b: "low_block" }, runs: 4, steps: 400, team_size: 5 },
];
