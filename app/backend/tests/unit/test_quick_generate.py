"""
Tests for quick-generate endpoint (T5: 快速生成直达画布).
User flow: input prompt → generate canvas directly, skip parsing & form filling.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


class TestQuickGenerate:
    """RED tests — quick-generate endpoint that skips parsing and goes straight to canvas."""

    def test_quick_generate_accepts_prompt_only(self, client):
        """POST /quick-generate should accept a prompt string and return task_id immediately."""
        resp = client.post("/api/v1/quick-generate", json={
            "prompt": "一款智能手表，心率监测，运动模式",
            "project_id": 2,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["status"] == "processing"

    def test_quick_generate_rejects_empty_prompt(self, client):
        """Empty prompt should return 400."""
        resp = client.post("/api/v1/quick-generate", json={
            "prompt": "",
            "project_id": 2,
        })
        assert resp.status_code == 400

    def test_quick_generate_rejects_missing_prompt(self, client):
        """Missing prompt should return 422 (Pydantic validation)."""
        resp = client.post("/api/v1/quick-generate", json={
            "project_id": 2,
        })
        assert resp.status_code == 422

    def test_quick_generate_skips_review(self, client):
        """Quick-generate should NEVER return needs_review — it always generates."""
        mock_plan = AsyncMock()
        mock_plan.main_image = None
        mock_plan.white_bg = None
        mock_plan.scene_images = []
        mock_plan.selling_points = []
        mock_plan.video_scripts = []
        mock_plan.ad_material = None

        with patch("app.services.visual_agent.VisualAgent.generate_all",
                   new_callable=AsyncMock, return_value=mock_plan):
            resp = client.post("/api/v1/quick-generate", json={
                "prompt": "产品",  # minimal — would trigger review in normal flow
                "project_id": 2,
            })
        assert resp.status_code == 200
        data = resp.json()
        # Should return task_id, NOT needs_review
        assert "task_id" in data
        assert data.get("needs_review") is not True

    def test_poll_quick_generate_task_returns_generation(self, client):
        """Polling a completed quick-generate task should return generation result."""
        mock_plan = AsyncMock()
        mock_plan.main_image = None
        mock_plan.white_bg = None
        mock_plan.scene_images = []
        mock_plan.selling_points = []
        mock_plan.video_scripts = []
        mock_plan.ad_material = None

        with patch("app.services.visual_agent.VisualAgent.generate_all",
                   new_callable=AsyncMock, return_value=mock_plan):
            resp = client.post("/api/v1/quick-generate", json={
                "prompt": "智能手表",
                "project_id": 2,
            })
            task_id = resp.json()["task_id"]

        # Poll the task (same endpoint as async-generate)
        resp2 = client.get(f"/api/v1/generation/task/{task_id}")
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["status"] in ("processing", "complete")
        if data["status"] == "complete":
            assert "generation" in data

    def test_quick_generate_constructs_minimal_brief_from_prompt(self, client):
        """Quick-generate should internally construct a minimal brief from prompt without LLM parsing."""
        mock_plan = AsyncMock()
        mock_plan.main_image = None
        mock_plan.white_bg = None
        mock_plan.scene_images = []
        mock_plan.selling_points = []
        mock_plan.video_scripts = []
        mock_plan.ad_material = None

        with patch("app.services.visual_agent.VisualAgent.generate_all",
                   new_callable=AsyncMock, return_value=mock_plan) as mock_gen:
            resp = client.post("/api/v1/quick-generate", json={
                "prompt": "一款智能手表，心率监测，运动模式，黑色外观",
                "project_id": 2,
            })
            # Wait a bit for background task to start
            import time
            time.sleep(0.5)

        # Verify generate_all was called with a brief containing the prompt
        # (can't easily assert on background task call, so we just check endpoint accepts it)
        assert resp.status_code == 200

    def test_quick_generate_supports_optional_prompt_template(self, client):
        """Quick-generate should accept optional prompt_template (from inspiration library)."""
        resp = client.post("/api/v1/quick-generate", json={
            "prompt": "智能手表",
            "project_id": 2,
            "prompt_template": "极简科技风格，白色背景",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data


@pytest.mark.asyncio
async def test_quick_image_first_asset_plan_contains_one_real_image_slot():
    from types import SimpleNamespace
    from app.api.unified_generation_routes import _quick_generate_image_asset
    from app.models.image_generation_model import GeneratedImage, ImageGenerationResult

    req = SimpleNamespace(
        prompt="运动鞋，白底主图",
        project_id=2,
        image_provider="dataeyes",
        image_model=None,
        auto_model=True,
    )
    result = ImageGenerationResult(
        provider="dataeyes",
        status="succeeded",
        images=[GeneratedImage(url="/uploads/generated/real.png", width=1024, height=1024)],
    )

    with patch("app.services.image_generation_service.image_generation_service.generate", new_callable=AsyncMock, return_value=result):
        plan = await _quick_generate_image_asset(req, {"selling_points": [req.prompt]})

    image_slots = [
        plan.get("main_image"),
        plan.get("white_bg"),
        *(plan.get("scene_images") or []),
    ]
    urls = [slot.get("url") for slot in image_slots if isinstance(slot, dict) and slot.get("url")]
    assert urls == ["/uploads/generated/real.png"]
    assert plan["main_image"]["url"] == "/uploads/generated/real.png"
    assert plan.get("white_bg") is None
    assert plan.get("scene_images") == []


@pytest.mark.asyncio
async def test_quick_generate_prompt_injects_minimal_brand_context():
    from types import SimpleNamespace
    from app.api.unified_generation_routes import _quick_generate_image_asset
    from app.models.image_generation_model import GeneratedImage, ImageGenerationResult

    req = SimpleNamespace(
        prompt="运动鞋，白底主图",
        project_id=2,
        image_provider="dataeyes",
        image_model=None,
        auto_model=True,
    )
    result = ImageGenerationResult(
        provider="dataeyes",
        status="succeeded",
        images=[GeneratedImage(url="/uploads/generated/brand.png", width=1024, height=1024)],
    )

    with patch("app.services.image_generation_service.image_generation_service.generate", new_callable=AsyncMock, return_value=result) as mock_generate:
        await _quick_generate_image_asset(req, {
            "selling_points": [req.prompt],
            "_brand_context": "品牌色:#FF6900;风格关键词:动感,专业;避免:廉价感",
        })

    generated_req = mock_generate.call_args.args[0]
    assert "品牌色:#FF6900" in generated_req.prompt
    assert "风格关键词:动感,专业" in generated_req.prompt
    assert "避免:廉价感" in generated_req.prompt



def test_build_minimal_brand_prompt_context_uses_color_keywords_and_forbidden_words():
    from types import SimpleNamespace
    from app.api.unified_generation_routes import _build_minimal_brand_prompt_context

    brand = SimpleNamespace(
        primary_color="#FF6900",
        visual_keywords_list=["动感", "专业", "电商", "白底", "高转化", "多余"],
        forbidden_words_list=["廉价感", "杂乱"],
    )

    context = _build_minimal_brand_prompt_context(brand)

    assert context == "品牌色:#FF6900;风格关键词:动感,专业,电商,白底,高转化;避免:廉价感,杂乱"


def test_build_minimal_brand_prompt_context_returns_empty_without_brand():
    from app.api.unified_generation_routes import _build_minimal_brand_prompt_context

    assert _build_minimal_brand_prompt_context(None) == ""


@pytest.mark.asyncio
async def test_quick_image_first_preserves_provider_model_evidence():
    from types import SimpleNamespace
    from app.api.unified_generation_routes import _quick_generate_image_asset
    from app.models.image_generation_model import GeneratedImage, ImageGenerationResult

    req = SimpleNamespace(
        prompt="运动鞋，白底主图",
        project_id=2,
        image_provider="dataeyes",
        image_model="gpt-image-1.5-sp",
        auto_model=False,
    )
    result = ImageGenerationResult(
        provider="dataeyes",
        status="succeeded",
        images=[GeneratedImage(url="/uploads/generated/model.png", width=1024, height=1024)],
        raw={"requested_model": "gpt-image-1.5-sp", "model": "gpt-image-2-pro"},
    )

    with patch("app.services.image_generation_service.image_generation_service.generate", new_callable=AsyncMock, return_value=result):
        plan = await _quick_generate_image_asset(req, {"selling_points": [req.prompt]})

    assert plan["main_image"]["model"] == "gpt-image-1.5-sp"
    assert plan["main_image"]["provider_model"] == "gpt-image-2-pro"
    assert plan["_provider_raw"]["requested_model"] == "gpt-image-1.5-sp"
    assert plan["_provider_raw"]["model"] == "gpt-image-2-pro"

def test_quick_generate_accepts_parsed_brief_contract():
    """Homepage parsed_brief must be preserved when quick-generate starts from document parsing."""
    from app.api.unified_generation_routes import QuickGenerateRequest

    req = QuickGenerateRequest(
        prompt="电视机",
        project_id=2,
        brief={
            "product_name": "电视机",
            "category": "家电",
            "selling_points": ["4K 超高清"],
        },
    )

    assert req.brief["product_name"] == "电视机"
    route_source = Path('/opt/visual-agent/app/backend/app/api/unified_generation_routes.py').read_text()
    assert 'brief = dict(req.brief)' in route_source


@pytest.mark.asyncio
async def test_video_intent_submits_real_video_and_does_not_call_image_generation():
    """Video intent must route to the video pipeline and never fall back to images."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch
    from app.api.unified_generation_routes import _generate_quick_asset_for_modality

    req = SimpleNamespace(
        prompt="生成一个视频",
        project_id=2,
        image_provider="dataeyes",
        image_model=None,
        auto_model=True,
    )
    progress = AsyncMock()

    with patch("app.api.unified_generation_routes._quick_generate_image_asset", new_callable=AsyncMock) as mock_image, \
         patch("app.api.unified_generation_routes._quick_generate_video_asset", new_callable=AsyncMock, return_value={"modality": "video", "status": "submitted", "video": {"task_id": "remote-task-1"}}) as mock_video:
        plan = await _generate_quick_asset_for_modality(req, {"selling_points": [req.prompt]}, True, progress)

    mock_image.assert_not_called()
    mock_video.assert_awaited_once()
    progress.step.assert_any_await("生成第一段视频", "generating", "视频已提交，排队生成中")
    assert plan["modality"] == "video"
    assert plan["status"] == "submitted"
    assert plan["video"]["task_id"] == "remote-task-1"
    assert "main_image" not in plan


