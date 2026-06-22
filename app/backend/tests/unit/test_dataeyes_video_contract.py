from unittest.mock import AsyncMock

import pytest

from app.models.video_generation_model import VideoGenerationRequest
from app.services.video_generation_service import DataEyesAIVideoProvider, video_generation_service


def test_video_request_accepts_dataeyes_seedance_model():
    req = VideoGenerationRequest(
        provider="dataeyes",
        prompt="five second product reveal",
        duration=5,
        model="doubao-seedance-2-0-v2-250528",
        options={"resolution": "1080p", "ratio": "16:9", "first_frame_url": "/uploads/ref.png"},
    )
    assert req.provider == "dataeyes"
    assert req.model == "doubao-seedance-2-0-v2-250528"


@pytest.mark.asyncio
async def test_dataeyes_video_service_dispatches_request_to_provider(monkeypatch):
    provider = video_generation_service._providers["dataeyes"]
    monkeypatch.setattr(provider, "generate", AsyncMock(return_value={"status": "succeeded", "url": "https://example.test/video.mp4", "task_id": "task-1"}))
    req = VideoGenerationRequest(provider="dataeyes", prompt="seedance product video", duration=5, model="doubao-seedance-2-0-v2-250528")
    result = await video_generation_service.generate(req)
    assert result.provider == "dataeyes"
    assert result.videos[0].url == "https://example.test/video.mp4"
    provider.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_dataeyes_video_provider_maps_seedance_request(monkeypatch):
    provider = DataEyesAIVideoProvider(api_key="test-key", base_url="https://platform.dataeyes.ai")
    posts = []

    class SubmitResp:
        status_code = 200
        def json(self):
            return {"id": "cgt-test"}

    class PollResp:
        status_code = 200
        def json(self):
            return {"status": "succeeded", "content": {"video_url": "https://example.test/seedance.mp4"}}

    class Client:
        async def post(self, path, json):
            posts.append((path, json))
            return SubmitResp()
        async def get(self, path):
            return PollResp()

    async def fake_download(_url, _task_id):
        return "/uploads/generated/seedance.mp4"

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(provider, "_get_client", lambda _auth="Bearer": Client())
    monkeypatch.setattr("app.services.video_generation_service._download_video_to_local", fake_download)
    monkeypatch.setattr("asyncio.sleep", no_sleep)
    req = VideoGenerationRequest(
        provider="dataeyes",
        prompt="seedance prompt",
        duration=5,
        model="doubao-seedance-2-0-v2-250528",
        options={"resolution": "1080p", "ratio": "16:9", "first_frame_url": "/uploads/ref.png"},
    )
    result = await provider.generate(req)
    assert result.provider == "dataeyes"
    assert result.videos[0].url == "/uploads/generated/seedance.mp4"
    path, payload = posts[0]
    assert path == "/seedance/api/v3/contents/generations/tasks"
    assert payload["model"] == "doubao-seedance-2-0-v2-250528"
    assert payload["content"][0] == {"type": "text", "text": "seedance prompt"}
    assert payload["content"][1] == {"type": "image_url", "image_url": {"url": "/uploads/ref.png", "role": "first_frame"}}
    assert payload["duration"] == 5
    assert payload["resolution"] == "1080p"
    assert payload["ratio"] == "16:9"


def test_dataeyes_video_client_disables_environment_proxy(monkeypatch):
    """curl works on ECS; httpx must ignore proxy env to avoid ConnectError."""
    import httpx
    from app.services.video_generation_service import DataEyesAIVideoProvider

    captured = {}

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    provider = DataEyesAIVideoProvider(api_key="test-key", base_url="https://platform.dataeyes.ai")
    provider._get_client("Bearer")

    assert captured["trust_env"] is False
