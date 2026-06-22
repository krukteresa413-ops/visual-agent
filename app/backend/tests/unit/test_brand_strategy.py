"""
测试 Brand Strategy Agent。
PRD P2.1: Template-based brand strategy generation, no LLM.
"""
import pytest


class TestBrandStrategyAgent:
    """Test brand strategy agent template-based generation."""

    def test_generate_strategy_from_industry_template(self):
        """Should generate brand strategy from industry template."""
        from app.services.brand_strategy import BrandStrategyAgent

        agent = BrandStrategyAgent()
        strategy = agent.generate_strategy(
            industry="machinery",
            product_name="Industrial Freezer",
            target_audience="B2B procurement managers"
        )

        assert strategy is not None
        assert "visual_style" in strategy
        assert "color_palette" in strategy
        assert "tone_of_voice" in strategy
        assert "forbidden_elements" in strategy
        assert strategy["visual_style"] == "硬朗、金属质感"

    def test_generate_strategy_with_unknown_industry(self):
        """Should return None or empty strategy for unknown industry."""
        from app.services.brand_strategy import BrandStrategyAgent

        agent = BrandStrategyAgent()
        strategy = agent.generate_strategy(
            industry="unknown_industry_xyz",
            product_name="Test Product"
        )

        assert strategy is None or strategy == {}

    def test_generate_copywriting_guidelines(self):
        """Should generate copywriting guidelines from industry template."""
        from app.services.brand_strategy import BrandStrategyAgent

        agent = BrandStrategyAgent()
        guidelines = agent.generate_copywriting_guidelines(industry="fashion")

        assert guidelines is not None
        assert "tone" in guidelines
        assert "forbidden" in guidelines
        assert guidelines["tone"] == "时尚感"
        assert len(guidelines["forbidden"]) > 0

    def test_generate_visual_keywords(self):
        """Should extract visual keywords from industry template."""
        from app.services.brand_strategy import BrandStrategyAgent

        agent = BrandStrategyAgent()
        keywords = agent.generate_visual_keywords(industry="beauty")

        assert keywords is not None
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Should contain keywords related to beauty industry

    def test_strategy_includes_prompt_modifiers(self):
        """Strategy should include prompt modifiers for image generation."""
        from app.services.brand_strategy import BrandStrategyAgent

        agent = BrandStrategyAgent()
        strategy = agent.generate_strategy(
            industry="electronics",
            product_name="Smart Watch"
        )

        assert "prompt_modifiers" in strategy
        assert "tech product photography" in strategy["prompt_modifiers"]

    def test_strategy_includes_scene_suggestions(self):
        """Strategy should include scene suggestions from template."""
        from app.services.brand_strategy import BrandStrategyAgent

        agent = BrandStrategyAgent()
        strategy = agent.generate_strategy(
            industry="pet",
            product_name="Dog Food Bowl"
        )

        assert "scene_suggestions" in strategy
        assert len(strategy["scene_suggestions"]) > 0
        assert isinstance(strategy["scene_suggestions"], list)
