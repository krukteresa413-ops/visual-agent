"""并行 generate_all 测试"""
import pytest, time
from unittest.mock import AsyncMock, patch

MOCK_STRATEGY = {
    "visual_positioning":"定位","visual_style":"风格",
    "selling_points_priority":[{"rank":1,"point":"x","rationale":"测试"}],
    "asset_plan_summary":{"main_image":"方向","white_bg":"方向","scene_images":"方向","selling_points":"方向","video_scripts":"方向","ad_material":"方向"},
    "brand_tone":"tone","audience_type":"B2B","key_differentiators":"差异化",
}

SAMPLE_BRIEF = {
    "product_name":"Test","category":"Test","specifications":["x"],
    "selling_points":["x"],"target_market":["x"],"usage_scenarios":["x"],
}

MOCKS = [
    {"asset_type":"main_image","goal":"m","composition":"c","background":"b","prompt":"p"},
    {"asset_type":"white_bg","goal":"m","instructions":"i"},
    [{"scene_name":"s","target_user":"u","scene_narrative":"n","visual_elements":[],"product_position":"p","prompt":"p"}],
    [{"title":"t","description":"d","visual_representation":"v","icon_suggestion":"i","layout_suggestion":"l"}],
    [{"video_goal":"v","duration_seconds":15,"storyboard":[],"cta":"c","material_requirements":[],"pacing":"p"}],
    {"ad_goal":"a","target_audience":"a","ad_angle":"a","material_list":[],"shot_sequence":[],"hook":"h","key_selling_points":[],"cta":"c","platform_suggestion":"p"},
]

class TestParallelGeneration:
    @pytest.mark.asyncio
    async def test_parallel_same_result_as_sequential(self):
        """并行结果与串行一致"""
        from app.services.visual_agent import VisualAgent
        agent = VisualAgent()
        agent._llm.call = AsyncMock(side_effect=MOCKS.copy())
        with patch("app.services.visual_agent.VisualAgent.generate_images_from_plan", new_callable=AsyncMock) as mock_render, \
             patch("app.services.layout_agent.LayoutAgent.generate_layout", new_callable=AsyncMock) as mock_layout:
            mock_render.return_value = {"main_image": None, "white_bg": None, "scene_images": []}
            mock_layout.side_effect = Exception("layout skipped in unit test")
            result = await agent.generate_all(project_id=1, brief=SAMPLE_BRIEF)
        assert result.main_image is not None
        assert result.white_bg is not None
        assert len(result.scene_images) >= 1
        assert len(result.selling_points) >= 1
        assert len(result.video_scripts) >= 1
        assert result.ad_material is not None

    @pytest.mark.asyncio
    async def test_parallel_generation_finishes_near_single_task_latency(self):
        """Six 50ms independent tasks should complete near one task latency, not six."""
        import asyncio
        from app.schemas.visual_assets import (
            MainImagePlan,
            WhiteBgPlan,
            SceneImagePlan,
            SellingPointModule,
            VideoScript,
            AdMaterialPlan,
        )
        from app.services.visual_agent import VisualAgent

        agent = VisualAgent()

        async def delayed(value):
            await asyncio.sleep(0.05)
            return value

        agent.generate_main_image = lambda *a, **k: delayed(MainImagePlan(**MOCKS[0]))
        agent.generate_white_bg = lambda *a, **k: delayed(WhiteBgPlan(**MOCKS[1]))
        agent.generate_scene_images = lambda *a, **k: delayed([SceneImagePlan(**MOCKS[2][0])])
        agent.generate_selling_points = lambda *a, **k: delayed([SellingPointModule(**MOCKS[3][0])])
        agent.generate_video_scripts = lambda *a, **k: delayed([VideoScript(**MOCKS[4][0])])
        agent.generate_ad_material = lambda *a, **k: delayed(AdMaterialPlan(**MOCKS[5]))

        t0 = time.monotonic()
        with patch("app.services.visual_agent.VisualAgent.generate_images_from_plan", new_callable=AsyncMock) as mock_render,              patch("app.services.layout_agent.LayoutAgent.generate_layout", new_callable=AsyncMock) as mock_layout:
            mock_render.return_value = {"main_image": None, "white_bg": None, "scene_images": []}
            mock_layout.side_effect = Exception("layout skipped in unit test")
            await agent.generate_all(project_id=1, brief=SAMPLE_BRIEF)
        elapsed = time.monotonic() - t0

        assert elapsed < 0.16

    @pytest.mark.asyncio
    async def test_generate_all_starts_plan_tasks_concurrently(self):
        """Six independent plan tasks should start in the same scheduling window."""
        import asyncio
        from app.schemas.visual_assets import (
            MainImagePlan,
            WhiteBgPlan,
            SceneImagePlan,
            SellingPointModule,
            VideoScript,
            AdMaterialPlan,
        )
        from app.services.visual_agent import VisualAgent

        agent = VisualAgent()
        starts = []

        async def delayed(label, value):
            starts.append((label, time.monotonic()))
            await asyncio.sleep(0.05)
            return value

        agent.generate_main_image = lambda *a, **k: delayed("main", MainImagePlan(**MOCKS[0]))
        agent.generate_white_bg = lambda *a, **k: delayed("white", WhiteBgPlan(**MOCKS[1]))
        agent.generate_scene_images = lambda *a, **k: delayed("scene", [SceneImagePlan(**MOCKS[2][0])])
        agent.generate_selling_points = lambda *a, **k: delayed("selling", [SellingPointModule(**MOCKS[3][0])])
        agent.generate_video_scripts = lambda *a, **k: delayed("video", [VideoScript(**MOCKS[4][0])])
        agent.generate_ad_material = lambda *a, **k: delayed("ad", AdMaterialPlan(**MOCKS[5]))

        with patch("app.services.visual_agent.VisualAgent.generate_images_from_plan", new_callable=AsyncMock) as mock_render, \
             patch("app.services.layout_agent.LayoutAgent.generate_layout", new_callable=AsyncMock) as mock_layout:
            mock_render.return_value = {"main_image": None, "white_bg": None, "scene_images": []}
            mock_layout.side_effect = Exception("layout skipped in unit test")
            await agent.generate_all(project_id=1, brief=SAMPLE_BRIEF)

        assert len(starts) == 6
        first = min(ts for _, ts in starts)
        last = max(ts for _, ts in starts)
        assert last - first < 0.03

    @pytest.mark.asyncio
    async def test_configured_generate_asset_entrypoint(self):
        """One configured helper should drive individual asset generation."""
        from app.services.visual_agent import VisualAgent
        from app.schemas.visual_assets import MainImagePlan

        agent = VisualAgent()
        agent._llm.call = AsyncMock(return_value=MOCKS[0])

        result = await agent._generate_asset("main_image", SAMPLE_BRIEF)

        assert isinstance(result, MainImagePlan)
        assert agent._llm.call.await_count == 1
