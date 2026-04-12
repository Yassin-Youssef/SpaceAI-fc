"""
SpaceAI FC - El Clásico Demo Data
====================================
Pre-built match data for instant demo in every feature.
Barcelona (4-2-3-1) vs Real Madrid (4-3-3), La Liga.
"""

BARCA_PLAYERS = [
    {"name": "ter Stegen",  "number": 1,  "x": 5.0,  "y": 40.0, "position": "GK"},
    {"name": "Koundé",      "number": 23, "x": 30.0, "y": 70.0, "position": "RB"},
    {"name": "Araújo",      "number": 4,  "x": 25.0, "y": 52.0, "position": "CB"},
    {"name": "Cubarsí",     "number": 2,  "x": 25.0, "y": 28.0, "position": "CB"},
    {"name": "Baldé",       "number": 3,  "x": 30.0, "y": 10.0, "position": "LB"},
    {"name": "Pedri",       "number": 8,  "x": 45.0, "y": 48.0, "position": "CM"},
    {"name": "De Jong",     "number": 21, "x": 45.0, "y": 32.0, "position": "CM"},
    {"name": "Lamine",      "number": 19, "x": 65.0, "y": 68.0, "position": "RW"},
    {"name": "Gavi",        "number": 6,  "x": 60.0, "y": 40.0, "position": "CAM"},
    {"name": "Raphinha",    "number": 11, "x": 65.0, "y": 12.0, "position": "LW"},
    {"name": "Lewandowski", "number": 9,  "x": 80.0, "y": 40.0, "position": "ST"},
]

MADRID_PLAYERS = [
    {"name": "Courtois",   "number": 1,  "x": 115.0, "y": 40.0, "position": "GK"},
    {"name": "Carvajal",   "number": 2,  "x": 90.0,  "y": 70.0, "position": "RB"},
    {"name": "Rüdiger",    "number": 22, "x": 93.0,  "y": 52.0, "position": "CB"},
    {"name": "Militão",    "number": 3,  "x": 93.0,  "y": 28.0, "position": "CB"},
    {"name": "Mendy",      "number": 23, "x": 90.0,  "y": 10.0, "position": "LB"},
    {"name": "Tchouaméni", "number": 14, "x": 78.0,  "y": 40.0, "position": "CDM"},
    {"name": "Valverde",   "number": 15, "x": 70.0,  "y": 55.0, "position": "CM"},
    {"name": "Bellingham", "number": 5,  "x": 70.0,  "y": 25.0, "position": "CM"},
    {"name": "Rodrygo",    "number": 11, "x": 55.0,  "y": 65.0, "position": "RW"},
    {"name": "Mbappé",     "number": 7,  "x": 50.0,  "y": 40.0, "position": "ST"},
    {"name": "Vinícius",   "number": 20, "x": 55.0,  "y": 15.0, "position": "LW"},
]

