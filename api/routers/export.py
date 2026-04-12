"""
SpaceAI FC - Export Router
  POST /api/export/docx
  POST /api/export/pdf
"""

import io
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.models.requests import ExportRequest

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.post("/docx")
async def export_docx(req: ExportRequest):
    """Export analysis results as a Word document."""
    import tempfile, os
    tmp_path = None
    try:
        from engine.analysis.match_report import MatchReport

        report = MatchReport()
        report.set_team_a(req.team_name, "#a50044", [])
        report.set_team_b(req.opponent_name, "#ffffff", [])

        if req.match_info:
            report.set_match_info(
                home_team=req.match_info.get("home_team", req.team_name),
                away_team=req.match_info.get("away_team", req.opponent_name),
                score_home=req.match_info.get("score_home", 0),
                score_away=req.match_info.get("score_away", 0),
                minute=req.match_info.get("minute", 0),
                competition=req.match_info.get("competition", ""),
                date=req.match_info.get("date", ""),
            )

        # Write to a temp file, then stream it back
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".docx")
        os.close(tmp_fd)
        report.export_document(tmp_path)

        with open(tmp_path, "rb") as f:
            docx_bytes = f.read()

        filename = f"spaceaifc_{req.team_name}_vs_{req.opponent_name}.docx".replace(" ", "_")
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="python-docx is required for Word export.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/pdf")
async def export_pdf(req: ExportRequest):
    """
    Export analysis results as PDF.
    Requires matplotlib's PDF backend (no extra deps).
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages

        buf = io.BytesIO()
        with PdfPages(buf) as pdf:
            # Cover page
            fig, ax = plt.subplots(figsize=(8.5, 11))
            fig.patch.set_facecolor("#1a1a2e")
            ax.set_facecolor("#1a1a2e")
            ax.axis("off")

            title = f"SpaceAI FC — Tactical Report\n{req.team_name} vs {req.opponent_name}"
            ax.text(0.5, 0.65, title, transform=ax.transAxes,
                    fontsize=18, fontweight="bold", color="white",
                    ha="center", va="center", wrap=True)

            # Add summary text if available
            summary_lines = []
            for key in ("formation", "space_control", "pass_network"):
                val = req.analysis_data.get(key)
                if val and isinstance(val, dict):
                    summary_lines.append(f"{key.replace('_', ' ').title()}: available")

            if summary_lines:
                ax.text(0.5, 0.45, "\n".join(summary_lines),
                        transform=ax.transAxes, fontsize=12, color="#aaaaaa",
                        ha="center", va="center")

            pdf.savefig(fig, facecolor=fig.get_facecolor())
            plt.close(fig)

        buf.seek(0)
        filename = f"spaceaifc_{req.team_name}_vs_{req.opponent_name}.pdf".replace(" ", "_")
        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
