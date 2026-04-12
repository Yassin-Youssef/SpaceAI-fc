"""
SpaceAI FC - API Test Script
==============================
Sends sample requests to every endpoint using El Clásico demo data.
Run AFTER starting the server:
    uvicorn api.main:app --reload --port 8000

Usage:
    python test_api.py
    python test_api.py --base-url http://localhost:8000
    python test_api.py --endpoint health          # single endpoint
    python test_api.py --skip-slow                # skip full pipeline
"""

import argparse
import json
import sys
import httpx

# ── Demo data (El Clásico) ────────────────────────────────────────

BARCELONA = [
    {"name": "ter Stegen",  "number": 1,  "x": 5,  "y": 40, "position": "GK"},
    {"name": "Koundé",      "number": 23, "x": 30, "y": 70, "position": "RB"},
    {"name": "Araújo",      "number": 4,  "x": 25, "y": 52, "position": "CB"},
    {"name": "Cubarsí",     "number": 2,  "x": 25, "y": 28, "position": "CB"},
    {"name": "Baldé",       "number": 3,  "x": 30, "y": 10, "position": "LB"},
    {"name": "Pedri",       "number": 8,  "x": 45, "y": 48, "position": "CM"},
    {"name": "De Jong",     "number": 21, "x": 45, "y": 32, "position": "CM"},
    {"name": "Lamine",      "number": 19, "x": 65, "y": 68, "position": "RW"},
    {"name": "Gavi",        "number": 6,  "x": 60, "y": 40, "position": "CAM"},
    {"name": "Raphinha",    "number": 11, "x": 65, "y": 12, "position": "LW"},
    {"name": "Lewandowski", "number": 9,  "x": 80, "y": 40, "position": "ST"},
]

REAL_MADRID = [
    {"name": "Courtois",   "number": 1,  "x": 115, "y": 40, "position": "GK"},
    {"name": "Carvajal",   "number": 2,  "x": 90,  "y": 70, "position": "RB"},
    {"name": "Rüdiger",    "number": 22, "x": 93,  "y": 52, "position": "CB"},
    {"name": "Militão",    "number": 3,  "x": 93,  "y": 28, "position": "CB"},
    {"name": "Mendy",      "number": 23, "x": 90,  "y": 10, "position": "LB"},
    {"name": "Tchouaméni", "number": 14, "x": 78,  "y": 40, "position": "CDM"},
    {"name": "Valverde",   "number": 15, "x": 70,  "y": 55, "position": "CM"},
    {"name": "Bellingham", "number": 5,  "x": 70,  "y": 25, "position": "CM"},
    {"name": "Rodrygo",    "number": 11, "x": 55,  "y": 65, "position": "RW"},
    {"name": "Mbappé",     "number": 7,  "x": 50,  "y": 40, "position": "ST"},
    {"name": "Vinícius",   "number": 20, "x": 55,  "y": 15, "position": "LW"},
]

PASSES = [
    {"passer": 1,  "receiver": 4,  "success": True,  "x": 5,  "y": 40, "end_x": 25, "end_y": 52},
    {"passer": 4,  "receiver": 8,  "success": True,  "x": 25, "y": 52, "end_x": 45, "end_y": 48},
    {"passer": 8,  "receiver": 6,  "success": True,  "x": 45, "y": 48, "end_x": 60, "end_y": 40},
    {"passer": 6,  "receiver": 9,  "success": True,  "x": 60, "y": 40, "end_x": 80, "end_y": 40},
    {"passer": 9,  "receiver": 19, "success": True,  "x": 80, "y": 40, "end_x": 65, "end_y": 68},
    {"passer": 19, "receiver": 8,  "success": False, "x": 65, "y": 68, "end_x": 45, "end_y": 48},
    {"passer": 2,  "receiver": 21, "success": True,  "x": 25, "y": 28, "end_x": 45, "end_y": 32},
    {"passer": 21, "receiver": 6,  "success": True,  "x": 45, "y": 32, "end_x": 60, "end_y": 40},
    {"passer": 8,  "receiver": 11, "success": True,  "x": 45, "y": 48, "end_x": 65, "end_y": 12},
    {"passer": 11, "receiver": 9,  "success": True,  "x": 65, "y": 12, "end_x": 80, "end_y": 40},
]

MATCH_INFO = {
    "home_team": "FC Barcelona",
    "away_team": "Real Madrid",
    "score_home": 2,
    "score_away": 1,
    "minute": 65,
    "competition": "La Liga",
    "date": "2026-04-07",
}

