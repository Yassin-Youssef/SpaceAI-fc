"""
SpaceAI FC - Export Router
  POST /api/export/docx
  POST /api/export/pdf

Rebuilds a MatchReport from the supplied player positions (so the document
contains pass, space, formation, role, press and pattern sections) and
attaches any SWOT / recommendations / explanation text found in the
analysis payload the client already holds.
"""

import io
import os
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.config import OUTPUTS_DIR
from api.models.requests import ExportRequest

router = APIRouter(prefix="/api/export", tags=["Export"])


def _safe_name(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in value.strip()) or "team"


def _dump(items) -> list:
    return [i.model_dump() if hasattr(i, "model_dump") else dict(i) for i in (items or [])]


def _build_report(req: ExportRequest):
    """Create and populate a MatchReport from the request."""
    from engine.analysis.match_report import MatchReport

    report = MatchReport()
    team_a = _dump(req.team_a)
    team_b = _dump(req.team_b)
    passes = _dump(req.passes)

    report.set_team_a(req.team_name, req.team_a_color, team_a)
    report.set_team_b(req.opponent_name, req.team_b_color, team_b)
    report.set_ball(req.ball_x, req.ball_y)

    mi = req.match_info or {}
    report.set_match_info(
        home_team=mi.get("home_team") or req.team_name,
        away_team=mi.get("away_team") or req.opponent_name,
        score_home=int(mi.get("score_home") or 0),
        score_away=int(mi.get("score_away") or 0),
        minute=int(mi.get("minute") or 0),
        competition=mi.get("competition") or "SpaceAI FC analysis",
        date=mi.get("date") or None,
    )

    # ── Rebuild engine objects when positions are available ─────
    if team_a:
        from engine.analysis.formation_detection import FormationDetector
        from engine.analysis.role_classifier import RoleClassifier

        fd_a = FormationDetector(); fd_a.set_team(team_a, req.team_name, req.team_a_color)
        rc_a = RoleClassifier(); rc_a.set_team(team_a, req.team_name, req.team_a_color)
        fd_b = rc_b = None
        if team_b:
            fd_b = FormationDetector(); fd_b.set_team(team_b, req.opponent_name, req.team_b_color)
            rc_b = RoleClassifier(); rc_b.set_team(team_b, req.opponent_name, req.team_b_color)
        report.set_formation_detector(fd_a, fd_b)
        report.set_role_classifier(rc_a, rc_b)

        if passes:
            from engine.analysis.pass_network import PassNetwork
            pn = PassNetwork()
            pn.add_players(team_a)
            pn.add_passes([(p["passer"], p["receiver"], p.get("success", True)) for p in passes])
            if pn.get_total_passes() > 0:
                report.set_pass_network(pn)

    if team_a and team_b:
        from engine.analysis.space_control import SpaceControl
        from engine.analysis.pattern_detection import PatternDetector

        sc = SpaceControl(); sc.set_teams(team_a, team_b); sc.set_ball(req.ball_x, req.ball_y)
        report.set_space_control(sc)

        pd_inst = PatternDetector()
        pd_inst.set_teams(team_a, team_b, team_a_name=req.team_name, team_b_name=req.opponent_name,
                          team_a_color=req.team_a_color, team_b_color=req.team_b_color)
        report.set_pattern_detector(pd_inst)

        if passes:
            from engine.analysis.press_resistance import PressResistance
            pr = PressResistance()
            pr.set_teams(team_a, team_b, team_name=req.team_name,
                         team_color=req.team_a_color, opponent_name=req.opponent_name)
            pr.add_pass_events(passes)
            report.set_press_resistance(pr)

    # ── Phase 3 content from the client's analysis payload ──────
    ad = req.analysis_data or {}
    intel = ad.get("intelligence") if isinstance(ad.get("intelligence"), dict) else ad

    swot_list = intel.get("swot") if isinstance(intel, dict) else None
    if isinstance(swot_list, list) and swot_list:
        swot = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
        for item in swot_list:
            if not isinstance(item, dict):
                continue
            cat = str(item.get("category", "")).lower()
            cat = cat if cat.endswith("s") else cat + "s"
            if cat in swot:
                swot[cat].append({
                    "description": item.get("description", ""),
                    "confidence": float(item.get("confidence", 0.7)),
                    "action": item.get("source", ""),
                })
        if any(swot.values()):
            report.set_reasoning_results(swot)
    elif isinstance(swot_list, dict):
        report.set_reasoning_results(swot_list)

    recs = intel.get("recommendations") if isinstance(intel, dict) else None
    if isinstance(recs, list) and recs and isinstance(recs[0], dict) and "priority" in recs[0]:
        report.set_recommendations([
            {
                "priority": r.get("priority", "medium"),
                "category": r.get("category", ""),
                "description": r.get("description", ""),
                "reasoning": r.get("reasoning", ""),
                "expected_impact": r.get("expected_impact", ""),
            }
            for r in recs
        ])

    explanation = ad.get("explanation")
    if isinstance(explanation, dict):
        explanation = explanation.get("text")
    if not explanation and isinstance(ad.get("text"), str):
        explanation = ad["text"]
    if isinstance(explanation, str) and explanation.strip():
        report.set_explanation(explanation)

    return report


