"""
SpaceAI FC - Explanation Layer
================================
Converts all analysis into natural language tactical explanations.
Two modes: template-based (always available) and LLM-powered (optional).
"""

import os
import textwrap


class ExplanationLayer:
    """
    Generates natural language tactical explanations from structured analysis.
    
    Modes:
        - Template: uses Python f-strings to produce professional-sounding reports
        - LLM: uses Anthropic Claude API for richer, more nuanced explanations
          (requires ANTHROPIC_API_KEY environment variable)
    """
    
    def __init__(self, mode="template"):
        """
        Parameters:
            mode: "template" or "llm"
        """
        self.mode = mode
        self.match_info = {}
        self.report_data = {}
        self.swot_results = {}
        self.recommendations = []
        self.team_name = "Team"
        self.opponent_name = "Opponent"
    
    # ── Data input ──────────────────────────────────────────────
    
    def set_data(self, match_info=None, report_data=None,
                 swot_results=None, recommendations=None,
                 team_name="Team", opponent_name="Opponent"):
        """
        Set all analysis data for explanation generation.
        
        Parameters:
            match_info: dict with 'home_team', 'away_team', 'score_home', etc.
            report_data: dict from MatchReport.generate_report()
            swot_results: dict from TacticalReasoner.reason()
            recommendations: list from StrategyRecommender.recommend()
        """
        self.match_info = match_info or {}
        self.report_data = report_data or {}
        self.swot_results = swot_results or {}
        self.recommendations = recommendations or []
        self.team_name = team_name
        self.opponent_name = opponent_name
    
    # ── Generation ──────────────────────────────────────────────
    
    def generate(self):
        """
        Generate the tactical explanation.
        
        Returns:
            str: multi-paragraph tactical analysis text
        """
        if self.mode == "llm":
            return self._generate_llm()
        return self._generate_template()
    
    # ── Template mode ───────────────────────────────────────────
    
    def _generate_template(self):
        """Generate explanation using Python f-string templates."""
        sections = []
        
        sections.append(self._template_overview())
        sections.append(self._template_tactical_situation())
        sections.append(self._template_strengths_weaknesses())
        sections.append(self._template_recommendations())
        sections.append(self._template_conclusion())
        
        return "\n\n".join(s for s in sections if s)
    
    def _template_overview(self):
        """Match overview paragraph."""
        mi = self.match_info
        rd = self.report_data
        
        home = mi.get('home_team', self.team_name)
        away = mi.get('away_team', self.opponent_name)
        score_h = mi.get('score_home', 0)
        score_a = mi.get('score_away', 0)
        minute = mi.get('minute', 90)
        comp = mi.get('competition', 'the match')
        
        # Formations
        form_a = rd.get('team_a', {}).get('formation', 'unknown')
        form_b = rd.get('team_b', {}).get('formation', 'unknown')
        
        # Pass analysis
        pa = rd.get('pass_analysis', {})
        total_passes = pa.get('total_passes', 0)
        kd = pa.get('key_distributor', {})
        kd_name = kd.get('name', 'the key distributor')
        
        overview = (
            f"In this {comp} fixture between {home} and {away}, "
            f"the scoreline reads {score_h}-{score_a} at the {minute}th minute. "
            f"{home} are deployed in a {form_a} formation while {away} operate in a {form_b}. "
        )
        
        if total_passes > 0:
            overview += (
                f"{home} have completed {total_passes} passes, "
                f"with {kd_name} acting as the primary distributor through the centre of the pitch. "
            )
        
        # Space control
        sa = rd.get('space_analysis', {})
        overall = sa.get('overall', {})
        ctrl_a = overall.get('team_a_control', 50)
        ctrl_b = overall.get('team_b_control', 50)
        
        if ctrl_a > 55:
            overview += f"{home} are dominating territorial control at {ctrl_a}%, applying sustained pressure. "
        elif ctrl_b > 55:
            overview += f"However, {away} currently controls {ctrl_b}% of the territory, putting {home} under pressure. "
        else:
            overview += f"Territorial control is relatively balanced ({ctrl_a}% vs {ctrl_b}%). "
        
        return overview.strip()
    
    def _template_tactical_situation(self):
        """Tactical situation assessment paragraph."""
        swot = self.swot_results
        situations = list(set(swot.get('situations', [])))
        
        if not situations:
            return (
                f"The tactical picture is balanced, with neither side establishing "
                f"a clear structural advantage. Both teams are operating within "
                f"their standard tactical setups without significant deviations."
            )
        
        situation_descriptions = {
            'low_block': f"a low defensive block, sitting deep and compact",
            'high_press': f"a high press, putting intense pressure on the build-up",
            'park_the_bus': f"an ultra-defensive posture, parking the bus",
            'high_line': f"a high defensive line, pushing play into the opponent's half",
            'midfield_overload': f"midfield dominance through numerical overloads",
            'counter_attack': f"counter-attacking opportunities on the break",
            'possession_play': f"sustained possession to control the tempo",
            'wide_play': f"wide attacking play to stretch the defence",
            'single_buildup_route': f"a predictable build-up route that opponents can target",
        }
        
        situation_text = "The key tactical situations identified are: "
        desc_parts = []
        for s in situations[:3]:
            desc = situation_descriptions.get(s, s.replace('_', ' '))
            desc_parts.append(desc)
        
        situation_text += ", and ".join(desc_parts) + ". "
        
        # Press resistance context
        pr = self.report_data.get('press_resistance', {})
        if pr:
            score = pr.get('press_resistance_score', 50)
            if score >= 70:
                situation_text += (
                    f"{self.team_name} are showing excellent press resistance with a score of "
                    f"{score:.0f}/100, comfortably playing through the opponent's pressing structure. "
                )
            elif score < 45:
                situation_text += (
                    f"Crucially, {self.team_name}'s press resistance is concerning at "
                    f"{score:.0f}/100, suggesting they are struggling to play out from the back effectively. "
                )
        
        return situation_text.strip()
    
    def _template_strengths_weaknesses(self):
        """Strengths and weaknesses paragraph."""
        swot = self.swot_results
        strengths = swot.get('strengths', [])
        weaknesses = swot.get('weaknesses', [])
        opportunities = swot.get('opportunities', [])
        threats = swot.get('threats', [])
        
        parts = []
        
        if strengths:
            top_s = strengths[:2]
            strength_text = f"{self.team_name}'s key strengths include "
            strength_text += " and ".join(s['description'].lower() for s in top_s)
            strength_text += ". "
            parts.append(strength_text)
        
        if weaknesses:
            top_w = weaknesses[:2]
            weakness_text = "However, there are concerns: "
            weakness_text += "; ".join(w['description'].lower() for w in top_w)
            weakness_text += ". "
            parts.append(weakness_text)
        
        if opportunities:
            top_o = opportunities[:1]
            opp_text = f"An opportunity exists as "
            opp_text += top_o[0]['description'].lower()
            opp_text += ", which can be exploited. "
            parts.append(opp_text)
        
        if threats:
            top_t = threats[:2]
            threat_text = "The main threats to be aware of are: "
            threat_text += " and ".join(t['description'].lower() for t in top_t)
            threat_text += ". "
            parts.append(threat_text)
        
        if not parts:
            return "No significant tactical imbalances have been identified at this point."
        
        return "".join(parts).strip()
    
    def _template_recommendations(self):
        """Recommendations paragraph."""
        recs = self.recommendations
        if not recs:
            return "No specific tactical changes are recommended at this time. The current approach is working well."
        
        high = [r for r in recs if r['priority'] == 'high']
        medium = [r for r in recs if r['priority'] == 'medium']
        
        parts = []
        
        if high:
            parts.append(
                f"The most critical tactical adjustments needed are: "
            )
            for r in high[:2]:
                parts.append(f"{r['description']}. ")
        
        if medium:
            parts.append("Additionally, ")
            for r in medium[:2]:
                parts.append(f"{r['description'].lower()}. ")
        
        if not high and not medium:
            low = [r for r in recs if r['priority'] == 'low']
            if low:
                parts.append(
                    f"Minor adjustments could include: {low[0]['description'].lower()}. "
                )
        
        return "".join(parts).strip()
    
    def _template_conclusion(self):
        """Closing paragraph."""
        mi = self.match_info
        home = mi.get('home_team', self.team_name)
        away = mi.get('away_team', self.opponent_name)
        minute = mi.get('minute', 90)
        
        recs = self.recommendations
        high_count = sum(1 for r in recs if r['priority'] == 'high')
        
        if high_count > 2:
            urgency = "urgently"
        elif high_count > 0:
            urgency = "promptly"
        else:
            urgency = "to fine-tune the approach"
        
        return (
            f"Overall, {home} have the tactical structure to compete in this match, "
            f"but the coaching staff should act {urgency} to address the identified issues. "
            f"Implementing these changes in the next phase of play could significantly "
            f"alter the tactical balance against {away}."
        )
    
    # ── LLM mode ────────────────────────────────────────────────
    
    def _generate_llm(self):
        """Generate explanation using Anthropic Claude API."""
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        
        if not api_key:
            print("[LLM mode] No ANTHROPIC_API_KEY found — falling back to template mode.")
            return self._generate_template()
        
        try:
            import anthropic
        except ImportError:
            print("[LLM mode] anthropic library not installed — falling back to template mode.")
            return self._generate_template()
        
        # Build prompt
        system_prompt = (
            "You are a world-class football tactical analyst working for a top European club. "
            "You have deep expertise in formations, pressing structures, space control, and match strategy. "
            "Write in a professional, analytical tone — like a detailed half-time team talk or a post-match tactical briefing. "
            "Be specific about players, formations, and tactical concepts. "
            "Structure your response in 3-5 paragraphs covering: match overview, tactical situation, "
            "key strengths and vulnerabilities, and specific recommendations."
        )
        
        data_summary = self._build_data_summary()
        
        user_prompt = (
            f"Analyse this match situation and write a comprehensive tactical briefing:\n\n"
            f"{data_summary}\n\n"
            f"Write a 3-5 paragraph professional tactical analysis. "
            f"Be specific and reference actual players, formations, and metrics from the data."
        )
        
        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1200,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return message.content[0].text
        except Exception as e:
            print(f"[LLM mode] API error: {e} — falling back to template mode.")
            return self._generate_template()
    
    def _build_data_summary(self):
        """Build a text summary of all analysis data for the LLM prompt."""
        mi = self.match_info
        rd = self.report_data
        swot = self.swot_results
        recs = self.recommendations
        
        lines = []
        
        # Match info
        lines.append(f"Match: {mi.get('home_team', '?')} {mi.get('score_home', 0)} - "
                     f"{mi.get('score_away', 0)} {mi.get('away_team', '?')}")
        lines.append(f"Competition: {mi.get('competition', '?')} | Minute: {mi.get('minute', '?')}'")
        
        # Formations
        lines.append(f"\nFormations:")
        lines.append(f"  {rd.get('team_a', {}).get('name', '?')}: {rd.get('team_a', {}).get('formation', '?')}")
        lines.append(f"  {rd.get('team_b', {}).get('name', '?')}: {rd.get('team_b', {}).get('formation', '?')}")
        
        # Pass analysis
        pa = rd.get('pass_analysis', {})
        if pa:
            lines.append(f"\nPass Analysis:")
            lines.append(f"  Total passes: {pa.get('total_passes', 0)}")
            kd = pa.get('key_distributor', {})
            lines.append(f"  Key distributor: {kd.get('name', '?')} (betweenness: {kd.get('betweenness', 0):.2f})")
        
        # Space control
        sa = rd.get('space_analysis', {})
        if sa:
            overall = sa.get('overall', {})
            lines.append(f"\nSpace Control: {rd.get('team_a', {}).get('name', '?')} {overall.get('team_a_control', 50)}% | "
                        f"{rd.get('team_b', {}).get('name', '?')} {overall.get('team_b_control', 50)}%")
        
        # Press resistance
        pr = rd.get('press_resistance', {})
        if pr:
            lines.append(f"\nPress Resistance: {pr.get('press_resistance_score', 50):.0f}/100")
            lines.append(f"  Success under pressure: {pr.get('pass_success_under_pressure', 0):.0%}")
            lines.append(f"  Escape rate: {pr.get('escape_rate', 0):.0%}")
        
        # SWOT
        lines.append(f"\nSWOT Analysis:")
        for cat in ['strengths', 'weaknesses', 'opportunities', 'threats']:
            items = swot.get(cat, [])
            if items:
                lines.append(f"  {cat.upper()}:")
                for item in items[:3]:
                    lines.append(f"    - {item['description']}")
        
        # Recommendations
        if recs:
            lines.append(f"\nTop Recommendations:")
            for r in recs[:5]:
                lines.append(f"  [{r['priority'].upper()}] {r['category']}: {r['description']}")
        
        return "\n".join(lines)
    
    # ── Text output ─────────────────────────────────────────────
    
    def print_explanation(self, text=None):
        """Print the tactical explanation."""
        if text is None:
            text = self.generate()
        
        print("\n" + "=" * 60)
        print("  TACTICAL ANALYSIS — EXPLANATION")
        print("=" * 60)
        print(f"  Mode: {self.mode.upper()}")
        print()
        
        # Word-wrap for clean output
        for paragraph in text.split("\n\n"):
            wrapped = textwrap.fill(paragraph.strip(), width=76, initial_indent="  ",
                                     subsequent_indent="  ")
            print(wrapped)
            print()
        
        print("=" * 60)
    
    # ── Save ────────────────────────────────────────────────────
    
    def save_text(self, text=None, filename="tactical_explanation.txt"):
        """Save explanation to text file."""
        if text is None:
            text = self.generate()
        
        filepath = f"outputs/{filename}"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("SPACEAI FC - TACTICAL ANALYSIS\n")
            f.write("=" * 40 + "\n\n")
            f.write(text)
            f.write("\n\n" + "=" * 40 + "\n")
            f.write("Generated by SpaceAI FC v3 - Tactical Intelligence Engine\n")
        
        print(f"Saved: {filepath}")


