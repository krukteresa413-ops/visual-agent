"""Tests for storyboard generation service — P2.2 Video Agent Enhancement.

TDD: RED phase — tests written before implementation.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.video_generation_model import VideoGenerationRequest


# ---------------------------------------------------------------------------
# Storyboard data model tests (these should fail until model is defined)
# ---------------------------------------------------------------------------

class TestStoryboardModels:
    """Test the new storyboard data models."""

    def test_storyboard_shot_model_exists(self):
        """StoryboardShot model should be importable from video_generation_model."""
        from app.models.video_generation_model import StoryboardShot
        shot = StoryboardShot(
            shot_number=1,
            description="产品从黑暗中浮现，灯光渐亮",
            camera_angle="close-up",
            duration=3.0,
            transition="fade-in",
            dialogue="全新上市",
            visual_prompt="A sleek product emerging from darkness, dramatic lighting, cinematic, 4K",
        )
        assert shot.shot_number == 1
        assert shot.duration == 3.0
        assert shot.transition == "fade-in"

    def test_storyboard_model_exists(self):
        """Storyboard model should hold a list of shots."""
        from app.models.video_generation_model import Storyboard, StoryboardShot
        shots = [
            StoryboardShot(shot_number=1, description="开场", camera_angle="wide", duration=2.0, visual_prompt="opening shot"),
            StoryboardShot(shot_number=2, description="特写", camera_angle="close-up", duration=3.0, visual_prompt="close-up shot"),
        ]
        sb = Storyboard(title="产品广告", shots=shots, total_duration=5.0)
        assert len(sb.shots) == 2
        assert sb.total_duration == 5.0
        assert sb.title == "产品广告"

    def test_storyboard_shot_defaults(self):
        """StoryboardShot should have sensible defaults for optional fields."""
        from app.models.video_generation_model import StoryboardShot
        shot = StoryboardShot(
            shot_number=1,
            description="简洁镜头",
            visual_prompt="simple shot",
        )
        assert shot.camera_angle == "medium"  # default
        assert shot.duration == 5.0  # default
        assert shot.transition == "cut"  # default
        assert shot.dialogue == ""  # default

    def test_storyboard_serialization(self):
        """Storyboard should serialize to dict for API responses."""
        from app.models.video_generation_model import Storyboard, StoryboardShot
        shot = StoryboardShot(shot_number=1, description="测试", visual_prompt="test prompt")
        sb = Storyboard(title="test", shots=[shot], total_duration=5.0)
        data = sb.model_dump()
        assert data["title"] == "test"
        assert len(data["shots"]) == 1
        assert data["shots"][0]["shot_number"] == 1

    def test_keyframe_model_exists(self):
        """Keyframe model should associate an image URL with a shot."""
        from app.models.video_generation_model import Keyframe
        kf = Keyframe(shot_number=1, image_url="https://example.com/keyframe.png", prompt="test prompt")
        assert kf.shot_number == 1
        assert kf.image_url == "https://example.com/keyframe.png"

    def test_subtitle_model_exists(self):
        """Subtitle model should hold timed text entries."""
        from app.models.video_generation_model import Subtitle, SubtitleEntry
        entries = [
            SubtitleEntry(start_time=0.0, end_time=2.0, text="第一句台词"),
            SubtitleEntry(start_time=2.5, end_time=5.0, text="第二句台词"),
        ]
        sub = Subtitle(language="zh", entries=entries)
        assert len(sub.entries) == 2
        assert sub.language == "zh"
        assert sub.entries[0].start_time == 0.0


# ---------------------------------------------------------------------------
# Storyboard service tests (RED — service does not exist yet)
# ---------------------------------------------------------------------------

class TestStoryboardService:
    """Test the storyboard generation service."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM client that returns structured storyboard JSON."""
        mock = AsyncMock()
        mock.generate.return_value = """```json
{
    "title": "产品发布视频",
    "shots": [
        {
            "shot_number": 1,
            "description": "品牌logo从黑暗中浮现",
            "camera_angle": "close-up",
            "duration": 3.0,
            "transition": "fade-in",
            "dialogue": "",
            "visual_prompt": "Brand logo emerging from darkness, dramatic lighting, cinematic 4K"
        },
        {
            "shot_number": 2,
            "description": "产品旋转展示",
            "camera_angle": "medium",
            "duration": 5.0,
            "transition": "cut",
            "dialogue": "重新定义未来",
            "visual_prompt": "Product rotating on pedestal, studio lighting, clean background"
        },
        {
            "shot_number": 3,
            "description": "使用场景展示",
            "camera_angle": "wide",
            "duration": 4.0,
            "transition": "dissolve",
            "dialogue": "让生活更简单",
            "visual_prompt": "Person using product in modern home, natural lighting, lifestyle"
        }
    ],
    "total_duration": 12.0
}
```"""
        return mock

    @pytest.mark.asyncio
    async def test_generate_storyboard_from_brief(self, mock_llm):
        """Should generate a storyboard from a creative brief using LLM."""
        from app.services.storyboard_service import StoryboardService
        from app.models.video_generation_model import Storyboard

        service = StoryboardService(llm_client=mock_llm)
        brief = "为一个高端智能手表制作15秒产品宣传片"
        result = await service.generate_storyboard(brief)

        assert isinstance(result, Storyboard)
        assert result.title == "产品发布视频"
        assert len(result.shots) == 3
        assert result.total_duration == 12.0
        assert result.shots[0].shot_number == 1
        assert result.shots[0].transition == "fade-in"

    @pytest.mark.asyncio
    async def test_storyboard_handles_llm_error(self, mock_llm):
        """Should raise meaningful error when LLM fails."""
        from app.services.storyboard_service import StoryboardService
        mock_llm.generate.side_effect = Exception("LLM timeout")

        service = StoryboardService(llm_client=mock_llm)
        with pytest.raises(Exception, match="storyboard generation failed|LLM"):
            await service.generate_storyboard("test brief")

    @pytest.mark.asyncio
    async def test_storyboard_min_shots(self):
        """Should require at least 3 shots in a storyboard."""
        from app.services.storyboard_service import StoryboardService
        mock = AsyncMock()
        mock.generate.return_value = """```json
{"title": "too short", "shots": [{"shot_number": 1, "description": "only one", "visual_prompt": "test"}], "total_duration": 5.0}
```"""
        service = StoryboardService(llm_client=mock)
        with pytest.raises(ValueError, match="at least 3"):
            await service.generate_storyboard("test")

    @pytest.mark.asyncio
    async def test_storyboard_handles_null_fields(self):
        """Should handle JSON null values in optional string fields gracefully."""
        from app.services.storyboard_service import StoryboardService
        mock = AsyncMock()
        # Simulate LLM returning null for optional fields
        mock.generate.return_value = """```json
{"title": "null test", "shots": [
    {"shot_number": 1, "description": null, "visual_prompt": null, "camera_angle": null, "transition": null, "dialogue": null, "duration": 3.0},
    {"shot_number": 2, "description": "valid desc", "visual_prompt": "valid prompt", "duration": 3.0},
    {"shot_number": 3, "description": "third", "visual_prompt": "third prompt", "duration": 3.0}
], "total_duration": 9.0}
```"""
        service = StoryboardService(llm_client=mock)
        result = await service.generate_storyboard("null field test")
        assert len(result.shots) == 3
        # Null fields should fall back to defaults
        assert result.shots[0].description == ""
        assert result.shots[0].visual_prompt == ""
        assert result.shots[0].camera_angle == "medium"
        assert result.shots[0].transition == "cut"
        assert result.shots[0].dialogue == ""

    @pytest.mark.asyncio
    async def test_storyboard_rejects_null_shots(self):
        """Should raise ValueError when shots is null, not a list."""
        from app.services.storyboard_service import StoryboardService
        mock = AsyncMock()
        mock.generate.return_value = '{"title": "bad", "shots": null, "total_duration": 0}'
        service = StoryboardService(llm_client=mock)
        with pytest.raises(ValueError, match="shots"):
            await service.generate_storyboard("null shots")