def _collect_images(analysis_data: dict) -> tuple:
    """
    Decode every base64 visualisation in the analysis payload to a temp PNG.
    Returns ([(path, caption), ...], [temp paths]).
    """
    import base64
    import tempfile

    found = []
    seen = set()

    def walk(node, depth=0):
        if depth > 3:
            return
        if isinstance(node, dict):
            vis = node.get("visualizations")
            if isinstance(vis, list):
                for v in vis:
                    if isinstance(v, dict) and v.get("image_base64"):
                        key = v["image_base64"][:64]
                        if key not in seen:
                            seen.add(key)
                            found.append((v.get("title") or "Visualization", v["image_base64"]))
            for k, child in node.items():
                if k != "visualizations":
                    walk(child, depth + 1)

    walk(analysis_data)

    image_files, temp_paths = [], []
    for caption, b64 in found[:16]:
        try:
            raw = base64.b64decode(b64.split(",")[-1])
            fd, path = tempfile.mkstemp(suffix=".png")
            with os.fdopen(fd, "wb") as fh:
                fh.write(raw)
            image_files.append((path, caption))
            temp_paths.append(path)
        except Exception:
            continue
    return image_files, temp_paths


@router.post("/docx")
async def export_docx(req: ExportRequest):
    """Export analysis results as a Word document."""
    tmp_name: Optional[str] = None
    try:
        report = _build_report(req)

        # Embed the visualisations the client received for this analysis
        image_files, temp_images = _collect_images(req.analysis_data or {})

        # MatchReport always writes into outputs/<filename>
        tmp_name = f"export_{uuid.uuid4().hex}.docx"
        try:
            report.export_document(tmp_name, image_files=image_files)
        finally:
            for path in temp_images:
                try:
                    os.unlink(path)
                except OSError:
                    pass
        tmp_path = OUTPUTS_DIR / tmp_name
        docx_bytes = tmp_path.read_bytes()

        filename = f"spaceaifc_{_safe_name(req.team_name)}_vs_{_safe_name(req.opponent_name)}.docx"
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="python-docx is required for Word export.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")
    finally:
        if tmp_name:
            try:
                (OUTPUTS_DIR / tmp_name).unlink(missing_ok=True)
            except OSError:
                pass


@router.post("/pdf")
async def export_pdf(req: ExportRequest):
    """Export a summary report as PDF using matplotlib's PDF backend."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        import textwrap

        report = _build_report(req)
        data = report.generate_report()

        buf = io.BytesIO()
        with PdfPages(buf) as pdf:
            fig, ax = plt.subplots(figsize=(8.5, 11))
            fig.patch.set_facecolor("#0a0e27")
            ax.set_facecolor("#0a0e27")
            ax.axis("off")

            ax.text(0.5, 0.93, "SpaceAI FC — Tactical Report", transform=ax.transAxes,
                    fontsize=20, fontweight="bold", color="#00d9ff", ha="center")
            ax.text(0.5, 0.89, f"{req.team_name} vs {req.opponent_name}", transform=ax.transAxes,
                    fontsize=14, color="white", ha="center")

            lines = [
                f"{data['team_a']['name']} formation: {data['team_a']['formation']}",
                f"{data['team_b']['name']} formation: {data['team_b']['formation']}",
            ]
            for insight in data.get("insights", [])[:10]:
                lines += textwrap.wrap("• " + insight, 90)
            lines.append("")
            lines.append("Recommendations:")
            for rec in data.get("recommendations", [])[:8]:
                lines += textwrap.wrap("• " + rec, 90)

            ax.text(0.06, 0.82, "\n".join(lines), transform=ax.transAxes,
                    fontsize=9.5, color="#d0d6f0", va="top", family="monospace")

            pdf.savefig(fig, facecolor=fig.get_facecolor())
            plt.close(fig)

        buf.seek(0)
        filename = f"spaceaifc_{_safe_name(req.team_name)}_vs_{_safe_name(req.opponent_name)}.pdf"
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")
