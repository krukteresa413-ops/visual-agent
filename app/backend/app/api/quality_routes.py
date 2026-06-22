"""
Quality evaluation API route.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/quality", tags=["quality"])


class EvaluateRequest(BaseModel):
    brief: dict
    generation_result: dict


@router.post("/evaluate")
async def evaluate_generation(req: EvaluateRequest):
    """Evaluate generation quality across composition, color, commercial dimensions."""
    from app.services.quality_evaluator import evaluate_assets, report_to_dict

    try:
        report = await evaluate_assets(
            brief=req.brief,
            generation_result=req.generation_result,
        )
        return report_to_dict(report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")
