"""
Quality Evaluator — lightweight quality assessment using LLM.

Evaluates generated visual assets across three dimensions:
- Composition (构图): layout, balance, visual hierarchy
- Color Harmony (色彩协调): palette, contrast, brand alignment
- Commercial Appeal (商业适用性): market fit, persuasiveness, professionalism

Design: separate agent from main generation — uses minimal tokens
and lower temperature for consistent, objective scoring.
"""
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

EVALUATION_SYSTEM_PROMPT = """你是视觉素材质量评估专家。对生成的视觉素材方案进行三维评分。

评分标准（每项 1-10 分）：
1. 构图 (composition): 布局是否合理、视觉层次是否清晰、主体是否突出
2. 色彩协调 (color_harmony): 配色是否和谐、对比度是否恰当、是否符品牌调性
3. 商业适用性 (commercial_appeal): 是否适合目标市场、是否有说服力、专业度

对每项给出：
- score: 1-10 的整数分数
- reasoning: 1-2 句中文评价
- suggestion: 1 条优化建议（如有）

只输出 JSON，格式：{"dimensions": [...], "overall_score": N, "summary": "..."}"""


@dataclass
class QualityDimension:
    name: str
    name_cn: str
    score: int
    reasoning: str
    suggestion: str = ""


@dataclass
class QualityReport:
    dimensions: list = field(default_factory=list)
    overall_score: int = 0
    summary: str = ""
    model_used: str = ""


async def evaluate_assets(
    brief: dict,
    generation_result: dict,
    llm_client=None,
) -> QualityReport:
    """Evaluate generation quality across three dimensions.

    Args:
        brief: The original product brief
        generation_result: The generated VisualAssetPlanOut (as dict)
        llm_client: Optional LLMClient instance

    Returns:
        QualityReport with scores and suggestions
    """
    # Build evaluation context
    product_name = brief.get("product_name", "未知产品")
    category = brief.get("category", "")
    target_market = brief.get("target_market", [])
    brand_style = brief.get("brand_style", "")

    # Extract key generation outputs for evaluation
    main_image = generation_result.get("main_image", {})
    scene_images = generation_result.get("scene_images", [])
    selling_points = generation_result.get("selling_points", [])

    # Build the evaluation prompt
    eval_context = f"""产品信息：
- 产品名: {product_name}
- 品类: {category}
- 目标市场: {', '.join(target_market) if isinstance(target_market, list) else target_market}
- 品牌风格: {brand_style}

生成的素材方案摘要：
- 主图方案: {json.dumps(main_image, ensure_ascii=False)[:500] if main_image else '无'}
- 场景图数量: {len(scene_images) if isinstance(scene_images, list) else 0}
- 卖点模块数: {len(selling_points) if isinstance(selling_points, list) else 0}

请对该方案进行三维评分："""

    try:
        # 优先走 DataEyes(唯一可用文字通道);测试可注入 llm_client 覆盖
        if llm_client is not None:
            raw = await llm_client.call(
                system_prompt=EVALUATION_SYSTEM_PROMPT,
                user_prompt=eval_context,
                temperature=0.3,
                max_tokens=1024,
            )
        else:
            from app.services.dataeyes_text import dataeyes_json
            raw = await dataeyes_json(
                EVALUATION_SYSTEM_PROMPT, eval_context,
                temperature=0.3, max_tokens=1024,
            )
        if not isinstance(raw, dict) or not raw.get("dimensions"):
            raise ValueError("评估返回为空")

        # Parse dimensions
        dims = []
        for d in raw.get("dimensions", []):
            dims.append(QualityDimension(
                name=d.get("name", "unknown"),
                name_cn=d.get("name_cn", d.get("name", "")),
                score=int(d.get("score", 5)),
                reasoning=d.get("reasoning", ""),
                suggestion=d.get("suggestion", ""),
            ))

        return QualityReport(
            dimensions=dims,
            overall_score=int(raw.get("overall_score", sum(d.score for d in dims) // len(dims) if dims else 5)),
            summary=raw.get("summary", "评估完成"),
            model_used=(getattr(getattr(llm_client, '_provider', None), '_model', 'unknown')
                        if llm_client is not None else "dataeyes:gpt-4o"),
        )

    except Exception as e:
        logger.error(f"Quality evaluation failed: {e}")
        # Return fallback report
        return QualityReport(
            dimensions=[
                QualityDimension(name="composition", name_cn="构图", score=6, reasoning="评估暂时不可用"),
                QualityDimension(name="color_harmony", name_cn="色彩协调", score=6, reasoning="评估暂时不可用"),
                QualityDimension(name="commercial_appeal", name_cn="商业适用性", score=6, reasoning="评估暂时不可用"),
            ],
            overall_score=6,
            summary=f"评估服务暂时不可用 ({str(e)[:50]})",
        )


def report_to_dict(report: QualityReport) -> dict:
    """Convert QualityReport to JSON-serializable dict."""
    return {
        "dimensions": [
            {
                "name": d.name,
                "name_cn": d.name_cn,
                "score": d.score,
                "reasoning": d.reasoning,
                "suggestion": d.suggestion,
            }
            for d in report.dimensions
        ],
        "overall_score": report.overall_score,
        "summary": report.summary,
        "model_used": report.model_used,
    }