DEMO_PASSES = [
    {"passer": 1,  "receiver": 4,  "success": True,  "x": 5.0,  "y": 40.0, "end_x": 25.0, "end_y": 52.0},
    {"passer": 1,  "receiver": 2,  "success": True,  "x": 5.0,  "y": 40.0, "end_x": 25.0, "end_y": 28.0},
    {"passer": 4,  "receiver": 8,  "success": True,  "x": 25.0, "y": 52.0, "end_x": 45.0, "end_y": 48.0},
    {"passer": 4,  "receiver": 21, "success": True,  "x": 25.0, "y": 52.0, "end_x": 45.0, "end_y": 32.0},
    {"passer": 4,  "receiver": 23, "success": True,  "x": 25.0, "y": 52.0, "end_x": 30.0, "end_y": 70.0},
    {"passer": 2,  "receiver": 21, "success": True,  "x": 25.0, "y": 28.0, "end_x": 45.0, "end_y": 32.0},
    {"passer": 2,  "receiver": 3,  "success": True,  "x": 25.0, "y": 28.0, "end_x": 30.0, "end_y": 10.0},
    {"passer": 23, "receiver": 19, "success": True,  "x": 30.0, "y": 70.0, "end_x": 65.0, "end_y": 68.0},
    {"passer": 23, "receiver": 8,  "success": True,  "x": 30.0, "y": 70.0, "end_x": 45.0, "end_y": 48.0},
    {"passer": 3,  "receiver": 11, "success": True,  "x": 30.0, "y": 10.0, "end_x": 65.0, "end_y": 12.0},
    {"passer": 3,  "receiver": 21, "success": True,  "x": 30.0, "y": 10.0, "end_x": 45.0, "end_y": 32.0},
    {"passer": 8,  "receiver": 6,  "success": True,  "x": 45.0, "y": 48.0, "end_x": 60.0, "end_y": 40.0},
    {"passer": 8,  "receiver": 19, "success": True,  "x": 45.0, "y": 48.0, "end_x": 65.0, "end_y": 68.0},
    {"passer": 8,  "receiver": 21, "success": True,  "x": 45.0, "y": 48.0, "end_x": 45.0, "end_y": 32.0},
    {"passer": 8,  "receiver": 9,  "success": True,  "x": 45.0, "y": 48.0, "end_x": 80.0, "end_y": 40.0},
    {"passer": 8,  "receiver": 11, "success": True,  "x": 45.0, "y": 48.0, "end_x": 65.0, "end_y": 12.0},
    {"passer": 21, "receiver": 8,  "success": True,  "x": 45.0, "y": 32.0, "end_x": 45.0, "end_y": 48.0},
    {"passer": 21, "receiver": 6,  "success": True,  "x": 45.0, "y": 32.0, "end_x": 60.0, "end_y": 40.0},
    {"passer": 21, "receiver": 11, "success": True,  "x": 45.0, "y": 32.0, "end_x": 65.0, "end_y": 12.0},
    {"passer": 6,  "receiver": 9,  "success": True,  "x": 60.0, "y": 40.0, "end_x": 80.0, "end_y": 40.0},
    {"passer": 6,  "receiver": 19, "success": True,  "x": 60.0, "y": 40.0, "end_x": 65.0, "end_y": 68.0},
    {"passer": 6,  "receiver": 8,  "success": True,  "x": 60.0, "y": 40.0, "end_x": 45.0, "end_y": 48.0},
    {"passer": 6,  "receiver": 11, "success": False, "x": 60.0, "y": 40.0, "end_x": 65.0, "end_y": 12.0},
    {"passer": 19, "receiver": 9,  "success": True,  "x": 65.0, "y": 68.0, "end_x": 80.0, "end_y": 40.0},
    {"passer": 19, "receiver": 6,  "success": True,  "x": 65.0, "y": 68.0, "end_x": 60.0, "end_y": 40.0},
    {"passer": 19, "receiver": 8,  "success": False, "x": 65.0, "y": 68.0, "end_x": 45.0, "end_y": 48.0},
    {"passer": 11, "receiver": 9,  "success": True,  "x": 65.0, "y": 12.0, "end_x": 80.0, "end_y": 40.0},
    {"passer": 11, "receiver": 6,  "success": True,  "x": 65.0, "y": 12.0, "end_x": 60.0, "end_y": 40.0},
    {"passer": 9,  "receiver": 6,  "success": True,  "x": 80.0, "y": 40.0, "end_x": 60.0, "end_y": 40.0},
    {"passer": 9,  "receiver": 19, "success": True,  "x": 80.0, "y": 40.0, "end_x": 65.0, "end_y": 68.0},
]

DEMO_MATCH_INFO = {
    "home_team": "FC Barcelona",
    "away_team": "Real Madrid",
    "score_home": 2,
    "score_away": 1,
    "minute": 65,
    "competition": "La Liga",
    "date": "2026-04-07",
}

# Passes as simple text format for text areas: "from,to,success,x,y"
DEMO_PASSES_TEXT = "\n".join(
    f"{p['passer']},{p['receiver']},{1 if p['success'] else 0},{p['x']},{p['y']}"
    for p in DEMO_PASSES
)

# Simple pass text for pass network (just from,to)
DEMO_PASSES_SIMPLE_TEXT = "\n".join(
    f"{p['passer']},{p['receiver']}" for p in DEMO_PASSES
)

# Positions available in all dropdowns
POSITIONS = ["GK", "CB", "RB", "LB", "RWB", "LWB", "CDM", "CM", "CAM", "RW", "LW", "ST", "CF"]

# Formations
FORMATIONS = ["4-3-3", "4-2-3-1", "3-5-2", "4-4-2", "5-4-1", "5-3-2", "4-1-4-1", "3-4-3"]

# Tactical situations — must match knowledge graph node names
SITUATIONS = [
    "low_block", "high_press", "counter_attack", "possession_play",
    "wide_play", "midfield_overload", "park_the_bus", "high_line",
    "transition_moment", "set_piece_threat",
]

# Available tactical presets for simulation
TACTICS = ["high_press", "low_block", "wide_play", "narrow_play", "counter_attack", "possession"]
