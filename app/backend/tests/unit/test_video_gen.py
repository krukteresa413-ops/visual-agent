"""视频生成 Provider + 批量生视频测试 — TDD RED"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.video_generation_model import (
    GeneratedVideo,
    VideoGenerationRequest,
    VideoGenerationResult,
    VideoProviderKind,
)


class TestVideoProviders:
    """测试多种视频 Provider 注册和预留。"""

    def test_provider_kinds_reserved(self):
        """验证预留的 provider 种类充足。"""
        # runway, pika, kling 已存在; 扩展预留 sora, luma, hailuo
        kinds = VideoProviderKind.__args__  # type: ignore
        assert "local" in kinds
        assert "runway" in kinds
        assert "pika" in kinds
        assert "kling" in kinds

    def test_new_provider_registered(self):
        """新增 Runway provider 可注册并列出。"""
        from app.services.video_generation_service import (
            VideoGenerationService,
            RunwayVideoProvider,
        )
        service = VideoGenerationService()
        service.register(RunwayVideoProvider())
        names = [p["name"] for p in service.list_providers()]
        assert "runway" in names

    @patch("httpx.AsyncClient.post")
    async def test_runway_generate_calls_api(self, mock_post):
        """Runway provider 调用正确的 API 端点。"""
        from app.services.video_generation_service import RunwayVideoProvider

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "vid-123", "status": "processing"}
        mock_post.return_value = mock_response

        provider = RunwayVideoProvider(api_key="test-key")
        request = VideoGenerationRequest(
            provider="runway",
            prompt="A commercial freezer rotating on white background",
            duration=10,
        )
        result = await provider.generate(request)

        assert result.provider == "runway"
        assert result.status == "succeeded"
        assert len(result.videos) == 1

    @patch("httpx.AsyncClient.post")
    async def test_pika_generate_calls_api(self, mock_post):
        """Pika provider 调用正确的 API 端点。"""
        from app.services.video_generation_service import PikaVideoProvider

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "pika-456", "video_url": "https://cdn.pika.art/vid.mp4"}
        mock_post.return_value = mock_response

        provider = PikaVideoProvider(api_key="test-pika-key")
        request = VideoGenerationRequest(provider="pika", prompt="test video", duration=5)
        result = await provider.generate(request)

        assert result.provider == "pika"
        assert result.status == "succeeded"


class TestGenerateVideosFromPlan:
    """测试从 VisualAssetPlan 批量生成视频。"""

    def _make_plan(self):
        from app.schemas.visual_assets import (
            MainImagePlan, WhiteBgPlan, AdMaterialPlan,
            SceneImagePlan, VideoScript, VisualAssetPlanOut,
        )
        return VisualAssetPlanOut(
            project_id=2,
            main_image=MainImagePlan(asset_type="main_image", goal="t", composition="t", background="t", prompt="t"),
            white_bg=WhiteBgPlan(goal="t", instructions="t"),
            scene_images=[SceneImagePlan(scene_name="s1", target_user="u", scene_narrative="n", visual_elements=["v"], product_position="c", prompt="p")],
            selling_points=[],
            video_scripts=[
                VideoScript(duration_seconds=15, video_goal="产品展示", pacing="中速", storyboard=[], material_requirements=[], cta="立即购买"),
                VideoScript(duration_seconds=30, video_goal="品牌故事", pacing="慢速", storyboard=[], material_requirements=[], cta="了解更多"),
            ],
            ad_material=AdMaterialPlan(ad_goal="t", target_audience="t", ad_angle="t", material_list=[], shot_sequence=[], hook="t", key_selling_points=[], cta="t", platform_suggestion="t"),
        )

    @patch("app.services.video_generation_service.video_generation_service.generate")
    async def test_generates_videos_from_scripts(self, mock_gen):
        """应从 video_scripts 生成对应视频。"""
        from app.services.visual_agent import VisualAgent

        mock_gen.return_value = VideoGenerationResult(
            provider="runway",
            status="succeeded",
            videos=[GeneratedVideo(url="https://example.com/vid.mp4", duration=15)],
        )

        agent = VisualAgent()
        plan = self._make_plan()
        result = await agent.generate_videos_from_plan(plan, provider="runway")

        assert len(result) == 2
        assert result[0] is not None
        assert result[0]["url"] == "https://example.com/vid.mp4"
        assert mock_gen.call_count == 2

    @patch("app.services.video_generation_service.video_generation_service.generate")
    async def test_partial_failure_ok(self, mock_gen):
        """部分失败不影响其他。"""
        from app.services.visual_agent import VisualAgent

        call_count = [0]

        async def flaky(req):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("API error")
            return VideoGenerationResult(
                provider="runway", status="succeeded",
                videos=[GeneratedVideo(url=f"https://ex.com/v{call_count[0]}.mp4")],
            )

        mock_gen.side_effect = flaky

        agent = VisualAgent()
        plan = self._make_plan()
        result = await agent.generate_videos_from_plan(plan, provider="runway")

        assert len(result) == 2
        assert result[0] is None  # failed
        assert result[1] is not None  # succeeded
