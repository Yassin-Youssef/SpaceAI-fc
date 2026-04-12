"""
SpaceAI FC - Ask SpaceAI Router
  POST /api/ask
"""

from fastapi import APIRouter, HTTPException
from api.models.requests import AskRequest
from api.models.responses import AskResponse
from api.services.llm_service import ask_llm

router = APIRouter(tags=["Ask SpaceAI"])


@router.post("/api/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """
    Natural language Q&A.  Uses LLM if an API key is set; falls back
    to the knowledge graph for rule-based answers.
    """
    try:
        answer, mode = await ask_llm(req.question, context=req.match_context)
        return AskResponse(
            success=True,
            question=req.question,
            answer=answer,
            mode=mode,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
