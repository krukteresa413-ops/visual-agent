"""
Creative Strategy Agent — orchestrates brand + research + visual direction
into a unified creative strategy. Template-based, no LLM required.
"""
from typing import Dict, Optional
from app.services.industry_templates import INDUSTRY_TEMPLATES
from app.services.research_templates import TEMPLATES as RESEARCH_TEMPLATES
from app.services.brand_strategy import BrandStrategyAgent
from app.services.visual_direction import VisualDirection


# Platform-specific content themes
PLATFORM_THEMES = {
    "xiaohongshu": ["种草测评", "使用教程", "前后对比", "成分解析", "场景化展示"],
    "douyin": ["短视频种草", "挑战赛", "开箱测评", "达人推荐", "剧情植入"],
    "taobao": ["主图优化", "详情页", "白底图", "场景图", "视频主图"],
    "wechat": ["朋友圈广告", "公众号种草", "社群分享", "小程序展示"],
    "amazon": ["A+ Content", "Lifestyle", "Infographic", "Comparison Chart"],
}


# Creative angle templates by category
CREATIVE_ANGLES = {
    "美妆": "成分党信赖 + 真实效果 + 国风美学",
    "食品": "健康溯源 + 食欲感 + 场景共情",
    "女装": "风格穿搭 + 身材友好 + 季节氛围",
    "3C数码": "科技美学 + 场景赋能 + 参数可视化",
    "家居": "空间美学 + 材质质感 + 生活方式",
}


class CreativeStrategyAgent:
    """Creative strategy orchestrator. Combines industry research, brand
    strategy, and visual direction into a unified creative brief."""

    def generate_strategy(
        self,
        brief: dict,
        platform: str,
    ) -> Dict:
        """Generate creative strategy from brief and platform."""
        category = brief.get("category", "")
        product_name = brief.get("product_name", "产品")

        # 1. Industry insight from research templates
        industry_insight = self._get_industry_insight(category, platform)

        # 2. Brand guidelines from BrandStrategyAgent
        brand_agent = BrandStrategyAgent()
        industry_key = self._resolve_industry_key(category)
        brand_guidelines = brand_agent.generate_strategy(
            industry=industry_key,
            product_name=product_name,
        ) or {}

        # 3. Visual direction
        visual = VisualDirection()
        style_params = visual.extract_style_params(brief)
        visual_direction = {
            "style_params": style_params,
            "moodboard_context": visual.build_moodboard_context(style_params),
        }

        # 4. Creative angle from category template
        creative_angle = CREATIVE_ANGLES.get(category, "产品价值 + 场景化 + 情感共鸣")

        # 5. Content themes from platform
        content_themes = PLATFORM_THEMES.get(platform, ["主图", "详情", "场景图"])

        # 6. Mood keywords from brand + industry + visual
        mood_keywords = self._build_mood_keywords(
            brief, brand_guidelines, style_params, category
        )

        # 7. Visual approach summary
        visual_approach = self._build_visual_approach(
            category, platform, style_params
        )

        # 8. Build prompt context
        prompt_context = self._build_prompt_context(
            product_name=product_name,
            category=category,
            platform=platform,
            creative_angle=creative_angle,
            style_params=style_params,
            brand_guidelines=brand_guidelines,
            industry_insight=industry_insight,
        )

        return {
            "creative_angle": creative_angle,
            "visual_approach": visual_approach,
            "mood_keywords": mood_keywords,
            "content_themes": content_themes,
            "industry_insight": industry_insight,
            "brand_guidelines": brand_guidelines,
            "visual_direction": visual_direction,
            "prompt_context": prompt_context,
        }

    # -- helpers --

    def _resolve_industry_key(self, category: str) -> str:
        """Map category to industry_templates key."""
        mapping = {
            "美妆": "beauty",
            "食品": "food",
            "女装": "fashion",
            "3C数码": "electronics",
            "家居": "home_living",
        }
        return mapping.get(category, "home_living")

    def _get_industry_insight(self, category: str, platform: str) -> dict:
        """Get industry insight from research templates."""
        templates = RESEARCH_TEMPLATES.get(category, {})
        platform_data = templates.get(platform, {})
        if not platform_data:
            # Fallback: try first available platform
            for plat_data in templates.values():
                platform_data = plat_data
                break
        return {
            "competitors": platform_data.get("competitors", []),
            "trends": platform_data.get("trends", []),
            "price_range": platform_data.get("price_range", ""),
            "hot_topics": platform_data.get("hot_topics", []),
        }

    def _build_mood_keywords(
        self,
        brief: dict,
        brand_guidelines: dict,
        style_params: dict,
        category: str,
    ) -> list:
        """Build mood keywords from brand + visual + category."""
        keywords = list(style_params.get("style_keywords", []))
        brand_style = brief.get("brand_style", "")
        if brand_style:
            for k in brand_style.split("/"):
                k = k.strip()
                if k and k not in keywords:
                    keywords.append(k)
        return keywords

    def _build_visual_approach(
        self,
        category: str,
        platform: str,
        style_params: dict,
    ) -> str:
        """Build visual approach summary."""
        primary = style_params.get("primary_color", "#333")
        composition = style_params.get("composition", "centered")
        platform_hint = {
            "xiaohongshu": "高级感 + 生活化场景",
            "douyin": "动态 + 冲击力 + 快节奏",
            "taobao": "信任感 + 细节清晰 + 白底为主",
        }.get(platform, "专业 + 清晰")
        return f"{platform_hint}，主色{primary}，{composition}构图"

    def _build_prompt_context(
        self,
        product_name: str,
        category: str,
        platform: str,
        creative_angle: str,
        style_params: dict,
        brand_guidelines: dict,
        industry_insight: dict,
    ) -> str:
        """Build combined prompt context string."""
        trends = "、".join(industry_insight.get("trends", [])[:3])
        keywords = "、".join(style_params.get("style_keywords", []))
        return (
            f"产品：{product_name}，品类：{category}，平台：{platform}。"
            f"创意角度：{creative_angle}。"
            f"行业趋势：{trends}。"
            f"风格关键词：{keywords}。"
        )