# ═══════════════════════════════════════════════════════════════
# Quick test — Explanation from El Clásico analysis
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    
    import os, sys, random
    sys.path.insert(0, '.')
    os.makedirs("outputs", exist_ok=True)
    
    import matplotlib
    matplotlib.use('Agg')
    
    import numpy as np
    from engine.analysis.formation_detection import FormationDetector
    from engine.analysis.role_classifier import RoleClassifier
    from engine.analysis.press_resistance import PressResistance
    from engine.analysis.pattern_detection import PatternDetector
    from engine.analysis.pass_network import PassNetwork
    from engine.analysis.space_control import SpaceControl
    from engine.analysis.match_report import MatchReport
    from engine.intelligence.knowledge_graph import TacticalKnowledgeGraph
    from engine.intelligence.tactical_reasoning import TacticalReasoner
    from engine.intelligence.strategy_recommender import StrategyRecommender
    
    barca = [
        {'name': 'ter Stegen',  'number': 1,  'x': 5,  'y': 40, 'position': 'GK'},
        {'name': 'Koundé',      'number': 23, 'x': 30, 'y': 70, 'position': 'RB'},
        {'name': 'Araújo',      'number': 4,  'x': 25, 'y': 52, 'position': 'CB'},
        {'name': 'Cubarsí',     'number': 2,  'x': 25, 'y': 28, 'position': 'CB'},
        {'name': 'Baldé',       'number': 3,  'x': 30, 'y': 10, 'position': 'LB'},
        {'name': 'Pedri',       'number': 8,  'x': 45, 'y': 48, 'position': 'CM'},
        {'name': 'De Jong',     'number': 21, 'x': 45, 'y': 32, 'position': 'CM'},
        {'name': 'Lamine',      'number': 19, 'x': 65, 'y': 68, 'position': 'RW'},
        {'name': 'Gavi',        'number': 6,  'x': 60, 'y': 40, 'position': 'CAM'},
        {'name': 'Raphinha',    'number': 11, 'x': 65, 'y': 12, 'position': 'LW'},
        {'name': 'Lewandowski', 'number': 9,  'x': 80, 'y': 40, 'position': 'ST'},
    ]
    
    madrid = [
        {'name': 'Courtois',    'number': 1,  'x': 115, 'y': 40, 'position': 'GK'},
        {'name': 'Carvajal',    'number': 2,  'x': 90,  'y': 70, 'position': 'RB'},
        {'name': 'Rüdiger',     'number': 22, 'x': 93,  'y': 52, 'position': 'CB'},
        {'name': 'Militão',     'number': 3,  'x': 93,  'y': 28, 'position': 'CB'},
        {'name': 'Mendy',       'number': 23, 'x': 90,  'y': 10, 'position': 'LB'},
        {'name': 'Tchouaméni',  'number': 14, 'x': 73,  'y': 40, 'position': 'CDM'},
        {'name': 'Valverde',    'number': 15, 'x': 70,  'y': 58, 'position': 'CM'},
        {'name': 'Bellingham',  'number': 5,  'x': 70,  'y': 22, 'position': 'CM'},
        {'name': 'Rodrygo',     'number': 11, 'x': 55,  'y': 65, 'position': 'RW'},
        {'name': 'Mbappé',      'number': 7,  'x': 50,  'y': 40, 'position': 'ST'},
        {'name': 'Vinícius',    'number': 20, 'x': 55,  'y': 15, 'position': 'LW'},
    ]
    
    passes = [
        (1, 4), (1, 2), (1, 4), (4, 8), (4, 21), (4, 8), (4, 23), (4, 2),
        (2, 21), (2, 3), (2, 8), (2, 21), (2, 4), (23, 19), (23, 8), (23, 19), (23, 4),
        (3, 11), (3, 21), (3, 11), (3, 2), (8, 6), (8, 19), (8, 23), (8, 21), (8, 9),
        (8, 6), (8, 19), (8, 4), (8, 9), (8, 11), (8, 6), (8, 21), (8, 23),
        (21, 8), (21, 2), (21, 3), (21, 6), (21, 11), (21, 8), (21, 4), (21, 6),
        (6, 9), (6, 19), (6, 8), (6, 11), (6, 9), (6, 8), (6, 19), (6, 21),
        (19, 9), (19, 23), (19, 6), (19, 8), (19, 9), (19, 6),
        (11, 9), (11, 3), (11, 6), (11, 21), (11, 9), (11, 6),
        (9, 6), (9, 19), (9, 8), (9, 11), (6, 8), (19, 8), (9, 6), (11, 21),
    ]
    
    # Run Phase 1+2
    fd_b = FormationDetector(); fd_b.set_team(barca, "FC Barcelona", "#a50044")
    fd_m = FormationDetector(); fd_m.set_team(madrid, "Real Madrid", "#ffffff")
    pn = PassNetwork(); pn.add_players(barca); pn.add_passes(passes)
    sc = SpaceControl(); sc.set_teams(barca, madrid); sc.set_ball(60, 40)
    grid, stats = sc.compute_influence_control(); mid = sc.get_midfield_control(grid)
    rc_b = RoleClassifier(); rc_b.set_team(barca, "FC Barcelona", "#a50044")
    rc_m = RoleClassifier(); rc_m.set_team(madrid, "Real Madrid", "#ffffff")
    random.seed(42)
    events = []
    for _ in range(65):
        p = random.choice([x for x in barca if x['position']!='GK'])
        r = random.choice([x for x in barca if x['position']!='GK'])
        px = max(0,min(120,p['x']+random.gauss(0,3))); py = max(0,min(80,p['y']+random.gauss(0,3)))
        opp = np.array([[x['x'],x['y']] for x in madrid])
        d = np.linalg.norm(opp-np.array([px,py]),axis=1); n = np.sum(d<10)
        events.append({'passer':p['number'],'receiver':r['number'],'success':random.random()<(0.55 if n>=2 else 0.90),'x':px,'y':py,'end_x':r['x'],'end_y':r['y']})
    pr = PressResistance(); pr.set_teams(barca,madrid,"FC Barcelona","#a50044","Real Madrid"); pr.add_pass_events(events)
    ptd = PatternDetector(); ptd.set_teams(barca,madrid,"FC Barcelona","Real Madrid","#a50044","#ffffff")
    
    # Match report for report_data
    mr = MatchReport()
    mr.set_match_info("FC Barcelona", "Real Madrid", 2, 1, 72, "La Liga", "2026-03-22")
    mr.set_team_a("FC Barcelona", "#a50044", barca)
    mr.set_team_b("Real Madrid", "#ffffff", madrid)
    mr.set_ball(60, 40)
    mr.set_pass_network(pn)
    mr.set_space_control(sc)
    mr.set_formation_detector(fd_b, fd_m)
    mr.set_role_classifier(rc_b, rc_m)
    mr.set_press_resistance(pr)
    mr.set_pattern_detector(ptd)
    report_data = mr.generate_report()
    
    # Phase 3
    analysis_data = {
        'formation_a': fd_b.detect(), 'formation_b': fd_m.detect(),
        'space_control': {'team_a_control':stats['team_a_control'],'team_b_control':stats['team_b_control'],'zones':stats['zones'],'midfield':mid},
        'pass_summary': pn.get_summary(), 'press_resistance': pr.analyze(),
        'patterns_a': ptd.detect_all("a"), 'patterns_b': ptd.detect_all("b"),
        'roles_a': rc_b.classify_all(), 'roles_b': rc_m.classify_all(),
    }
    
    kg = TacticalKnowledgeGraph()
    reasoner = TacticalReasoner(knowledge_graph=kg)
    reasoner.set_analysis(analysis_data, "FC Barcelona", "Real Madrid")
    swot = reasoner.reason()
    
    sr = StrategyRecommender(knowledge_graph=kg)
    sr.set_reasoning(swot, analysis_data, "FC Barcelona", "Real Madrid")
    recs = sr.recommend()
    
    # Explanation (template mode)
    el = ExplanationLayer(mode="template")
    el.set_data(
        match_info={'home_team': 'FC Barcelona', 'away_team': 'Real Madrid',
                    'score_home': 2, 'score_away': 1, 'minute': 72,
                    'competition': 'La Liga'},
        report_data=report_data,
        swot_results=swot,
        recommendations=recs,
        team_name="FC Barcelona",
        opponent_name="Real Madrid",
    )
    
    text = el.generate()
    el.print_explanation(text)
    el.save_text(text, "tactical_explanation.txt")
    
    print("\nExplanation layer complete!")
