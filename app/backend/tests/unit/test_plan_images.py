"""generate_images_from_plan 批量生图测试 — TDD RED"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.schemas.visual_assets import (
    MainImagePlan,
    SceneImagePlan,
    VisualAssetPlanOut,
    WhiteBgPlan,
    AdMaterialPlan,
)
from app.models.image_generation_model import GeneratedImage, ImageGenerationResult


def make_mock_plan():
    """构造一个含 prompt 的 mock plan。"""
    return VisualAssetPlanOut(
        project_id=2,
        main_image=MainImagePlan(
            asset_type="main_image",
            goal="转化",
            composition="45度角",
            background="纯白",
            prompt="A commercial freezer, 45 degree angle, white background, product photography",
        ),
        white_bg=WhiteBgPlan(goal="test", instructions="test"),
        scene_images=[
            SceneImagePlan(
                scene_name="超市场景",
                target_user="采购商",
                scene_narrative="超市冷柜区",
                visual_elements=["freezer", "shopper"],
                product_position="center",
                prompt="Commercial freezer in supermarket aisle, bright lighting",
            ),
            SceneImagePlan(
                scene_name="餐厅场景",
                target_user="餐厅老板",
                scene_narrative="后厨",
                visual_elements=["freezer", "chef"],
                product_position="right",
                prompt="Commercial freezer in restaurant kitchen, chef reaching in",
            ),
        ],
        selling_points=[],
        video_scripts=[],
        ad_material=AdMaterialPlan(
            ad_goal="test", target_audience="test", ad_angle="test",
            material_list=[], shot_sequence=[], hook="test", key_selling_points=[],
            cta="test", platform_suggestion="test",
        ),
    )


class TestGenerateImagesFromPlan:
    """测试从 VisualAssetPlan 批量生成图片。"""

    @patch("app.services.image_generation_service.image_generation_service.generate")
    async def test_generates_main_image_and_scenes(self, mock_gen):
        from app.services.visual_agent import VisualAgent

        mock_gen.return_value = ImageGenerationResult(
            provider="dalle",
            status="succeeded",
            images=[GeneratedImage(url="https://example.com/img.png", width=1024, height=1024)],
        )

        agent = VisualAgent()
        plan = make_mock_plan()
        result = await agent.generate_images_from_plan(plan, provider="dalle")

        assert result["main_image"] is not None
        assert result["main_image"]["url"] == "https://example.com/img.png"
        assert len(result["scene_images"]) == 2
        assert mock_gen.call_count == 3

    @patch("app.services.image_generation_service.image_generation_service.generate")
    async def test_handles_no_scene_images(self, mock_gen):
        from app.services.visual_agent import VisualAgent

        mock_gen.return_value = ImageGenerationResult(
            provider="dalle",
            status="succeeded",
            images=[GeneratedImage(url="https://example.com/main.png")],
        )

        agent = VisualAgent()
        plan = make_mock_plan()
        plan.scene_images = []
        result = await agent.generate_images_from_plan(plan, provider="dalle")

        assert result["main_image"] is not None
        assert result["scene_images"] == []
        assert mock_gen.call_count == 1

    @patch("app.services.image_generation_service.image_generation_service.generate")
    async def test_partial_failure_still_returns_partial(self, mock_gen):
        from app.services.visual_agent import VisualAgent

        call_count = [0]

        async def flaky_gen(request):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("API error")
            return ImageGenerationResult(
                provider="dalle",
                status="succeeded",
                images=[GeneratedImage(url=f"https://example.com/{call_count[0]}.png")],
            )

        mock_gen.side_effect = flaky_gen

        agent = VisualAgent()
        plan = make_mock_plan()
        result = await agent.generate_images_from_plan(plan, provider="dalle")

        assert result["main_image"] is not None
        assert len(result["scene_images"]) == 2
        assert result["scene_images"][0] is None
        assert result["scene_images"][1] is not None