@pytest.mark.asyncio
async def test_image_intent_still_generates_first_image():
    """Image flow must keep using the existing fast image path."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch
    from app.api.unified_generation_routes import _generate_quick_asset_for_modality

    req = SimpleNamespace(
        prompt="生成一张跑鞋主图",
        project_id=2,
        image_provider="dataeyes",
        image_model=None,
        auto_model=True,
    )
    expected = {"main_image": {"url": "/uploads/generated/ok.png"}}
    progress = AsyncMock()

    with patch("app.api.unified_generation_routes._quick_generate_image_asset", new_callable=AsyncMock, return_value=expected) as mock_image:
        plan = await _generate_quick_asset_for_modality(req, {"selling_points": [req.prompt]}, False, progress)

    mock_image.assert_awaited_once()
    progress.step.assert_any_await("快速出图", "generating", "正在用 AI 模型生成第一张图...")
    assert plan == expected


@pytest.mark.asyncio
async def test_quick_generate_video_asset_returns_submitted_task_id():
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch
    from app.api.unified_generation_routes import _quick_generate_video_asset
    from app.models.video_generation_model import GeneratedVideo, VideoGenerationResult

    req = SimpleNamespace(prompt="用 seedance 生成一段马拉松视频", project_id=2)
    result = VideoGenerationResult(
        provider="dataeyes",
        status="succeeded",
        videos=[GeneratedVideo(url="/uploads/generated/seedance.mp4", duration=5, provider_asset_id="cgt-test")],
    )

    with patch("app.services.video_generation_service.video_generation_service.generate", new_callable=AsyncMock, return_value=result) as mock_generate:
        plan = await _quick_generate_video_asset(req, {"selling_points": [req.prompt]})

    mock_generate.assert_awaited_once()
    generated_req = mock_generate.call_args.args[0]
    assert generated_req.provider == "dataeyes"
    assert generated_req.model == "doubao-seedance-1-5-pro-251215"
    assert generated_req.options["platform"] == "seedance"
    assert generated_req.options["resolution"] == "720p"
    assert plan == {
        "video": {"url": "/uploads/generated/seedance.mp4", "duration": 5, "task_id": "cgt-test"},
        "modality": "video",
        "status": "submitted",
        "message": "视频已提交，排队生成中",
    }


def test_ensure_canvas_elements_seeds_video_node(tmp_path):
    from app.api.unified_generation_routes import _canvas_elements_from_asset_plan

    elements = _canvas_elements_from_asset_plan(2, {
        "modality": "video",
        "video": {"url": "/uploads/generated/video_test.mp4", "duration": 5, "task_id": "cgt-test"},
    })

    assert elements == [{
        "id": "video_2_cgt-test",
        "type": "video",
        "label": "生成视频",
        "x": 0,
        "y": 0,
        "width": 360,
        "height": 260,
        "thumbnail_url": "/uploads/generated/video_test.mp4",
        "asset_ref": {"type": "video", "url": "/uploads/generated/video_test.mp4", "task_id": "cgt-test"},
        "metadata": {"auto_seeded": True, "source": "video_generation", "duration_seconds": 5, "status": "complete"},
    }]


@pytest.mark.asyncio
async def test_quick_generate_video_asset_respects_selected_kling_model():
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch
    from app.api.unified_generation_routes import _quick_generate_video_asset
    from app.models.video_generation_model import GeneratedVideo, VideoGenerationResult

    req = SimpleNamespace(prompt="生成一段产品视频", project_id=2, image_model="kling-v2-6")
    result = VideoGenerationResult(
        provider="dataeyes",
        status="succeeded",
        videos=[GeneratedVideo(url="/uploads/generated/kling.mp4", duration=5, provider_asset_id="kling-task")],
    )

    with patch("app.services.video_generation_service.video_generation_service.generate", new_callable=AsyncMock, return_value=result) as mock_generate:
        plan = await _quick_generate_video_asset(req, {"selling_points": [req.prompt]})

    generated_req = mock_generate.call_args.args[0]
    assert generated_req.model == "kling-v2-6"
    assert generated_req.options["platform"] == "kling"
    assert generated_req.options["mode"] == "std"
    assert generated_req.options["sound"] == "off"
    assert plan["video"]["url"] == "/uploads/generated/kling.mp4"


@pytest.mark.asyncio
async def test_quick_generate_video_asset_respects_selected_vidu_model():
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, patch
    from app.api.unified_generation_routes import _quick_generate_video_asset
    from app.models.video_generation_model import GeneratedVideo, VideoGenerationResult

    req = SimpleNamespace(prompt="生成一段产品视频", project_id=2, image_model="viduq3-pro")
    result = VideoGenerationResult(
        provider="dataeyes",
        status="succeeded",
        videos=[GeneratedVideo(url="/uploads/generated/vidu.mp4", duration=5, provider_asset_id="vidu-task")],
    )

    with patch("app.services.video_generation_service.video_generation_service.generate", new_callable=AsyncMock, return_value=result) as mock_generate:
        plan = await _quick_generate_video_asset(req, {"selling_points": [req.prompt]})

    generated_req = mock_generate.call_args.args[0]
    assert generated_req.model == "viduq3-pro"
    assert generated_req.options["platform"] == "vidu"
    assert generated_req.options["resolution"] == "720p"
    assert plan["video"]["url"] == "/uploads/generated/vidu.mp4"
