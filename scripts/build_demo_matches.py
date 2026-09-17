"""
Build the bundled demo matches used by every "Try Demo" button.
================================================================

Real fixtures come from StatsBomb's free open data (statsbombpy).  Each
starter's position is their average event location over the match, passes
are the team-of-interest's real pass events (with coordinates and success
flags), and everything is written to data/demo_matches/<id>.json so the app
never needs network access at runtime.

Two fixtures have no public event data and are *reconstructed*: real
line-ups, formations and score, with pass events synthesised from the
formation.  They are labelled as such in the JSON and in the UI.

Run from the project root (needs internet for the StatsBomb fetch):
    .venv/Scripts/python scripts/build_demo_matches.py

StatsBomb open data licence: free for non-commercial use with attribution.
https://github.com/statsbomb/open-data
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "demo_matches"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TEAM_A_COLOR = "#00d9ff"
TEAM_B_COLOR = "#ff5a6e"
MAX_PASSES = 260

# StatsBomb position name → engine position code
POSITION_MAP = {
    "Goalkeeper": "GK",
    "Right Back": "RB", "Left Back": "LB",
    "Right Center Back": "CB", "Left Center Back": "CB", "Center Back": "CB",
    "Right Wing Back": "RWB", "Left Wing Back": "LWB",
    "Right Defensive Midfield": "CDM", "Left Defensive Midfield": "CDM", "Center Defensive Midfield": "CDM",
    "Right Center Midfield": "CM", "Left Center Midfield": "CM", "Center Midfield": "CM",
    "Right Midfield": "RM", "Left Midfield": "LM",
    "Right Attacking Midfield": "CAM", "Left Attacking Midfield": "CAM", "Center Attacking Midfield": "CAM",
    "Right Wing": "RW", "Left Wing": "LW",
    "Right Center Forward": "ST", "Left Center Forward": "ST", "Center Forward": "ST",
    "Secondary Striker": "CF",
}

# ── Real-data fixtures ────────────────────────────────────────────

REAL_FIXTURES = [
    {
        "id": "wc2022-final",
        "match_id": 3869685,
        "team_a": "Argentina", "team_b": "France",
        "title": "Argentina 3-3 France",
        "subtitle": "FIFA World Cup Final · Lusail · 18 Dec 2022 (Argentina won 4-2 on penalties)",
        "competition": "FIFA World Cup 2022 — Final",
        "date": "2022-12-18",
        "score": (3, 3),
        "minute": 120,
    },
    {
        "id": "ucl2005-final",
        "match_id": 2302764,
        "team_a": "Liverpool", "team_b": "AC Milan",
        "title": "Liverpool 3-3 AC Milan",
        "subtitle": "Champions League Final · Istanbul · 25 May 2005 (Liverpool won 3-2 on penalties)",
        "competition": "UEFA Champions League 2004/05 — Final",
        "date": "2005-05-25",
        "score": (3, 3),
        "minute": 120,
    },
    {
        "id": "ucl2011-final",
        "match_id": 18236,
        "team_a": "Barcelona", "team_b": "Manchester United",
        "title": "Barcelona 3-1 Manchester United",
        "subtitle": "Champions League Final · Wembley · 28 May 2011",
        "competition": "UEFA Champions League 2010/11 — Final",
        "date": "2011-05-28",
        "score": (3, 1),
        "minute": 90,
    },
    {
        "id": "clasico-2017",
        "match_id": 267569,
        "team_a": "Barcelona", "team_b": "Real Madrid",
        "title": "Real Madrid 2-3 Barcelona",
        "subtitle": "La Liga · Santiago Bernabéu · 23 Apr 2017 · Messi 92' winner",
        "competition": "La Liga 2016/17",
        "date": "2017-04-23",
        "score": (3, 2),
        "minute": 90,
    },
]

# ── Reconstructed fixtures (no public event data) ─────────────────
# Positions follow the formation each side used; passes are synthesised.

RECONSTRUCTED = [
    {
        "id": "clasico-2025",
        "title": "Barcelona 4-3 Real Madrid",
        "subtitle": "La Liga · Estadi Olímpic Lluís Companys · 11 May 2025 · title decider",
        "competition": "La Liga 2024/25",
        "date": "2025-05-11",
        "team_a": "Barcelona", "team_b": "Real Madrid",
        "formation_a": "4-2-3-1", "formation_b": "4-2-3-1",
        "score": (4, 3),
        "minute": 90,
        "players_a": [  # 4-2-3-1
            ("Szczęsny", 25, "GK", 5, 40),
            ("Eric García", 24, "RB", 30, 68), ("Cubarsí", 2, "CB", 26, 50), ("Iñigo Martínez", 5, "CB", 26, 30), ("Gerard Martín", 35, "LB", 30, 12),
            ("De Jong", 21, "CDM", 46, 46), ("Pedri", 8, "CM", 48, 32),
            ("Lamine Yamal", 19, "RW", 68, 68), ("Dani Olmo", 20, "CAM", 62, 40), ("Raphinha", 11, "LW", 68, 12),
            ("Ferran Torres", 7, "ST", 82, 40),
        ],
        "players_b": [  # 4-2-3-1 (engine coordinates: attacking right-to-left)
            ("Courtois", 1, "GK", 115, 40),
            ("Lucas Vázquez", 17, "RB", 92, 12), ("Asencio", 35, "CB", 95, 30), ("Tchouaméni", 14, "CB", 95, 50), ("Fran García", 20, "LB", 92, 68),
            ("Ceballos", 19, "CDM", 76, 34), ("Valverde", 8, "CM", 74, 50),
            ("Güler", 15, "RW", 58, 14), ("Bellingham", 5, "CAM", 60, 40), ("Vinícius", 7, "LW", 56, 66),
            ("Mbappé", 9, "ST", 44, 40),
        ],
        "note": "Real line-ups and score; pass events are synthesised from the formations because no public event data exists for this match.",
    },
    {
        "id": "liverpool-7-0",
        "title": "Liverpool 7-0 Manchester United",
        "subtitle": "Premier League · Anfield · 5 Mar 2023 · record derby win",
        "competition": "Premier League 2022/23",
        "date": "2023-03-05",
        "team_a": "Liverpool", "team_b": "Manchester United",
        "formation_a": "4-3-3", "formation_b": "4-2-3-1",
        "score": (7, 0),
        "minute": 90,
        "players_a": [  # 4-3-3
            ("Alisson", 1, "GK", 5, 40),
            ("Alexander-Arnold", 66, "RB", 34, 68), ("Konaté", 5, "CB", 26, 50), ("Van Dijk", 4, "CB", 26, 30), ("Robertson", 26, "LB", 34, 12),
            ("Fabinho", 3, "CDM", 44, 40), ("Henderson", 14, "CM", 54, 54), ("Elliott", 19, "CM", 54, 26),
            ("Salah", 11, "RW", 72, 66), ("Gakpo", 18, "ST", 78, 40), ("Núñez", 27, "LW", 72, 14),
        ],
        "players_b": [  # 4-2-3-1
            ("De Gea", 1, "GK", 115, 40),
            ("Dalot", 20, "RB", 92, 12), ("Varane", 19, "CB", 96, 30), ("Lisandro Martínez", 6, "CB", 96, 50), ("Shaw", 23, "LB", 92, 68),
            ("Casemiro", 18, "CDM", 78, 44), ("Fred", 17, "CM", 76, 30),
            ("Antony", 21, "RW", 58, 12), ("Bruno Fernandes", 8, "CAM", 62, 40), ("Rashford", 10, "LW", 56, 68),
            ("Weghorst", 27, "ST", 46, 40),
        ],
        "note": "Real line-ups and score; pass events are synthesised from the formations because no public event data exists for this match.",
    },
]


# ── Demo players (for Player Assessment) ──────────────────────────
# Stats are computed from the StatsBomb events of the fixture; bio fields
# are public record at the date of the match.

DEMO_PLAYERS = [
    {"id": "messi-2022", "match": "wc2022-final", "team": "Argentina", "name": "Lionel Messi", "number": 10,
     "age": 35, "foot": "Left", "height": "170cm", "weight": "72kg", "position": "RW"},
    {"id": "enzo-2022", "match": "wc2022-final", "team": "Argentina", "name": "Enzo Fernández", "number": 24,
     "age": 21, "foot": "Right", "height": "178cm", "weight": "76kg", "position": "CDM"},
    {"id": "mbappe-2022", "match": "wc2022-final", "team": "France", "name": "Kylian Mbappé", "number": 10,
     "age": 23, "foot": "Right", "height": "178cm", "weight": "75kg", "position": "LW"},
    {"id": "griezmann-2022", "match": "wc2022-final", "team": "France", "name": "Antoine Griezmann", "number": 7,
     "age": 31, "foot": "Left", "height": "176cm", "weight": "73kg", "position": "CAM"},
    {"id": "gerrard-2005", "match": "ucl2005-final", "team": "Liverpool", "name": "Steven Gerrard", "number": 8,
     "age": 24, "foot": "Right", "height": "183cm", "weight": "83kg", "position": "CM"},
    {"id": "kaka-2005", "match": "ucl2005-final", "team": "AC Milan", "name": "Kaká", "number": 22,
     "age": 23, "foot": "Right", "height": "186cm", "weight": "82kg", "position": "CAM"},
    {"id": "xavi-2011", "match": "ucl2011-final", "team": "Barcelona", "name": "Xavi", "number": 6,
     "age": 31, "foot": "Right", "height": "170cm", "weight": "68kg", "position": "CM"},
    {"id": "rooney-2011", "match": "ucl2011-final", "team": "Manchester United", "name": "Wayne Rooney", "number": 10,
     "age": 25, "foot": "Right", "height": "176cm", "weight": "83kg", "position": "ST"},
    {"id": "messi-2017", "match": "clasico-2017", "team": "Barcelona", "name": "Lionel Messi", "number": 10,
     "age": 29, "foot": "Left", "height": "170cm", "weight": "72kg", "position": "CAM"},
]

# No public event data: line-up facts are real, the stat line is an estimate.
RECONSTRUCTED_PLAYERS = [
    {"id": "lamine-2025", "match": "clasico-2025", "team": "Barcelona", "name": "Lamine Yamal", "number": 19,
     "age": 17, "foot": "Left", "height": "180cm", "weight": "72kg", "position": "RW",
     "stats": {"passes_completed": 38, "passes_attempted": 47, "tackles": 1, "interceptions": 1,
               "shots": 4, "dribbles": 6, "aerial_duels": 1, "distance_covered": 10.1, "sprints": 24},
     "note": "Reconstructed: real line-up facts, estimated stat line (no public event data)."},
]


def _carry_len(row) -> float:
    a, b = row.get("location"), row.get("carry_end_location")
    if isinstance(a, list) and isinstance(b, list):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
    return 0.0


def player_stats(events: pd.DataFrame, lineup: pd.DataFrame, number: int) -> dict:
    """Count a player's match actions from StatsBomb events."""
    row = lineup[lineup["jersey_number"] == number]
    if row.empty:
        raise ValueError(f"no player with number {number}")
    pid = int(row.iloc[0]["player_id"])
    ev = events[(events["player_id"] == pid) & (events["period"] <= 4)]

    passes = ev[ev["type"] == "Pass"]
    completed = int(passes["pass_outcome"].isna().sum()) if "pass_outcome" in passes.columns else len(passes)
    shots = int((ev["type"] == "Shot").sum())
    dribbles = ev[ev["type"] == "Dribble"]
    dribbles_ok = int((dribbles["dribble_outcome"] == "Complete").sum()) if "dribble_outcome" in dribbles.columns else len(dribbles)
    duels = ev[ev["type"] == "Duel"]
    tackles = int((duels["duel_type"] == "Tackle").sum()) if "duel_type" in duels.columns else 0
    interceptions = int((ev["type"] == "Interception").sum()) + int((ev["type"] == "Ball Recovery").sum()) // 3
    aerial_cols = [c for c in ("pass_aerial_won", "shot_aerial_won", "clearance_aerial_won", "miscontrol_aerial_won") if c in ev.columns]
    aerials = int(sum(ev[c].fillna(False).astype(bool).sum() for c in aerial_cols))

    # Minutes on the pitch: span from first "from" to last "to" (missing "to"
    # means the player finished the match, including extra time).
    positions = row.iloc[0]["positions"] or []
    match_end = int(events.loc[events["period"] <= 4, "minute"].max() or 90)
    starts = [int(str(pos.get("from") or "0:00").split(":")[0]) for pos in positions] or [0]
    ends = [int(str(pos["to"]).split(":")[0]) if pos.get("to") else match_end for pos in positions] or [match_end]
    minutes = int(max(45, min(120, max(ends) - min(starts))))

    carries = ev[ev["type"] == "Carry"]
    lengths = [_carry_len(c) for _, c in carries.iterrows()]
    carry_dist = sum(lengths)
    long_carries = sum(1 for L in lengths if L > 10)

    return {
        "passes_completed": completed,
        "passes_attempted": int(len(passes)),
        "tackles": tackles,
        "interceptions": interceptions,
        "shots": shots,
        "dribbles": dribbles_ok,
        "aerial_duels": aerials,
        # Event data has no tracking, so these two are estimates from minutes and carries
        "distance_covered": round(minutes * 0.112, 1),
        "sprints": int(long_carries * 2 + minutes // 9),
        "minutes": minutes,
        "carry_distance_m": round(carry_dist * 0.9144, 0),
    }


# ── Helpers ───────────────────────────────────────────────────────

NAME_OVERRIDES = {
    "Javier Hernández Balcázar": "Chicharito",
    "Edwin van der Sar": "Van der Sar",
    "Dayotchanculle Upamecano": "Upamecano",
    "Alexis Mac Allister": "Mac Allister",
    "Alexis MacAllister": "Mac Allister",
}
PARTICLES = {"van", "der", "de", "la", "del", "di", "da", "dos", "le", "el"}


def short_name(row) -> str:
    name = str(row["player_name"]).strip()
    if name in NAME_OVERRIDES:
        return NAME_OVERRIDES[name]
    nick = row.get("player_nickname")
    if isinstance(nick, str) and nick.strip():
        return nick.strip()
    parts = name.split()
    if len(parts) <= 2:
        return name
    # Keep surname particles ("van der Sar", "de la Fuente")
    i = len(parts) - 1
    while i > 0 and parts[i - 1].lower() in PARTICLES:
        i -= 1
    return " ".join(parts[i:])


def starting_xi(lineup: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in lineup.iterrows():
        positions = r.get("positions") or []
        if not positions:
            continue
        first = positions[0]
        if first.get("start_reason") != "Starting XI":
            continue
        rows.append({
            "player_id": r["player_id"],
            "name": short_name(r),
            "number": int(r["jersey_number"]),
            "position": POSITION_MAP.get(first.get("position", ""), "CM"),
        })
    return pd.DataFrame(rows)


def average_positions(events: pd.DataFrame, xi: pd.DataFrame, flip: bool) -> list:
    """Average event location per starter; flipped for the team attacking right-to-left."""
    ev = events[events["location"].notna() & events["player_id"].isin(xi["player_id"])]
    # Ignore the shoot-out and, for regulation, weight all periods equally
    ev = ev[ev["period"] <= 4]
    loc = pd.DataFrame(ev["location"].tolist(), columns=["x", "y"], index=ev.index)
    ev = ev.assign(x=loc["x"], y=loc["y"])
    agg = ev.groupby("player_id")[["x", "y"]].median()

    players = []
    for _, p in xi.iterrows():
        if p["player_id"] not in agg.index:
            continue
        x, y = float(agg.loc[p["player_id"], "x"]), float(agg.loc[p["player_id"], "y"])
        if flip:
            x, y = 120 - x, 80 - y
        players.append({
            "name": p["name"], "number": p["number"],
            "x": round(min(120, max(0, x)), 1), "y": round(min(80, max(0, y)), 1),
            "position": p["position"],
        })
    return players


def nominal_formation(events: pd.DataFrame, team: str) -> str:
    """Formation named in the team's Starting XI event, e.g. 433 → '4-3-3'."""
    xi = events[(events["type"] == "Starting XI") & (events["team"] == team)]
    for _, r in xi.iterrows():
        tactics = r.get("tactics")
        if isinstance(tactics, dict) and tactics.get("formation"):
            digits = str(tactics["formation"])
            return "-".join(digits)
    return ""


def real_passes(events: pd.DataFrame, team: str, xi: pd.DataFrame) -> list:
    num = dict(zip(xi["player_id"], xi["number"]))
    ev = events[(events["type"] == "Pass") & (events["team"] == team) & (events["period"] <= 4)]
    ev = ev.sort_values(["period", "minute", "second"])
    out = []
    for _, r in ev.iterrows():
        passer = num.get(r["player_id"])
        recipient = num.get(r.get("pass_recipient_id"))
        if passer is None or recipient is None:
            continue
        loc = r["location"]
        end = r.get("pass_end_location")
        if not isinstance(loc, list) or not isinstance(end, list):
            continue
        outcome = r.get("pass_outcome")
        success = not isinstance(outcome, str)  # NaN outcome == completed
        out.append({
            "passer": int(passer), "receiver": int(recipient), "success": bool(success),
            "x": round(float(loc[0]), 1), "y": round(float(loc[1]), 1),
            "end_x": round(min(120, float(end[0])), 1), "end_y": round(min(80, float(end[1])), 1),
        })
        if len(out) >= MAX_PASSES:
            break
    return out


def synth_passes(players: list) -> list:
    """Plausible build-up passes from a formation snapshot (deterministic)."""
    by_pos = {}
    for p in players:
        by_pos.setdefault(p["position"], []).append(p)

    def pick(*codes):
        out = []
        for c in codes:
            out += by_pos.get(c, [])
        return out

    gk = pick("GK"); cbs = pick("CB"); fbs = pick("RB", "LB", "RWB", "LWB")
    mids = pick("CDM", "CM"); ams = pick("CAM", "CF"); wings = pick("RW", "LW", "RM", "LM"); sts = pick("ST")
    chains = []
    for a in gk:
        for b in cbs: chains.append((a, b, True))
    for a in cbs:
        for b in fbs + mids: chains.append((a, b, True))
    for a in fbs:
        for b in mids + wings: chains.append((a, b, True))
    for a in mids:
        for b in mids + ams + wings:
            if a is not b: chains.append((a, b, True))
        for b in sts: chains.append((a, b, False))
    for a in ams:
        for b in wings + sts: chains.append((a, b, True))
    for i, a in enumerate(wings):
        for b in sts + ams: chains.append((a, b, i % 2 == 0))
    for a in sts:
        for b in ams + wings[:1]: chains.append((a, b, True))
    out = []
    for a, b, ok in chains:
        out.append({"passer": a["number"], "receiver": b["number"], "success": ok,
                    "x": a["x"], "y": a["y"], "end_x": b["x"], "end_y": b["y"]})
    return out


def write(match: dict) -> None:
    path = OUT_DIR / f"{match['id']}.json"
    path.write_text(json.dumps(match, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}  ({len(match['players_a'])}v{len(match['players_b'])}, {len(match['passes'])} passes)")


_EVENT_CACHE: dict = {}


def build_real(fx: dict) -> dict:
    from statsbombpy import sb

    print(f"[{fx['id']}] fetching StatsBomb match {fx['match_id']} …")
    events = sb.events(match_id=fx["match_id"])
    lineups = sb.lineups(match_id=fx["match_id"])
    _EVENT_CACHE[fx["id"]] = (events, lineups)
    xi_a = starting_xi(lineups[fx["team_a"]])
    xi_b = starting_xi(lineups[fx["team_b"]])
    players_a = average_positions(events, xi_a, flip=False)
    players_b = average_positions(events, xi_b, flip=True)
    passes = real_passes(events, fx["team_a"], xi_a)
    return {
        "id": fx["id"], "title": fx["title"], "subtitle": fx["subtitle"],
        "competition": fx["competition"], "date": fx["date"],
        "team_a": {"name": fx["team_a"], "color": TEAM_A_COLOR, "formation": nominal_formation(events, fx["team_a"])},
        "team_b": {"name": fx["team_b"], "color": TEAM_B_COLOR, "formation": nominal_formation(events, fx["team_b"])},
        "score": {"a": fx["score"][0], "b": fx["score"][1]},
        "players_a": players_a, "players_b": players_b, "passes": passes,
        "ball": {"x": 60, "y": 40},
        "match_info": {
            "home_team": fx["team_a"], "away_team": fx["team_b"],
            "score_home": fx["score"][0], "score_away": fx["score"][1],
            "minute": fx["minute"], "competition": fx["competition"], "date": fx["date"],
        },
        "source": {
            "kind": "statsbomb",
            "match_id": fx["match_id"],
            "note": "Positions are each starter's median event location; passes are the real events. Data © StatsBomb (open data, non-commercial, attribution required).",
        },
    }


def build_reconstructed(fx: dict) -> dict:
    def players(rows):
        return [{"name": n, "number": num, "position": pos, "x": x, "y": y} for n, num, pos, x, y in rows]
    pa, pb = players(fx["players_a"]), players(fx["players_b"])
    return {
        "id": fx["id"], "title": fx["title"], "subtitle": fx["subtitle"],
        "competition": fx["competition"], "date": fx["date"],
        "team_a": {"name": fx["team_a"], "color": TEAM_A_COLOR, "formation": fx.get("formation_a", "")},
        "team_b": {"name": fx["team_b"], "color": TEAM_B_COLOR, "formation": fx.get("formation_b", "")},
        "score": {"a": fx["score"][0], "b": fx["score"][1]},
        "players_a": pa, "players_b": pb, "passes": synth_passes(pa),
        "ball": {"x": 60, "y": 40},
        "match_info": {
            "home_team": fx["team_a"], "away_team": fx["team_b"],
            "score_home": fx["score"][0], "score_away": fx["score"][1],
            "minute": fx["minute"], "competition": fx["competition"], "date": fx["date"],
        },
        "source": {"kind": "reconstructed", "match_id": None, "note": fx["note"]},
    }


def main() -> int:
    only = set(sys.argv[1:])
    for fx in RECONSTRUCTED:
        if only and fx["id"] not in only:
            continue
        write(build_reconstructed(fx))
    for fx in REAL_FIXTURES:
        if only and fx["id"] not in only:
            continue
        try:
            write(build_real(fx))
        except Exception as exc:  # keep going so one bad fetch doesn't block the rest
            print(f"  !! {fx['id']} failed: {exc}")
    # demo players
    players_out = []
    fixtures_by_id = {fx["id"]: fx for fx in REAL_FIXTURES}
    for dp in DEMO_PLAYERS:
        if only and dp["match"] not in only:
            continue
        cached = _EVENT_CACHE.get(dp["match"])
        if cached is None:
            try:
                from statsbombpy import sb
                fx = fixtures_by_id[dp["match"]]
                cached = (sb.events(match_id=fx["match_id"]), sb.lineups(match_id=fx["match_id"]))
                _EVENT_CACHE[dp["match"]] = cached
            except Exception as exc:
                print(f"  !! player {dp['id']}: {exc}")
                continue
        events, lineups = cached
        try:
            stats = player_stats(events, lineups[dp["team"]], dp["number"])
        except Exception as exc:
            print(f"  !! player {dp['id']}: {exc}")
            continue
        fx = fixtures_by_id[dp["match"]]
        players_out.append({
            **dp, "stats": stats, "match_title": fx["title"], "match_subtitle": fx["subtitle"],
            "source": {"kind": "statsbomb",
                       "note": "Counts from StatsBomb events; distance and sprints are estimates (event data has no tracking)."},
        })
    for dp in RECONSTRUCTED_PLAYERS:
        fx = next(f for f in RECONSTRUCTED if f["id"] == dp["match"])
        players_out.append({
            **{k: v for k, v in dp.items() if k != "note"},
            "match_title": fx["title"], "match_subtitle": fx["subtitle"],
            "source": {"kind": "reconstructed", "note": dp["note"]},
        })
    order = ["lamine-2025", "messi-2022", "mbappe-2022", "enzo-2022", "griezmann-2022",
             "messi-2017", "xavi-2011", "rooney-2011", "gerrard-2005", "kaka-2005"]
    players_out.sort(key=lambda q: order.index(q["id"]) if q["id"] in order else 99)
    if players_out:
        (OUT_DIR / "players.json").write_text(json.dumps(players_out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"players: {len(players_out)} written")

    # index
    index = []
    for path in sorted(OUT_DIR.glob("*.json")):
        if path.name in ("index.json", "players.json"):
            continue
        m = json.loads(path.read_text(encoding="utf-8"))
        index.append({
            "id": m["id"], "title": m["title"], "subtitle": m["subtitle"], "date": m["date"],
            "competition": m["competition"], "team_a": m["team_a"]["name"], "team_b": m["team_b"]["name"],
            "score": m["score"], "source_kind": m["source"]["kind"],
            "formation_a": m["team_a"].get("formation", ""), "formation_b": m["team_b"].get("formation", ""),
            "players": len(m["players_a"]) + len(m["players_b"]), "passes": len(m["passes"]),
        })
    order = ["clasico-2025", "wc2022-final", "clasico-2017", "ucl2011-final", "ucl2005-final", "liverpool-7-0"]
    index.sort(key=lambda m: order.index(m["id"]) if m["id"] in order else 99)
    (OUT_DIR / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"index: {len(index)} matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
