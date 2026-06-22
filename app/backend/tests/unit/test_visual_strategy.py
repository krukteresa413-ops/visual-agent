"""
Visual Strategy tests — adapted for refactored generate_all (2026-06-16).

generate_visual_strategy and generate_all_parallel were removed.
Strategy is now implicit in sub-generators; all generation flows through generate_all.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.schemas.visual_strategy import VisualStrategy
from app.services.visual_agent import VisualAgent


SAMPLE_BRIEF = {
    "product_name": "Commercial Chest Freezer",
    "category": "Commercial Refrigeration",
    "specifications": ["300L", "stainless steel", "low noise"],
    "selling_points": ["fast cooling", "energy saving", "OEM customization"],
    "target_market": ["US", "EU"],
    "target_customer": ["supermarket buyer", "restaurant owner"],
    "usage_scenarios": ["supermarket", "restaurant", "convenience store"],
    "brand_style": "clean, professional, industrial",
    "compliance_notes": ["avoid unverifiable certification claims"],
}

MOCK_STRATEGY_OUTPUT = {
    "visual_positioning": "专业商用制冷解决方案",
    "target_customer_analysis": "超市采购商关注能效和可靠性",
    "visual_style": "工业专业风格，蓝灰调，产品居中",
    "selling_points_priority": [
        {"rank": 1, "point": "Fast Cooling", "rationale": "核心差异化卖点"},
        {"rank": 2, "point": "Energy Saving", "rationale": "降低运营成本"},
        {"rank": 3, "point": "OEM Customization", "rationale": "灵活适配不同市场需求"},
    ],
    "asset_plan_summary": {
        "main_image": "展示300L大容量和工业级不锈钢质感",
        "white_bg": "标准电商白底，展示产品正面和侧面",
        "scene_images": "超市、餐厅后厨、便利店三个场景",
        "selling_points": "快速制冷、节能、OEM定制三张卖点图",
        "video_scripts": "15秒产品演示+30秒品牌故事",
        "ad_material": "Facebook/Google广告素材，强调性价比",
    },
    "brand_tone": "Professional, reliable, solution-oriented",
    "audience_type": "B2B",
    "key_differentiators": "fast cooling speed, 30% energy saving, full customization",
}


class TestVisualStrategySchema:
    """VisualStrategy 模型校验"""

    def test_valid_strategy(self):
        strategy = VisualStrategy(**MOCK_STRATEGY_OUTPUT)
        assert strategy.visual_positioning == "专业商用制冷解决方案"
        assert strategy.audience_type == "B2B"
        assert len(strategy.selling_points_priority) == 3
        assert strategy.asset_plan_summary["main_image"] is not None

    def test_selling_points_have_rank(self):
        strategy = VisualStrategy(**MOCK_STRATEGY_OUTPUT)
        ranks = [sp.rank for sp in strategy.selling_points_priority]
        assert ranks == sorted(ranks)

    def test_optional_fields_default(self):
        minimal = {
            "visual_positioning": "定位",
            "visual_style": "风格",
            "selling_points_priority": [],
            "brand_tone": "tone",
            "audience_type": "B2B",
            "key_differentiators": "none",
        }
        strategy = VisualStrategy(**minimal)
        assert strategy.target_customer_analysis is None
        assert strategy.asset_plan_summary is None

    def test_audience_type_validation(self):
        data = {**MOCK_STRATEGY_OUTPUT, "audience_type": "B2C"}
        strategy = VisualStrategy(**data)
        assert strategy.audience_type == "B2C"

        data["audience_type"] = "invalid"
        with pytest.raises(Exception):
            VisualStrategy(**data)


class TestGenerateAllIntegration:
    """generate_all replaces old generate_all_parallel — tests multi-generator flow."""

    @pytest.mark.asyncio
    @patch("app.services.visual_agent.VisualAgent.generate_images_from_plan", new_callable=AsyncMock)
    @patch("app.services.layout_agent.LayoutAgent.generate_layout", new_callable=AsyncMock)
    async def test_generate_all_includes_brief_context(self, mock_layout, mock_render):
        """Verify sub-generators receive brief context via generate_all."""
        agent = VisualAgent()
        mock_render.return_value = {"main_image": None, "white_bg": None, "scene_images": []}
        mock_layout.side_effect = Exception("layout skipped in unit test")

        mock_llm = AsyncMock()

        # Mock 6 sub-generator calls
        mock_llm.call.side_effect = [
            {"asset_type": "main_image", "goal": "...", "composition": "...",
             "background": "...", "prompt": "A freezer...", "status": "draft"},
            {"asset_type": "white_bg", "goal": "...", "instructions": "...", "status": "draft"},
            [{"scene_name": "supermarket", "target_user": "...", "scene_narrative": "...",
              "visual_elements": [], "product_position": "...", "prompt": "..."}],
            [{"title": "Fast", "description": "...", "visual_representation": "...",
              "icon_suggestion": "...", "layout_suggestion": "..."}],
            [{"video_goal": "...", "duration_seconds": 15, "storyboard": [],
              "cta": "...", "material_requirements": [], "pacing": "fast"}],
            {"ad_goal": "...", "target_audience": "...", "ad_angle": "...",
             "material_list": [], "shot_sequence": [], "hook": "...",
             "key_selling_points": [], "cta": "...", "platform_suggestion": "..."},
        ]
        agent._llm = mock_llm

        result = await agent.generate_all(project_id=1, brief=SAMPLE_BRIEF)
        assert result is not None
        # 6 sub-generator calls (layout agent may add more)
        assert mock_llm.call.call_count >= 6

    @pytest.mark.asyncio
    @patch("app.services.visual_agent.VisualAgent.generate_images_from_plan", new_callable=AsyncMock)
    @patch("app.services.layout_agent.LayoutAgent.generate_layout", new_callable=AsyncMock)
    async def test_generate_all_passes_brief_to_main_image(self, mock_layout, mock_render):
        """Verify main_image generator receives product info."""
        agent = VisualAgent()
        mock_render.return_value = {"main_image": None, "white_bg": None, "scene_images": []}
        mock_layout.side_effect = Exception("layout skipped in unit test")

        mock_llm = AsyncMock()

        mock_llm.call.side_effect = [
            {"asset_type": "main_image", "goal": "...", "composition": "...",
             "background": "...", "prompt": "...", "status": "draft"},
            {"asset_type": "white_bg", "goal": "...", "instructions": "...", "status": "draft"},
            [{"scene_name": "s", "target_user": "...", "scene_narrative": "...",
              "visual_elements": [], "product_position": "...", "prompt": "..."}],
            [{"title": "X", "description": "...", "visual_representation": "...",
              "icon_suggestion": "...", "layout_suggestion": "..."}],
            [{"video_goal": "...", "duration_seconds": 15, "storyboard": [],
              "cta": "...", "material_requirements": [], "pacing": "fast"}],
            {"ad_goal": "...", "target_audience": "...", "ad_angle": "...",
             "material_list": [], "shot_sequence": [], "hook": "...",
             "key_selling_points": [], "cta": "...", "platform_suggestion": "..."},
        ]
        agent._llm = mock_llm

        await agent.generate_all(project_id=1, brief=SAMPLE_BRIEF)

        # First call is main_image
        call_args = mock_llm.call.call_args_list[0]
        user_prompt = call_args.kwargs.get("user_prompt", "")
        assert "Commercial Chest Freezer" in user_prompt, (
            "FAIL: main_image should receive product name in prompt"
        )

    @pytest.mark.asyncio
    @patch("app.services.visual_agent.VisualAgent.generate_images_from_plan", new_callable=AsyncMock)
    @patch("app.services.layout_agent.LayoutAgent.generate_layout", new_callable=AsyncMock)
    async def test_generate_all_returns_structured_result(self, mock_layout, mock_render):
        """generate_all returns VisualAssetPlanOut with modules."""
        agent = VisualAgent()
        mock_render.return_value = {"main_image": None, "white_bg": None, "scene_images": []}
        mock_layout.side_effect = Exception("layout skipped in unit test")

        mock_llm = AsyncMock()

        mock_llm.call.side_effect = [
            {"asset_type": "main_image", "goal": "...", "composition": "...",
             "background": "...", "prompt": "test", "status": "draft"},
            {"asset_type": "white_bg", "goal": "...", "instructions": "...", "status": "draft"},
            [{"scene_name": "s", "target_user": "...", "scene_narrative": "...",
              "visual_elements": [], "product_position": "...", "prompt": "..."}],
            [{"title": "X", "description": "...", "visual_representation": "...",
              "icon_suggestion": "...", "layout_suggestion": "..."}],
            [{"video_goal": "...", "duration_seconds": 15, "storyboard": [],
              "cta": "...", "material_requirements": [], "pacing": "fast"}],
            {"ad_goal": "...", "target_audience": "...", "ad_angle": "...",
             "material_list": [], "shot_sequence": [], "hook": "...",
             "key_selling_points": [], "cta": "...", "platform_suggestion": "..."},
        ]
        agent._llm = mock_llm

        result = await agent.generate_all(project_id=1, brief=SAMPLE_BRIEF)
        assert hasattr(result, "main_image")
        assert hasattr(result, "scene_images")

    @pytest.mark.asyncio
    @patch("app.services.visual_agent.VisualAgent.generate_images_from_plan", new_callable=AsyncMock)
    @patch("app.services.layout_agent.LayoutAgent.generate_layout", new_callable=AsyncMock)
    async def test_generate_all_call_count(self, mock_layout, mock_render):
        """generate_all calls 6 sub-generators + optional layout agent."""
        agent = VisualAgent()
        mock_render.return_value = {"main_image": None, "white_bg": None, "scene_images": []}
        mock_layout.side_effect = Exception("layout skipped in unit test")

        mock_llm = AsyncMock()

        mock_llm.call.side_effect = [
            {"asset_type": "main_image", "goal": "...", "composition": "...",
             "background": "...", "prompt": "...", "status": "draft"},
            {"asset_type": "white_bg", "goal": "...", "instructions": "...", "status": "draft"},
            [{"scene_name": "s", "target_user": "...", "scene_narrative": "...",
              "visual_elements": [], "product_position": "...", "prompt": "..."}],
            [{"title": "X", "description": "...", "visual_representation": "...",
              "icon_suggestion": "...", "layout_suggestion": "..."}],
            [{"video_goal": "...", "duration_seconds": 15, "storyboard": [],
              "cta": "...", "material_requirements": [], "pacing": "fast"}],
            {"ad_goal": "...", "target_audience": "...", "ad_angle": "...",
             "material_list": [], "shot_sequence": [], "hook": "...",
             "key_selling_points": [], "cta": "...", "platform_suggestion": "..."},
        ]
        agent._llm = mock_llm

        await agent.generate_all(project_id=1, brief=SAMPLE_BRIEF)
        # At least 6 calls for the 6 generator types
        assert mock_llm.call.call_count >= 6
