"""Platform trend research service — LLM-powered trend analysis (P2.3).

Researches trending products, visual styles, and copywriting patterns
across Chinese e-commerce platforms per category.
"""
import asyncio
from app.services.llm_utils import parse_json

from app.models.research_models import PlatformTrend, ResearchReport


RESEARCH_SYSTEM_PROMPT = """You are an e-commerce trend analyst specializing in Chinese platforms (Taobao, JD, PDD, Douyin, Xiaohongshu).

Given a platform and product category, analyze current trends. Output ONLY valid JSON:

{
    "platform": "平台名",
    "category": "品类",
    "trends": ["trend1", "trend2", "trend3"],
    "visual_styles": ["style1", "style2", "style3"],
    "copywriting_patterns": ["pattern1", "pattern2", "pattern3"],
    "price_range": "价格区间",
    "hot_keywords": ["#关键词1", "#关键词2", "#关键词3"]
}

Rules:
- trends: current popular styles/subcategories (3-5 items)
- visual_styles: photography style, color palette, composition patterns (3-5 items)
- copywriting_patterns: common copywriting structures used by top sellers (3-5 items)
- price_range: typical price band for this category on this platform
- hot_keywords: popular hashtags and search terms
- All text should match the platform's language (Chinese for Chinese platforms)
"""

RECOMMENDATION_PROMPT = """Based on the following platform trends, generate 3-5 actionable template recommendations for MOYAG (a visual content generation platform for e-commerce).

Each recommendation should suggest a specific visual template type that MOYAG should build, with a brief rationale tied to the trends.

Output format (JSON array of strings):
["recommendation 1", "recommendation 2", ...]
"""


class PlatformTrendService:
    """Researches e-commerce trends per platform + category using LLM."""

    def __init__(self, llm_client):
        self._llm = llm_client

    async def research_platform(self, platform: str, category: str) -> PlatformTrend:
        """Research trends for a single platform + category.

        Args:
            platform: Platform name (taobao, jd, pdd, douyin, xiaohongshu).
            category: Product category in Chinese (e.g., "女装", "美妆").

        Returns:
            PlatformTrend with structured trend data.
        """
        user_prompt = f"分析 {platform} 平台上「{category}」品类的当前趋势"

        try:
            raw = await self._llm.generate(
                system=RESEARCH_SYSTEM_PROMPT,
                prompt=user_prompt,
            )
            data = parse_json(raw)
        except Exception:
            # Return a fallback with error indicator
            return PlatformTrend(
                platform=platform,
                category=category,
                trends=["数据获取失败"],
                visual_styles=["待重新采集"],
                copywriting_patterns=["待重新采集"],
                price_range="N/A",
                hot_keywords=["#待更新"],
            )

        return PlatformTrend(
            platform=data.get("platform", platform),
            category=data.get("category", category),
            trends=(data.get("trends") or [])[:5],
            visual_styles=(data.get("visual_styles") or [])[:5],
            copywriting_patterns=(data.get("copywriting_patterns") or [])[:5],
            price_range=data.get("price_range") or "N/A",
            hot_keywords=(data.get("hot_keywords") or [])[:5],
        )

    async def research_category(
        self, category: str, platforms: list[str]
    ) -> ResearchReport:
        """Research trends across multiple platforms for a category.

        Runs all platform queries concurrently.

        Args:
            category: Product category in Chinese.
            platforms: List of platform names to research.

        Returns:
            ResearchReport with aggregated findings and recommendations.
        """
        tasks = [self.research_platform(p, category) for p in platforms]
        results = await asyncio.gather(*tasks)

        recommendations = self.synthesize_recommendations(results)
        summary = self._build_summary(category, results)

        return ResearchReport(
            category=category,
            platforms=list(results),
            summary=summary,
            moe_recommendations=recommendations,
        )

    @staticmethod
    def synthesize_recommendations(trends: list[PlatformTrend]) -> list[str]:
        """Generate template recommendations from collected trends.

        Args:
            trends: List of PlatformTrend results.

        Returns:
            List of recommendation strings.
        """
        recs = []

        # Collect all trends across platforms
        all_trends = []
        all_styles = []
        all_keywords = []
        for t in trends:
            all_trends.extend(t.trends)
            all_styles.extend(t.visual_styles)
            all_keywords.extend(t.hot_keywords)

        # Generate recommendations based on collected data
        if all_trends:
            top_trends = list(dict.fromkeys(all_trends))[:3]
            recs.append(f"创建「{'/'.join(top_trends[:2])}」风格模板，覆盖{trends[0].category}品类热门口味")

        if all_styles:
            top_styles = list(dict.fromkeys(all_styles))[:2]
            recs.append(f"视觉风格包：整合{top_styles[0]}等流行视觉风格，支持一键切换")

        if all_keywords:
            top_kw = list(dict.fromkeys(all_keywords))[:2]
            recs.append(f"文案模板：内置{top_kw[0]}等热门话题标签，提升搜索曝光")

        # Platform-specific recommendations
        platform_names = [t.platform for t in trends if "数据获取失败" not in t.trends]
        if len(platform_names) >= 2:
            recs.append(f"跨平台适配模板：统一视觉风格下自动适配{'/'.join(platform_names[:3])}不同尺寸规格")

        # Always ensure we have at least 2 recommendations
        if not trends:
            return ["通用电商模板：整合主流平台视觉规范", "品牌定制模板：根据品牌色系自动适配"]
        if len(recs) < 2:
            recs.append(f"通用{trends[0].category}电商模板：整合主流平台视觉规范")

        return recs

    def _build_summary(self, category: str, results: list[PlatformTrend]) -> str:
        """Build a human-readable summary from platform results."""
        success = [r for r in results if "数据获取失败" not in r.trends]
        failed = [r for r in results if "数据获取失败" in r.trends]

        parts = [f"{category}品类跨平台趋势分析："]
        if success:
            platforms_str = "、".join(r.platform for r in success)
            all_trends = set()
            for r in success:
                all_trends.update(r.trends)
            parts.append(f"成功采集 {platforms_str} 共 {len(success)} 个平台。")
            if all_trends:
                parts.append(f"热门趋势：{'、'.join(list(all_trends)[:5])}。")
        if failed:
            parts.append(f"{len(failed)} 个平台采集失败。")

        return "".join(parts)

