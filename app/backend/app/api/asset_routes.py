"""Asset modify API — supports text and crop operations (with brand learning)."""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.brand_memory_learner import BrandMemoryLearner

router = APIRouter(prefix="/api/v1/asset", tags=["asset-modify"])

brand_learner = BrandMemoryLearner()

MODIFY_SYSTEM_PROMPT = """你是素材修改助手。你收到一个已生成的素材和一个修改指令，请根据指令修改素材内容。

规则：
1. 保持输出 JSON 结构完全不变，只修改内容
2. 只修改与指令相关的字段，其他字段保持不变
3. 修改后的内容应与产品信息一致
4. 严格输出 JSON，不要任何额外文字"""


class CropRegion(BaseModel):
    x: int
    y: int
    width: int
    height: int


class ModifyRequest(BaseModel):
    asset_type: str
    original: dict
    instruction: str
    brief: dict
    operation: str = "text"
    crop_region: Optional[CropRegion] = None


@router.post("/modify")
async def modify_asset(req: ModifyRequest):
    """根据自然语言指令或 crop 操作修改素材内容。"""
    if not req.instruction.strip():
        return {"modified": req.original}

    # Crop operation: just annotate the crop intent
    if req.operation == "crop" and req.crop_region:
        modified = dict(req.original)
        modified["_crop"] = req.crop_region.model_dump()
        modified["_crop_instruction"] = req.instruction
        return {"modified": modified}

    # Text operation: use LLM
    from app.api.unified_generation_routes import agent

    try:
        user_prompt = (
            f"## 产品信息\n{req.brief}\n\n"
            f"## 当前素材\n```json\n{req.original}\n```\n\n"
            f"## 修改指令\n{req.instruction}\n\n"
            f"请输出修改后的 JSON（保持结构不变）："
        )
        modified = await agent._llm.call(
            system_prompt=MODIFY_SYSTEM_PROMPT,
            user_prompt=str(user_prompt),
            temperature=0.7,
        )

        # Auto-learn from text edits (fire-and-forget)
        try:
            await brand_learner.learn_from_edit(
                project_id=req.brief.get("project_id", 0),
                edit_type="text",
                before=str(req.instruction),
                after=str(modified),
            )
        except Exception:
            pass  # learning failure must not block the response

        return {"modified": modified}
    except Exception as e:
        return {"modified": req.original, "error": str(e)}
