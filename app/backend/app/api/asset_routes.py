"""
资产修改 API — 画布中点选素材后用自然语言修改。
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/asset", tags=["asset-modify"])

MODIFY_SYSTEM_PROMPT = """你是素材修改助手。你收到一个已生成的素材和一个修改指令，请根据指令修改素材内容。

规则：
1. 保持输出 JSON 结构完全不变，只修改内容
2. 只修改与指令相关的字段，其他字段保持不变
3. 修改后的内容应与产品信息一致
4. 严格输出 JSON，不要任何额外文字"""


class ModifyRequest(BaseModel):
    asset_type: str
    original: dict
    instruction: str
    brief: dict


@router.post("/modify")
async def modify_asset(req: ModifyRequest):
    """根据自然语言指令修改素材内容。"""
    if not req.instruction.strip():
        return {"modified": req.original}

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
        return {"modified": modified}
    except Exception as e:
        # 如果 LLM 调用失败，返回原始素材
        return {"modified": req.original, "error": str(e)}