BASE_BODY = {
    "input_type": "manual",
    "match_info": MATCH_INFO,
    "team_a": BARCELONA,
    "team_b": REAL_MADRID,
    "team_a_name": "FC Barcelona",
    "team_b_name": "Real Madrid",
    "team_a_color": "#a50044",
    "team_b_color": "#ffffff",
    "ball_x": 60.0,
    "ball_y": 40.0,
    "passes": PASSES,
}


# ── Test helpers ─────────────────────────────────────────────────

def _print_result(name: str, resp: httpx.Response, preview_keys: list = None):
    ok = "✓" if resp.status_code < 300 else "✗"
    print(f"  {ok} [{resp.status_code}] {name}")
    if resp.status_code >= 300:
        print(f"      ERROR: {resp.text[:300]}")
        return

    try:
        data = resp.json()
        if preview_keys:
            for k in preview_keys:
                val = data.get(k, "—")
                if isinstance(val, (dict, list)):
                    val = str(val)[:120]
                print(f"      {k}: {val}")
        else:
            print(f"      keys: {list(data.keys())[:8]}")
    except Exception:
        print(f"      (non-JSON response, {len(resp.content)} bytes)")


def _section(title: str):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ── Tests ─────────────────────────────────────────────────────────

def test_health(client, base):
    _section("Utility")
    r = client.get(f"{base}/api/health")
    _print_result("/api/health", r, ["status", "version", "engine_phases", "llm_available"])
    r = client.get(f"{base}/api/features")
    _print_result("/api/features", r, ["total"])


def test_pass_network(client, base):
    _section("Pass Network")
    body = {**BASE_BODY, "min_passes": 1}
    r = client.post(f"{base}/api/pass-network", json=body, timeout=60)
    _print_result("/api/pass-network", r, ["total_passes", "key_distributor", "weak_links"])

    # With sequence
    body_seq = {**body, "sequence": [2, 4, 8, 6, 19, 9]}
    r2 = client.post(f"{base}/api/pass-network", json=body_seq, timeout=60)
    _print_result("/api/pass-network (with sequence)", r2, ["total_passes"])


def test_space_control(client, base):
    _section("Space Control")
    body = {**BASE_BODY, "mode": "both"}
    r = client.post(f"{base}/api/space-control", json=body, timeout=60)
    _print_result("/api/space-control", r, ["team_a_control", "team_b_control", "midfield_control"])


def test_formation(client, base):
    _section("Formation Detection")
    r = client.post(f"{base}/api/formation", json=BASE_BODY, timeout=60)
    _print_result("/api/formation", r, ["team_a_formation", "team_a_confidence",
                                         "team_b_formation", "team_b_confidence"])


def test_roles(client, base):
    _section("Player Roles")
    r = client.post(f"{base}/api/roles", json=BASE_BODY, timeout=60)
    _print_result("/api/roles", r, ["team_a_roles"])
    if r.status_code == 200:
        roles = r.json().get("team_a_roles", [])[:3]
        for role in roles:
            print(f"      #{role['number']} {role['name']}: {role['role']} ({role['confidence']:.0%})")


def test_press_resistance(client, base):
    _section("Press Resistance")
    r = client.post(f"{base}/api/press-resistance", json=BASE_BODY, timeout=60)
    _print_result("/api/press-resistance", r, ["press_resistance_score", "escape_rate",
                                                "passes_under_pressure"])


def test_patterns(client, base):
    _section("Tactical Patterns")
    body = {**BASE_BODY, "analyze_team": "both"}
    r = client.post(f"{base}/api/patterns", json=body, timeout=60)
    _print_result("/api/patterns", r, ["team_a_patterns"])
    if r.status_code == 200:
        for p in r.json().get("team_a_patterns", [])[:3]:
            print(f"      {p['name']}: detected={p['detected']} conf={p['confidence']:.2f}")


def test_intelligence(client, base):
    _section("Intelligence")
    r = client.post(f"{base}/api/knowledge-graph",
                    json={"formation": "4-3-3", "situation": "high_press"}, timeout=30)
    _print_result("/api/knowledge-graph", r, ["formation", "counter_strategies", "weaknesses"])

    r2 = client.post(f"{base}/api/reasoning", json=BASE_BODY, timeout=90)
    _print_result("/api/reasoning", r2, ["swot"])

    r3 = client.post(f"{base}/api/recommendations",
                     json={"team_name": "FC Barcelona", "opponent_name": "Real Madrid"}, timeout=30)
    _print_result("/api/recommendations", r3, ["recommendations"])


def test_explanation(client, base):
    _section("Explanation")
    body = {
        "mode": "template",
        "team_name": "FC Barcelona",
        "opponent_name": "Real Madrid",
        "match_info": MATCH_INFO,
    }
    r = client.post(f"{base}/api/explanation", json=body, timeout=30)
    _print_result("/api/explanation", r, ["mode"])
    if r.status_code == 200:
        text = r.json().get("text", "")
        print(f"      text preview: {text[:200]}...")


