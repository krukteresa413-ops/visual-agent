"""
测试视觉素材输出 Schema 的数据验证。
每个测试验证：合法数据能通过，非法数据被拒绝。
"""
import pytest
from pydantic import ValidationError


class TestMainImagePlan:
    """PRD 8.3节：主图生成方案"""

    def test_valid_main_image_plan(self):
        from app.schemas.visual_assets import MainImagePlan

        data = {
            "asset_type": "main_image",
            "goal": "突出产品主体和核心卖点",
            "composition": "产品居中，45度角展示",
            "background": "浅灰色渐变背景",
            "lighting": "柔光，金属质感",
            "copywriting": "Fast Cooling for Commercial Use",
            "prompt": "A commercial chest freezer, stainless steel, centered, 45-degree angle, light gray gradient background, soft lighting, product photography, 4K",
            "negative_prompt": "no fake certification logo",
            "platform": "Alibaba.com",
            "status": "draft",
        }
        plan = MainImagePlan(**data)
        assert plan.asset_type == "main_image"
        assert plan.platform == "Alibaba.com"

    def test_main_image_requires_goal(self):
        from app.schemas.visual_assets import MainImagePlan

        with pytest.raises(ValidationError):
            MainImagePlan(
                asset_type="main_image",
                # goal 缺失
                composition="居中",
                background="白底",
                prompt="test",
            )

    def test_main_image_asset_type_must_be_main_image(self):
        from app.schemas.visual_assets import MainImagePlan

        with pytest.raises(ValidationError):
            MainImagePlan(
                asset_type="wrong_type",  # 不允许
                goal="test",
                composition="test",
                background="test",
                prompt="test",
            )


class TestSceneImagePlan:
    """PRD 8.5节：场景图生成方案"""

    def test_valid_scene_image(self):
        from app.schemas.visual_assets import SceneImagePlan

        data = {
            "scene_name": "supermarket",
            "target_user": "supermarket buyer",
            "scene_narrative": "产品放置在超市冷藏区",
            "visual_elements": ["人物", "货架", "产品"],
            "product_position": "前景居中",
            "prompt": "A commercial chest freezer in a modern supermarket...",
        }
        plan = SceneImagePlan(**data)
        assert plan.scene_name == "supermarket"
        assert len(plan.visual_elements) == 3


class TestSellingPointModule:
    """PRD 8.6节：卖点图生成方案"""

    def test_valid_selling_point(self):
        from app.schemas.visual_assets import SellingPointModule

        data = {
            "title": "Fast Cooling Performance",
            "description": "Designed for stable temperature control in commercial use.",
            "visual_representation": "温度曲线、冷气流动、食材保鲜场景",
            "icon_suggestion": "snowflake",
            "layout_suggestion": "左图右文",
        }
        module = SellingPointModule(**data)
        assert module.title == "Fast Cooling Performance"


class TestVideoScript:
    """PRD 8.7节：短视频脚本"""

    def test_valid_15s_script(self):
        from app.schemas.visual_assets import VideoScript

        data = {
            "video_goal": "引流",
            "duration_seconds": 15,
            "storyboard": [
                {
                    "shot_number": 1,
                    "duration": "0-3s",
                    "visual": "产品全景",
                    "subtitle": "Need Reliable Cooling?",
                    "voiceover": "Looking for a commercial freezer you can trust?",
                }
            ],
            "cta": "Learn More",
            "material_requirements": ["产品白底图", "场景图", "Logo"],
            "pacing": "开头钩子 → 卖点展开 → CTA",
        }
        script = VideoScript(**data)
        assert script.duration_seconds == 15
        assert len(script.storyboard) >= 1

    def test_duration_must_be_15_or_30(self):
        from app.schemas.visual_assets import VideoScript

        with pytest.raises(ValidationError):
            VideoScript(
                video_goal="引流",
                duration_seconds=60,  # PRD只要求15和30
                storyboard=[],
                cta="Buy Now",
                material_requirements=[],
                pacing="",
            )


class TestAdMaterialPlan:
    """PRD 8.8节：广告视频素材方案"""

    def test_valid_ad_plan(self):
        from app.schemas.visual_assets import AdMaterialPlan

        data = {
            "ad_goal": "冷启动引流",
            "target_audience": "B2B distributors",
            "ad_angle": "产品性能突出",
            "material_list": ["产品全景图", "工厂实拍", "客户评价"],
            "shot_sequence": ["开头钩子", "卖点1", "卖点2", "CTA"],
            "hook": "Tired of unreliable freezers?",
            "key_selling_points": ["fast cooling", "energy saving"],
            "cta": "Get Quote",
            "platform_suggestion": "Meta Ads",
        }
        plan = AdMaterialPlan(**data)
        assert plan.ad_goal == "冷启动引流"


class TestVisualAssetPlanOut:
    """PRD 5.1节：聚合输出 — 六类素材全部生成"""

    def test_aggregated_output_has_all_six_types(self):
        from app.schemas.visual_assets import VisualAssetPlanOut

        # 这个测试验证PRD成功指标："六类输出覆盖率 100%"
        plan = VisualAssetPlanOut(
            project_id=1,
            main_image={"asset_type": "main_image", "goal": "t", "composition": "t", "background": "t", "prompt": "t"},
            white_bg={"asset_type": "white_bg", "goal": "t", "instructions": "t"},
            scene_images=[{"scene_name": "s", "target_user": "u", "scene_narrative": "n", "visual_elements": [], "product_position": "p", "prompt": "p"}],
            selling_points=[{"title": "t", "description": "d", "visual_representation": "v", "icon_suggestion": "i", "layout_suggestion": "l"}],
            video_scripts=[{"video_goal": "g", "duration_seconds": 15, "storyboard": [], "cta": "c", "material_requirements": [], "pacing": "p"}],
            ad_material={"ad_goal": "g", "target_audience": "a", "ad_angle": "a", "material_list": [], "shot_sequence": [], "hook": "h", "key_selling_points": [], "cta": "c", "platform_suggestion": "p"},
        )
        assert plan.main_image is not None
        assert plan.white_bg is not None
        assert len(plan.scene_images) >= 1
        assert len(plan.selling_points) >= 1
        assert len(plan.video_scripts) >= 1
        assert plan.ad_material is not None
