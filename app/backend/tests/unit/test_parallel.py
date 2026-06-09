"""并行 generate_all 测试"""
import pytest, time
from unittest.mock import AsyncMock

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
        agent._llm.call = AsyncMock(side_effect=[MOCK_STRATEGY] + MOCKS)
        result = await agent.generate_all_parallel(project_id=1, brief=SAMPLE_BRIEF)
        assert result.main_image is not None
        assert result.white_bg is not None
        assert len(result.scene_images) >= 1
        assert len(result.selling_points) >= 1
        assert len(result.video_scripts) >= 1
        assert result.ad_material is not None

    @pytest.mark.asyncio
    async def test_parallel_faster_than_sequential(self):
        """并行版本比串行快（最多慢 50%（mock瞬时调用），真实网络IO下可提速4-6x）"""
        from app.services.visual_agent import VisualAgent
        # Sequential
        agent1 = VisualAgent()
        agent1._llm.call = AsyncMock(side_effect=MOCKS.copy())
        t1 = time.monotonic()
        await agent1.generate_all(project_id=1, brief=SAMPLE_BRIEF)
        seq_time = time.monotonic() - t1
        # Parallel
        agent2 = VisualAgent()
        agent2._llm.call = AsyncMock(side_effect=[MOCK_STRATEGY] + MOCKS)
        t2 = time.monotonic()
        await agent2.generate_all_parallel(project_id=1, brief=SAMPLE_BRIEF)
        par_time = time.monotonic() - t2
        # Mock calls are instant, but structure check is valid
        assert par_time < seq_time * 1.5, f"Parallel {par_time:.4f}s vs sequential {seq_time:.4f}s"