def test_video(client, base):
    _section("Video (synthetic demo)")
    r = client.post(f"{base}/api/video/youtube",
                    json={"url": "https://youtube.com/watch?v=demo", "demo_mode": True}, timeout=30)
    _print_result("/api/video/youtube (demo)", r, ["tracking_data"])


def test_simulation(client, base):
    _section("Simulation & RL")
    body = {"team_size": 5, "tactic_a": "possession", "tactic_b": "low_block", "steps": 200}
    r = client.post(f"{base}/api/simulation/run", json=body, timeout=60)
    _print_result("/api/simulation/run", r, ["goals_a", "goals_b", "possession_a"])

    compare_body = {
        "team_size": 5,
        "tactic_a": "high_press", "tactic_b": "low_block",
        "tactic_a2": "possession", "tactic_b2": "counter_attack",
        "runs": 2, "steps_per_run": 150,
    }
    r2 = client.post(f"{base}/api/simulation/compare", json=compare_body, timeout=120)
    _print_result("/api/simulation/compare", r2, ["verdict"])

    state = {
        "own_formation": 1, "opp_formation": 3,
        "space_control": 45.0, "press_resistance": 38.0,
        "score_diff": -1, "minute": 72, "possession": 55.0,
    }
    r3 = client.post(f"{base}/api/rl/predict", json=state, timeout=30)
    _print_result("/api/rl/predict", r3, ["action_name", "available"])


def test_ask(client, base):
    _section("Ask SpaceAI")
    r = client.post(f"{base}/api/ask",
                    json={"question": "What are the weaknesses of a 4-3-3 against a high press?",
                          "team_name": "FC Barcelona", "opponent_name": "Real Madrid"},
                    timeout=30)
    _print_result("/api/ask", r, ["mode"])
    if r.status_code == 200:
        print(f"      answer: {r.json().get('answer', '')[:300]}")


def test_full_pipeline(client, base):
    _section("Full Pipeline (POST /api/analyze)")
    print("  [Running full pipeline — this may take 15-30s]")
    r = client.post(f"{base}/api/analyze", json=BASE_BODY, timeout=180)
    _print_result("/api/analyze", r, ["success"])
    if r.status_code == 200:
        data = r.json()
        print(f"      formation A: {data.get('formation', {}).get('team_a_formation')}")
        print(f"      space control A: {data.get('space_control', {}).get('team_a_control')}%")
        print(f"      pass total: {data.get('pass_network', {}).get('total_passes')}")
        print(f"      press score: {data.get('press_resistance', {}).get('press_resistance_score')}")
        print(f"      visuals returned: {len(data.get('visualizations', []))}")


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SpaceAI FC API test suite")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--endpoint", default="all",
                        help="Run a single endpoint test: health, pass_network, space_control, "
                             "formation, roles, press_resistance, patterns, intelligence, "
                             "explanation, video, simulation, ask, full")
    parser.add_argument("--skip-slow", action="store_true",
                        help="Skip full pipeline test (/api/analyze)")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")

    print(f"\n{'='*55}")
    print(f"  SpaceAI FC API Test Suite")
    print(f"  Target: {base}")
    print(f"{'='*55}")

    with httpx.Client() as client:
        # Quick connectivity check
        try:
            client.get(f"{base}/api/health", timeout=5)
        except httpx.ConnectError:
            print(f"\n  ERROR: Cannot connect to {base}")
            print("  Make sure the server is running:")
            print("    uvicorn api.main:app --reload --port 8000\n")
            sys.exit(1)

        ep = args.endpoint
        run_all = ep == "all"

        if run_all or ep == "health":       test_health(client, base)
        if run_all or ep == "pass_network": test_pass_network(client, base)
        if run_all or ep == "space_control":test_space_control(client, base)
        if run_all or ep == "formation":    test_formation(client, base)
        if run_all or ep == "roles":        test_roles(client, base)
        if run_all or ep == "press_resistance": test_press_resistance(client, base)
        if run_all or ep == "patterns":     test_patterns(client, base)
        if run_all or ep == "intelligence": test_intelligence(client, base)
        if run_all or ep == "explanation":  test_explanation(client, base)
        if run_all or ep == "video":        test_video(client, base)
        if run_all or ep == "simulation":   test_simulation(client, base)
        if run_all or ep == "ask":          test_ask(client, base)

        if (run_all and not args.skip_slow) or ep == "full":
            test_full_pipeline(client, base)
        elif run_all and args.skip_slow:
            print("\n  [Skipped /api/analyze — use --endpoint full to run it separately]")

    print(f"\n{'='*55}")
    print("  Tests complete.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
