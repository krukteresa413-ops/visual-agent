"""
Visual Agent 服务测试。
验证：给定 ProductBrief → 调用LLM → 返回结构化的六类素材方案。
用 mock 替代 LLM 真实调用。
"""
import pytest
from unittest.mock import AsyncMock, patch

# 测试用的 Product Brief 数据（PRD第14节：Commercial Chest Freezer）
SAMPLE_BRIEF = {
    "product_name": "Commercial Chest Freezer",
    "category": "Commercial Refrigeration",
    "specifications": ["300L", "stainless steel", "low noise"],
    "materials": ["stainless steel"],
    "selling_points": ["fast cooling", "energy saving", "OEM customization"],
    "target_market": ["US", "EU"],
    "target_customer": ["supermarket buyer", "restaurant owner"],
    "usage_scenarios": ["supermarket", "restaurant", "convenience store"],
    "brand_style": "clean, professional, industrial",
    "compliance_notes": ["avoid unverifiable certification claims"],
}


# 模拟 LLM 返回
MOCK_MAIN_IMAGE = {
    "asset_type": "main_image",
    "goal": "展示300L不锈钢商用冷柜的专业品质",
    "composition": "产品居中，45度角，展示不锈钢表面质感",
    "background": "浅灰色工业风背景",
    "lighting": "柔光，突出金属质感",
    "copywriting": "300L Commercial Chest Freezer - Fast Cooling",
    "prompt": "A 300L commercial chest freezer, stainless steel body, centered composition, 45-degree angle, light gray industrial background, soft studio lighting, product photography, 4K, high detail",
    "negative_prompt": "no fake certification logo, no unrealistic ice effect",
    "platform": "Alibaba.com",
    "status": "draft",
}

MOCK_WHITE_BG = {
    "asset_type": "white_bg",
    "goal": "为平台上架提供标准白底产品图",
    "instructions": "产品正面及侧面各一张，纯白背景，无阴影",
    "quality_checklist": ["主体完整", "背景纯白", "无多余元素"],
    "status": "draft",
}

MOCK_SCENES = [
    {
        "scene_name": "supermarket",
        "target_user": "supermarket buyer",
        "scene_narrative": "冷柜放置在超市冷藏区，周围有食品",
        "visual_elements": ["超市货架", "食品", "顾客"],
        "product_position": "前景居中",
        "prompt": "A commercial chest freezer in a modern supermarket...",
    }
]

MOCK_SELLING_POINTS = [
    {
        "title": "Fast Cooling Performance",
        "description": "Stable temperature control for commercial use",
        "visual_representation": "温度曲线下降图",
        "icon_suggestion": "snowflake",
        "layout_suggestion": "左图右文",
    },
    {
        "title": "Energy Saving Design",
        "description": "Reduces electricity costs by up to 30%",
        "visual_representation": "能耗对比柱状图",
        "icon_suggestion": "energy",
        "layout_suggestion": "上下结构",
    },
    {
        "title": "OEM Customization",
        "description": "Logo, color, and capacity customizable",
        "visual_representation": "多色产品阵列",
        "icon_suggestion": "palette",
        "layout_suggestion": "四宫格",
    },
]

MOCK_SCRIPTS = [
    {
        "video_goal": "引流",
        "duration_seconds": 15,
        "storyboard": [
            {"shot_number": 1, "duration": "0-3s", "visual": "产品全景", "subtitle": "Need Reliable Cooling?", "voiceover": "Looking for a freezer you can trust?"}
        ],
        "cta": "Learn More",
        "material_requirements": ["产品白底图", "Logo"],
        "pacing": "钩子→卖点→CTA",
    },
    {
        "video_goal": "转化",
        "duration_seconds": 30,
        "storyboard": [
            {"shot_number": 1, "duration": "0-5s", "visual": "痛点场景", "subtitle": "Tired of breakdowns?", "voiceover": "Commercial freezers that keep failing?"}
        ],
        "cta": "Get Quote",
        "material_requirements": ["产品白底图", "场景图", "Logo"],
        "pacing": "痛点→解决方案→卖点展开→信任背书→CTA",
    },
]

MOCK_AD_MATERIAL = {
    "ad_goal": "冷启动引流",
    "target_audience": "B2B distributors",
    "ad_angle": "产品可靠性",
    "material_list": ["产品全景图", "工厂实拍"],
    "shot_sequence": ["钩子", "卖点1", "卖点2", "CTA"],
    "hook": "Tired of unreliable freezers?",
    "key_selling_points": ["fast cooling", "energy saving"],
    "cta": "Get Quote",
    "platform_suggestion": "Meta Ads",
}


class TestVisualAgent:

    @pytest.mark.asyncio
    async def test_generate_main_image_plan(self):
        """单独生成主图方案"""
        from app.services.visual_agent import VisualAgent

        agent = VisualAgent()

        with patch.object(agent._llm, "call", new_callable=AsyncMock, return_value=MOCK_MAIN_IMAGE):
            result = await agent.generate_main_image(SAMPLE_BRIEF)

        assert result.asset_type == "main_image"
        assert "300L" in result.prompt or "chest freezer" in result.prompt

    @pytest.mark.asyncio
    async def test_generate_all_six_types(self):
        """
        PRD 5.2 成功指标：六类输出覆盖率 100%
        验证一次 generate_all 调用能返回六类素材。
        """
        from app.services.visual_agent import VisualAgent

        agent = VisualAgent()

        # 按调用顺序 mock 六次 LLM 调用
        agent._llm.call = AsyncMock(side_effect=[
            MOCK_MAIN_IMAGE,
            MOCK_WHITE_BG,
            MOCK_SCENES,
            MOCK_SELLING_POINTS,
            MOCK_SCRIPTS,
            MOCK_AD_MATERIAL,
        ])

        with patch("app.services.visual_agent.VisualAgent.generate_images_from_plan", new_callable=AsyncMock) as mock_render, \
             patch("app.services.layout_agent.LayoutAgent.generate_layout", new_callable=AsyncMock) as mock_layout:
            mock_render.return_value = {"main_image": None, "white_bg": None, "scene_images": []}
            mock_layout.side_effect = Exception("layout skipped in unit test")
            result = await agent.generate_all(project_id=1, brief=SAMPLE_BRIEF)

        assert result.main_image is not None
        assert result.white_bg is not None
        assert len(result.scene_images) >= 1
        assert len(result.selling_points) >= 3  # PRD要求3-5
        assert len(result.video_scripts) == 2   # PRD要求15s+30s
        assert result.ad_material is not None
