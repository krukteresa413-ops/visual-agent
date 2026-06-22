"""
测试 Creative Strategy Agent。
PRD Step 3: 创意策略 — 确定整体方向，综合 Brand + Research + Visual。
"""

import pytest


SAMPLE_BRIEF = {
    "product_name": "天然植萃洗发水",
    "category": "美妆",
    "specifications": ["500ml", "无硅油", "含茶树精油"],
    "selling_points": ["控油去屑", "天然成分", "温和不刺激"],
    "target_market": ["国内"],
    "usage_scenarios": ["家庭日常", "美发沙龙"],
    "brand_style": "清新/自然/专业",
}

SAMPLE_PLATFORM = "xiaohongshu"


class TestCreativeStrategyAgent:
    """Test CreativeStrategyAgent — orchestrates brand + research + visual."""

    def test_generate_creative_strategy(self):
        """Should generate creative strategy from brief + platform."""
        from app.services.creative_strategy import CreativeStrategyAgent

        agent = CreativeStrategyAgent()
        strategy = agent.generate_strategy(
            brief=SAMPLE_BRIEF,
            platform=SAMPLE_PLATFORM,
        )

        assert strategy is not None
        assert "creative_angle" in strategy
        assert "visual_approach" in strategy
        assert "mood_keywords" in strategy
        assert "content_themes" in strategy
        assert isinstance(strategy["mood_keywords"], list)
        assert len(strategy["mood_keywords"]) > 0

    def test_strategy_includes_industry_context(self):
        """Strategy should reference industry data from research templates."""
        from app.services.creative_strategy import CreativeStrategyAgent

        agent = CreativeStrategyAgent()
        strategy = agent.generate_strategy(
            brief=SAMPLE_BRIEF,
            platform=SAMPLE_PLATFORM,
        )

        # Should include competitor/trend info from research_templates
        assert "industry_insight" in strategy
        assert isinstance(strategy["industry_insight"], dict)

    def test_strategy_includes_brand_guidelines(self):
        """Strategy should incorporate brand strategy guidelines."""
        from app.services.creative_strategy import CreativeStrategyAgent

        agent = CreativeStrategyAgent()
        strategy = agent.generate_strategy(
            brief=SAMPLE_BRIEF,
            platform=SAMPLE_PLATFORM,
        )

        assert "brand_guidelines" in strategy
        assert "visual_direction" in strategy

    def test_strategy_falls_back_with_minimal_input(self):
        """Should not crash with minimal brief (missing fields)."""
        from app.services.creative_strategy import CreativeStrategyAgent

        agent = CreativeStrategyAgent()
        minimal = {"product_name": "测试产品", "category": "其他"}
        strategy = agent.generate_strategy(
            brief=minimal,
            platform="taobao",
        )

        assert strategy is not None
        assert "creative_angle" in strategy
        # Should still produce valid output even with minimal input

    def test_strategy_output_is_serializable(self):
        """Strategy output should be JSON-serializable."""
        import json
        from app.services.creative_strategy import CreativeStrategyAgent

        agent = CreativeStrategyAgent()
        strategy = agent.generate_strategy(
            brief=SAMPLE_BRIEF,
            platform=SAMPLE_PLATFORM,
        )

        # Should not raise
        encoded = json.dumps(strategy, ensure_ascii=False)
        assert len(encoded) > 0

    def test_strategy_differs_by_platform(self):
        """Different platforms should produce different strategies."""
        from app.services.creative_strategy import CreativeStrategyAgent

        agent = CreativeStrategyAgent()
        s1 = agent.generate_strategy(brief=SAMPLE_BRIEF, platform="xiaohongshu")
        s2 = agent.generate_strategy(brief=SAMPLE_BRIEF, platform="douyin")

        # Platform-specific recommendations should differ
        assert s1["content_themes"] != s2["content_themes"]

    def test_prompt_context_includes_platform_trends(self):
        """Generated prompt context should mention platform-specific trends."""
        from app.services.creative_strategy import CreativeStrategyAgent

        agent = CreativeStrategyAgent()
        strategy = agent.generate_strategy(
            brief=SAMPLE_BRIEF,
            platform=SAMPLE_PLATFORM,
        )

        ctx = strategy.get("prompt_context", "")
        assert len(ctx) > 0
        # Should reference relevant style keywords
        assert any(
            word in ctx
            for word in ["清新", "自然", "纯净", "国风", "伪素颜"]
        )
