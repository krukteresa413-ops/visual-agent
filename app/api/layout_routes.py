"""
Layout Agent API — 独立排版生成端点。
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/layout", tags=["layout"])


class LayoutRequest(BaseModel):
    project_id: int
    brief: dict
    asset_plan: dict           # VisualAssetPlanOut.model_dump()
    platform_id: Optional[str] = None
    brand_context: Optional[str] = None


@router.post("/generate")
async def generate_layout(req: LayoutRequest):
    """生成完整的排版布局方案（覆盖主图/详情页/卖点/场景图）。"""
    from app.services.layout_agent import LayoutAgent

    agent = LayoutAgent()
    try:
        layout = await agent.generate_layout(
            project_id=req.project_id,
            brief=req.brief,
            asset_plan=req.asset_plan,
            platform_id=req.platform_id,
            brand_context=req.brand_context,
        )
        return layout.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"排版生成失败: {str(e)}")
