"""
Layout Agent 单元测试。
测试 schema 验证、LayoutPlan 构建、layout 生成逻辑。
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.schemas.layout_plan import (
    LayoutElement,
    MainImageLayout,
    DetailPageLayout,
    DetailPageModuleLayout,
    SellingPointModuleLayout,
    SceneImageLayout,
    SocialPostLayout,
    LayoutPlan,
)

# ══════════════════════════════════════════════════════════
# Schema 验证 — 合法数据
# ══════════════════════════════════════════════════════════

class TestLayoutElement:
    def test_valid_element(self):
        el = LayoutElement(
            element_type="title",
            content="300L 商用冷柜",
            x_pct=5, y_pct=5,
            width_pct=90, height_pct=12,
            font_size_pt=36,
            font_weight="bold",
            color="#1a1a2e",
            alignment="left",
            z_index=10,
        )
        assert el.element_type == "title"
        assert el.font_size_pt == 36

    def test_element_defaults(self):
        el = LayoutElement(
            element_type="body_text",
            content="正文",
            x_pct=10, y_pct=50,
            width_pct=80, height_pct=10,
        )
        assert el.font_size_pt == 14
        assert el.color == "#333333"
        assert el.alignment == "left"
        assert el.z_index == 1

    def test_element_type_variants(self):
        valid_types = [
            "title", "subtitle", "body_text", "cta_button",
            "product_image", "scene_image", "logo", "badge",
            "divider", "price_tag", "selling_point_icon",
        ]
        for t in valid_types:
            el = LayoutElement(
                element_type=t,
                content="test",
                x_pct=10, y_pct=10,
                width_pct=50, height_pct=50,
            )
            assert el.element_type == t


class TestMainImageLayout:
    def test_basic(self):
        mi = MainImageLayout(
            canvas_width=800,
            canvas_height=800,
            layout_strategy="中心产品+左上品牌标+底部卖点条",
            title_hierarchy="主标题 36pt 左上 → 卖点 16pt 底部",
            elements=[
                LayoutElement(
                    element_type="title", content="新品上市",
                    x_pct=5, y_pct=5, width_pct=90, height_pct=12,
                    font_size_pt=36, font_weight="bold",
                ),
                LayoutElement(
                    element_type="product_image", content="",
                    x_pct=15, y_pct=25, width_pct=70, height_pct=55,
                ),
            ],
        )
        assert mi.asset_type == "main_image_layout"
        assert len(mi.elements) == 2
        assert mi.elements[0].font_weight == "bold"


class TestDetailPageLayout:
    def test_basic(self):
        module = DetailPageModuleLayout(
            module_name="hero_banner",
            height_px=600,
            layout_type="full_width_image",
            elements=[],
        )
        dp = DetailPageLayout(
            module_order=["hero_banner", "selling_point_1", "cta"],
            modules=[module],
        )
        assert dp.asset_type == "detail_page_layout"
        assert dp.canvas_width == 750
        assert len(dp.modules) == 1


class TestSellingPointModuleLayout:
    def test_basic(self):
        sp = SellingPointModuleLayout(
            icon_position="left",
            text_alignment="left",
            elements=[
                LayoutElement(
                    element_type="selling_point_icon", content="⚡",
                    x_pct=5, y_pct=10, width_pct=15, height_pct=80,
                ),
            ],
        )
        assert sp.asset_type == "selling_point_layout"
        assert sp.icon_position == "left"


class TestSceneImageLayout:
    def test_no_overlay(self):
        sl = SceneImageLayout(
            text_overlay_position="none",
            elements=[],
        )
        assert sl.asset_type == "scene_image_layout"


class TestSocialPostLayout:
    def test_xiaohongshu(self):
        sp = SocialPostLayout(
            platform="xiaohongshu",
            canvas_width=1080,
            canvas_height=1440,
            image_grid="single",
            elements=[
                LayoutElement(
                    element_type="title", content="种草标题",
                    x_pct=10, y_pct=5, width_pct=80, height_pct=10,
                    font_size_pt=42, font_weight="bold",
                ),
            ],
        )
        assert sp.platform == "xiaohongshu"
        assert sp.canvas_height == 1440


class TestLayoutPlan:
    def test_full_plan(self):
        plan = LayoutPlan(
            project_id=1,
            platform_id="taobao",
            global_style_notes="专业工业风",
            typography_rules="思源黑体 Bold 36pt 主标 / Regular 14pt 正文",
            color_system="主色 #1a1a2e 辅色 #e94560",
            main_image_layout=MainImageLayout(
                layout_strategy="test",
                title_hierarchy="test",
                elements=[],
            ),
        )
        assert plan.project_id == 1
        assert plan.main_image_layout is not None

    def test_model_dump_roundtrip(self):
        plan = LayoutPlan(
            project_id=1,
            global_style_notes="test",
            typography_rules="test",
            color_system="test",
        )
        dumped = plan.model_dump()
        reloaded = LayoutPlan(**dumped)
        assert reloaded.project_id == 1


# ══════════════════════════════════════════════════════════
# Layout Agent Service — mock LLM
# ══════════════════════════════════════════════════════════

MOCK_LLM_RESPONSE = {
    "global_style_notes": "专业工业风，干净清晰",
    "typography_rules": "思源黑体 Bold 36pt 主标 / 14pt 正文",
    "color_system": "主色 #1a1a2e 辅色 #e94560",
    "main_image_layout": {
        "canvas_width": 800,
        "canvas_height": 800,
        "background_color": "#ffffff",
        "layout_strategy": "中心产品+左上品牌标+底部卖点条",
        "title_hierarchy": "主标题 36pt 左上 → 卖点 16pt 底部",
        "elements": [
            {
                "element_type": "title", "content": "300L 商用冷柜",
                "x_pct": 5, "y_pct": 5, "width_pct": 90, "height_pct": 12,
                "font_size_pt": 36, "font_weight": "bold",
                "color": "#1a1a2e", "alignment": "left", "z_index": 10,
            }
        ],
    },
    "detail_page_layout": {
        "canvas_width": 750, "canvas_height": 6000,
        "module_order": ["hero_banner", "selling_point_1", "cta"],
        "modules": [
            {
                "module_name": "hero_banner", "height_px": 600,
                "background_color": "#f5f0e8",
                "layout_type": "full_width_image",
                "elements": [],
            }
        ],
    },
    "selling_point_layouts": [],
    "scene_image_layouts": [],
    "social_post_layout": None,
}


class TestLayoutAgent:
    @pytest.mark.asyncio
    async def test_generate_layout(self):
        from app.services.layout_agent import LayoutAgent

        agent = LayoutAgent()
        agent._llm.call = AsyncMock(return_value=MOCK_LLM_RESPONSE)

        brief = {
            "product_name": "300L 商用冷柜",
            "category": "商用制冷设备",
            "selling_points": ["快速制冷", "节能省电"],
            "target_market": ["US", "EU"],
            "target_customer": ["超市采购商"],
            "brand_style": "professional",
        }
        asset_plan = {
            "main_image": {
                "goal": "展示产品外观",
                "composition": "中心产品图",
                "copywriting": "Fast Cooling",
                "prompt": "commercial freezer product photo",
            },
            "scene_images": [],
            "selling_points": [],
            "video_scripts": [],
            "ad_material": None,
        }

        result = await agent.generate_layout(
            project_id=1,
            brief=brief,
            asset_plan=asset_plan,
            platform_id="taobao",
            brand_context="主色:#1a1a2e 辅色:#e94560",
        )

        assert isinstance(result, LayoutPlan)
        assert result.project_id == 1
        assert result.main_image_layout is not None
        assert len(result.main_image_layout.elements) == 1
        assert result.main_image_layout.elements[0].content == "300L 商用冷柜"

    @pytest.mark.asyncio
    async def test_generate_layout_no_brand(self):
        """无品牌上下文时也能正常生成。"""
        from app.services.layout_agent import LayoutAgent

        agent = LayoutAgent()
        agent._llm.call = AsyncMock(return_value=MOCK_LLM_RESPONSE)

        brief = {"product_name": "Test", "category": "Test"}
        asset_plan = {}

        result = await agent.generate_layout(
            project_id=1,
            brief=brief,
            asset_plan=asset_plan,
        )
        assert isinstance(result, LayoutPlan)

    @pytest.mark.asyncio
    async def test_generate_layout_no_platform(self):
        """无平台时也能正常生成。"""
        from app.services.layout_agent import LayoutAgent

        agent = LayoutAgent()
        agent._llm.call = AsyncMock(return_value=MOCK_LLM_RESPONSE)

        brief = {"product_name": "Test", "category": "Test"}
        asset_plan = {}

        result = await agent.generate_layout(
            project_id=1,
            brief=brief,
            asset_plan=asset_plan,
            platform_id=None,
        )
        assert result.platform_id is None


# ══════════════════════════════════════════════════════════
# 辅助函数测试
# ══════════════════════════════════════════════════════════

class TestSummarizeAssetPlan:
    def test_full_plan(self):
        from app.services.layout_agent import _summarize_asset_plan

        plan = {
            "main_image": {
                "goal": "展示产品外观",
                "composition": "中心产品",
                "copywriting": "Fast Cooling",
                "prompt": "product photo on white",
            },
            "scene_images": [
                {"scene": "超市冷柜区", "prompt": "supermarket freezer"},
                {"scene": "餐厅后厨", "prompt": "restaurant kitchen"},
            ],
            "selling_points": [
                {"title": "快速制冷", "description": "30分钟降温"},
                {"title": "节能", "description": "一级能效"},
            ],
            "video_scripts": [],
            "ad_material": {"headline": "限时优惠"},
        }

        result = _summarize_asset_plan(plan)
        assert "主图" in result
        assert "场景图1" in result
        assert "场景图2" in result
        assert "卖点1" in result
        assert "卖点2" in result
        assert "广告" in result

    def test_empty_plan(self):
        from app.services.layout_agent import _summarize_asset_plan
        result = _summarize_asset_plan({})
        assert result == ""


class TestPlatformContext:
    def test_known_platforms(self):
        from app.services.layout_agent import _get_platform_layout_context

        assert "800×800" in _get_platform_layout_context("taobao")
        assert "2000×2000" in _get_platform_layout_context("amazon")
        assert "1080×1440" in _get_platform_layout_context("xiaohongshu")
        assert "1080×1920" in _get_platform_layout_context("douyin")

    def test_unknown_platform(self):
        from app.services.layout_agent import _get_platform_layout_context

        result = _get_platform_layout_context("unknown_platform")
        assert "unknown_platform" in result

    def test_none_platform(self):
        from app.services.layout_agent import _get_platform_layout_context

        result = _get_platform_layout_context(None)
        assert "通用" in result
