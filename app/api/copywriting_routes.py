"""
文案 Agent API — 生成中文商业文案。
支持：电商卖点/小红书标题/抖音口播/海报主标题/活动促销/品牌slogan
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.compliance import ComplianceChecker

router = APIRouter(prefix="/api/v1/copywriting", tags=["copywriting"])

COPY_TYPE_PROMPTS = {
    "ecommerce_selling_point": "电商卖点文案（标题+正文+行动号召，突出卖点和转化）",
    "xiaohongshu_title": "小红书种草标题（有吸引力不标题党，像爆款笔记口吻，15字以内）",
    "douyin_voiceover": "抖音口播文案（口语化有网感，前3秒钩子，每句短促有力，带行动号召）",
    "poster_headline": "海报主标题（简洁有力，8-12字，视觉冲击力强）",
    "promo_copy": "活动促销文案（紧迫感，利益点前置，适合活动海报和社群转发）",
    "brand_slogan": "品牌slogan（一句话品牌主张，易记有传播力，8字以内）",
}

COPY_SYSTEM_PROMPT = """你是资深中文商业文案，擅长电商、社媒、品牌文案。

根据产品信息和文案类型，生成高质量中文文案。

规则：
1. 避免使用广告法极限词（最好、第一、顶级、全网最等）
2. 文案要结合产品具体卖点，不能写泛泛模板
3. 根据文案类型调整风格和长度
4. 严格输出JSON，不要任何额外文字"""

ALL_TYPES = list(COPY_TYPE_PROMPTS.keys())


class CopywritingRequest(BaseModel):
    brief: dict
    copy_types: list[str]  # ["all"] 或 ["ecommerce_selling_point", ...]


@router.post("/generate")
async def generate_copy(req: CopywritingRequest):
    """生成指定类型的商业文案。"""
    types = ALL_TYPES if "all" in req.copy_types else req.copy_types
    types = [t for t in types if t in COPY_TYPE_PROMPTS]
    if not types:
        raise HTTPException(status_code=400, detail="无效的文案类型")

    from app.api.unified_generation_routes import agent

    product_name = req.brief.get("product_name", "产品")
    category = req.brief.get("category", "")
    selling_points = ", ".join(req.brief.get("selling_points", []))
    target = ", ".join(req.brief.get("target_customer", []))
    style = req.brief.get("brand_style", "")

    product_info = (
        f"产品：{product_name} | 品类：{category} | "
        f"卖点：{selling_points} | 目标用户：{target} | 风格：{style}"
    )

    result = {}
    for copy_type in types:
        try:
            type_desc = COPY_TYPE_PROMPTS[copy_type]
            user_prompt = (
                f"## 产品信息\n{product_info}\n\n"
                f"## 文案类型\n{type_desc}\n\n"
                f"请输出JSON：{{\"headline\":\"标题\",\"body\":\"正文\",\"cta\":\"行动号召\"}}"
            )
            raw = await agent._llm.call(
                system_prompt=COPY_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.8,
            )

            # 合规检查
            full_text = f"{raw.get('headline','')} {raw.get('body','')} {raw.get('cta','')}"
            compliance = ComplianceChecker.check_text(full_text)

            result[copy_type] = {
                "headline": raw.get("headline", ""),
                "body": raw.get("body", ""),
                "cta": raw.get("cta", ""),
                "compliance": compliance,
            }
        except Exception as e:
            result[copy_type] = {
                "headline": "",
                "body": "",
                "cta": "",
                "compliance": [],
                "error": str(e),
            }

    return result