# ---------------------------------------------------------------------------
# Keyframe generation tests (RED — service does not exist yet)
# ---------------------------------------------------------------------------

class TestKeyframeService:
    """Test keyframe generation from storyboard shots."""

    @pytest.fixture
    def mock_image_service(self):
        """Mock image generation service."""
        mock = AsyncMock()
        mock.generate.return_value = type("ImgResult", (), {
            "images": [type("Img", (), {"url": "https://example.com/keyframe_1.png"})()]
        })()
        return mock

    @pytest.fixture
    def sample_storyboard(self):
        from app.models.video_generation_model import Storyboard, StoryboardShot
        shots = [
            StoryboardShot(shot_number=1, description="开场", visual_prompt="opening shot"),
            StoryboardShot(shot_number=2, description="特写", visual_prompt="close-up"),
            StoryboardShot(shot_number=3, description="结束", visual_prompt="ending shot"),
        ]
        return Storyboard(title="test", shots=shots, total_duration=10.0)

    @pytest.mark.asyncio
    async def test_generate_keyframes(self, mock_image_service, sample_storyboard):
        """Should generate one keyframe image per storyboard shot."""
        from app.services.keyframe_service import KeyframeService
        from app.models.video_generation_model import Keyframe

        service = KeyframeService(image_service=mock_image_service)
        keyframes = await service.generate_keyframes(sample_storyboard)

        assert len(keyframes) == 3
        assert all(isinstance(kf, Keyframe) for kf in keyframes)
        assert keyframes[0].shot_number == 1
        assert mock_image_service.generate.call_count == 3

    @pytest.mark.asyncio
    async def test_keyframe_generation_partial_failure(self, mock_image_service, sample_storyboard):
        """Should mark failed keyframes but continue generating others."""
        from app.services.keyframe_service import KeyframeService

        # Shot 2 fails, others succeed
        call_count = [0]
        async def failing_generate(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Image generation failed")
            return type("ImgResult", (), {
                "images": [type("Img", (), {"url": f"https://example.com/kf_{call_count[0]}.png"})()]
            })()

        mock_image_service.generate = failing_generate
        service = KeyframeService(image_service=mock_image_service)

        keyframes = await service.generate_keyframes(sample_storyboard)
        assert len(keyframes) == 3
        assert keyframes[0].image_url != ""  # succeeded
        assert keyframes[1].image_url == ""  # failed, marked empty
        assert keyframes[2].image_url != ""  # succeeded


# ---------------------------------------------------------------------------
# Subtitle service tests (RED — service does not exist yet)
# ---------------------------------------------------------------------------

class TestSubtitleService:
    """Test subtitle generation and SRT formatting."""

    def test_generate_srt_content(self):
        """Should generate valid SRT format from Subtitle model."""
        from app.models.video_generation_model import Subtitle, SubtitleEntry
        from app.services.subtitle_service import SubtitleService

        entries = [
            SubtitleEntry(start_time=0.0, end_time=2.5, text="欢迎来到未来"),
            SubtitleEntry(start_time=3.0, end_time=6.0, text="智能手表，重新定义生活"),
        ]
        sub = Subtitle(language="zh", entries=entries)

        srt = SubtitleService.to_srt(sub)
        assert "00:00:00,000" in srt
        assert "00:00:02,500" in srt
        assert "欢迎来到未来" in srt
        assert "00:00:03,000" in srt
        assert "00:00:06,000" in srt
        assert "智能手表，重新定义生活" in srt

    def test_generate_subtitles_from_dialogue(self):
        """Should generate subtitle entries from storyboard dialogue."""
        from app.services.subtitle_service import SubtitleService
        from app.models.video_generation_model import Storyboard, StoryboardShot

        shots = [
            StoryboardShot(shot_number=1, description="开场", visual_prompt="test", dialogue="第一句话", duration=2.0),
            StoryboardShot(shot_number=2, description="中景", visual_prompt="test", dialogue="", duration=3.0),
            StoryboardShot(shot_number=3, description="特写", visual_prompt="test", dialogue="最后一句", duration=2.0),
        ]
        sb = Storyboard(title="test", shots=shots, total_duration=7.0)

        subtitle = SubtitleService.from_storyboard(sb, language="zh")
        assert len(subtitle.entries) == 2  # only shots with dialogue
        assert subtitle.entries[0].text == "第一句话"
        assert subtitle.entries[1].text == "最后一句"

    def test_srt_time_formatting(self):
        """Should format seconds correctly to SRT timestamp format."""
        from app.services.subtitle_service import SubtitleService
        assert SubtitleService._format_time(0) == "00:00:00,000"
        assert SubtitleService._format_time(1.5) == "00:00:01,500"
        assert SubtitleService._format_time(61.123) == "00:01:01,123"
        assert SubtitleService._format_time(3661.999) == "01:01:01,999"

    def test_subtitle_cumulative_timing(self):
        """Should calculate correct cumulative start times from storyboard."""
        from app.services.subtitle_service import SubtitleService
        from app.models.video_generation_model import Storyboard, StoryboardShot

        shots = [
            StoryboardShot(shot_number=1, description="s1", visual_prompt="v1", dialogue="A", duration=2.0),
            StoryboardShot(shot_number=2, description="s2", visual_prompt="v2", dialogue="", duration=3.0),
            StoryboardShot(shot_number=3, description="s3", visual_prompt="v3", dialogue="B", duration=2.0),
        ]
        sb = Storyboard(title="test", shots=shots, total_duration=7.0)

        subtitle = SubtitleService.from_storyboard(sb, language="zh")
        # Shot 1: 0.0 - 2.0
        assert subtitle.entries[0].start_time == pytest.approx(0.0)
        assert subtitle.entries[0].end_time == pytest.approx(2.0)
        # Shot 3: 5.0 - 7.0 (after shots 1+2 = 2.0+3.0 = 5.0 offset)
        assert subtitle.entries[1].start_time == pytest.approx(5.0)
        assert subtitle.entries[1].end_time == pytest.approx(7.0)
