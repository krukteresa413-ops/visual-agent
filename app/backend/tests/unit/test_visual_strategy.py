"""
创意策略层测试。
验证：VisualStrategy schema → generate_visual_strategy → 策略注入 generate_all_parallel
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.schemas.visual_strategy import VisualStrategy
from app.services.visual_agent import VisualAgent


# 用现有的 SAMPLE_BRIEF
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
        assert ranks == sorted(ranks)  # 按 rank 排序

    def test_optional_fields_default(self):
        """只有必填字段也能通过"""
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
        """audience_type 只能是 B2B 或 B2C"""
        data = {**MOCK_STRATEGY_OUTPUT, "audience_type": "B2C"}
        strategy = VisualStrategy(**data)
        assert strategy.audience_type == "B2C"

        data["audience_type"] = "invalid"
        with pytest.raises(Exception):
            VisualStrategy(**data)


class TestGenerateVisualStrategy:
    """generate_visual_strategy 方法测试"""

    @pytest.mark.asyncio
    async def test_generates_structured_strategy(self):
        """验证策略生成返回结构化 VisualStrategy"""
        agent = VisualAgent()
        mock_llm = AsyncMock()
        mock_llm.call.return_value = MOCK_STRATEGY_OUTPUT
        agent._llm = mock_llm

        strategy = await agent.generate_visual_strategy(SAMPLE_BRIEF)
        assert isinstance(strategy, VisualStrategy)
        assert strategy.visual_positioning is not None
        assert strategy.audience_type in ("B2B", "B2C")

    @pytest.mark.asyncio
    async def test_strategy_includes_brief_context(self):
        """策略应引用产品信息"""
        agent = VisualAgent()
        mock_llm = AsyncMock()
        mock_llm.call.return_value = MOCK_STRATEGY_OUTPUT
        agent._llm = mock_llm

        strategy = await agent.generate_visual_strategy(SAMPLE_BRIEF)
        # 验证 LLM 被调用时传入了产品信息
        call_args = mock_llm.call.call_args
        user_prompt = call_args.kwargs.get("user_prompt", "")
        assert "Commercial Chest Freezer" in user_prompt
        assert "fast cooling" in user_prompt


class TestStrategyInjection:
    """策略注入到子生成器"""

    @pytest.mark.asyncio
    async def test_strategy_enriches_brief_for_sub_generators(self):
        """验证 generate_all_parallel 将策略注入 brief 上下文"""
        agent = VisualAgent()
        mock_llm = AsyncMock()
        # 策略调用返回 strategy
        # 每个子生成器调用返回对应的 mock 结果
        mock_llm.call.side_effect = [
            MOCK_STRATEGY_OUTPUT,  # generate_visual_strategy
            # 6 个子生成器返回（简化 mock）
            {"asset_type": "main_image", "goal": "...", "composition": "...", "background": "...",
             "prompt": "A freezer...", "status": "draft"},
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

        from app.schemas.visual_assets import VisualAssetPlanOut
        result = await agent.generate_all_parallel(project_id=1, brief=SAMPLE_BRIEF)
        assert isinstance(result, VisualAssetPlanOut)
        # 验证共调用了 7 次 LLM (1 策略 + 6 素材)
        assert mock_llm.call.call_count == 7

    @pytest.mark.asyncio
    async def test_strategy_context_passed_to_main_image(self):
        """验证 main_image 生成时收到策略上下文"""
        agent = VisualAgent()
        mock_llm = AsyncMock()

        mock_llm.call.side_effect = [
            MOCK_STRATEGY_OUTPUT,
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

        await agent.generate_all_parallel(project_id=1, brief=SAMPLE_BRIEF)

        # 第二次 LLM 调用（index 1）是 main_image
        call_args = mock_llm.call.call_args_list[1]
        system_prompt = call_args.kwargs.get("system_prompt", "")
        assert "创意策略" in system_prompt, (
            "FAIL: main_image 的 system_prompt 未收到策略上下文！"
            "generate_all_parallel 应在调用子生成器时注入 strategy 上下文。"
        )
