"""Contract tests for six-vendor video adapters (P2-11).

Verifies per-vendor adapter configuration and mock-backed generation flow.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.services.video_generation_service import (
    DataEyesAIVideoProvider,
    VideoGenerationRequest,
)


@pytest.fixture(autouse=True)
def mock_video_download(monkeypatch):
    async def fake_download(_url, task_id, **_kw):  # O1: 接受 tenant_id/project_id kwargs
        return f"/uploads/generated/{task_id}.mp4"
    monkeypatch.setattr("app.services.video_generation_service._download_video_to_local", fake_download)


def mock_resp(status=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data or {}
    resp.text = text
    return resp


def setup_mock_client(provider, submit_resp, poll_resp):
    """Helper: mock provider._get_client to return a mock httpx client."""
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=submit_resp)
    mock_client.get = AsyncMock(return_value=poll_resp)
    provider._get_client = MagicMock(return_value=mock_client)
    return mock_client


# ── Seedance ──

class TestSeedanceAdapter:
    @pytest.mark.asyncio
    async def test_submits_to_correct_endpoint(self, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", AsyncMock())
        provider = DataEyesAIVideoProvider(api_key="test", base_url="https://platform.dataeyes.ai")
        submit = mock_resp(200, {"id": "cgt-test123"})
        poll = mock_resp(200, {"id": "cgt-test123", "status": "succeeded", "content": {"video_url": "https://cdn.example.com/v.mp4"}})
        mock = setup_mock_client(provider, submit, poll)

        req = VideoGenerationRequest(prompt="a running horse", model="doubao-seedance-2-0-v2-250528", duration=5)
        result = await provider.generate(req)

        call = mock.post.call_args[0]
        assert "/seedance/api/v3/contents/generations/tasks" in str(call)
        assert result.status == "succeeded"
        assert result.videos[0].url == "/uploads/generated/cgt-test123.mp4"


# ── Kling ──

class TestKlingAdapter:
    @pytest.mark.asyncio
    async def test_submits_to_correct_endpoint(self, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", AsyncMock())
        provider = DataEyesAIVideoProvider(api_key="test", base_url="https://platform.dataeyes.ai")
        submit = mock_resp(200, {"code": 0, "data": {"task_id": "kling-123", "task_status": "submitted"}})
        poll = mock_resp(200, {"code": 0, "data": {"task_id": "kling-123", "task_status": "succeed", "task_result": {"videos": [{"url": "https://kling-cdn.com/v.mp4"}]}}})
        mock = setup_mock_client(provider, submit, poll)

        req = VideoGenerationRequest(prompt="a cat", model="kling-v2-6", duration=5, options={"mode": "pro"})
        result = await provider.generate(req)

        call = mock.post.call_args[0]
        assert "/kling/v1/videos/text2video" in str(call)
        assert result.status == "succeeded"
        assert result.videos[0].url == "/uploads/generated/kling-123.mp4"


# ── Hailuo (two-step) ──

class TestHailuoAdapter:
    @pytest.mark.asyncio
    async def test_two_step_polling(self, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", AsyncMock())
        provider = DataEyesAIVideoProvider(api_key="test", base_url="https://platform.dataeyes.ai")
        submit = mock_resp(200, {"task_id": "hl-123", "base_resp": {"status_code": 0}})
        status_poll = mock_resp(200, {"task_id": "hl-123", "status": "completed", "file_id": "file-456"})
        download_poll = mock_resp(200, {"file_id": "file-456", "download_url": "https://hailuo-cdn.com/v.mp4"})

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=status_poll)
        mock_client.post = AsyncMock()
        mock_client.post.side_effect = [submit, download_poll]
        provider._get_client = MagicMock(return_value=mock_client)

        req = VideoGenerationRequest(prompt="a dog", model="MiniMax-Hailuo-2.3", duration=6)
        result = await provider.generate(req)

        assert result.status == "succeeded"
        assert result.videos[0].url == "/uploads/generated/hl-123.mp4"


# ── Vidu (Bearer auth + creations polling) ──

class TestViduAdapter:
    def test_config_correct(self):
        provider = DataEyesAIVideoProvider(api_key="test", base_url="https://platform.dataeyes.ai")
        v = provider.VENDORS["vidu"]
        assert v["submit_path"] == "/ent/v2/text2video"
        assert v["auth_scheme"] == "Bearer"

    def test_body_builder(self):
        provider = DataEyesAIVideoProvider(api_key="test", base_url="https://platform.dataeyes.ai")
        body = provider.VENDORS["vidu"]["build_submit_body"]("viduq3-pro", "test prompt", 5, {"resolution": "1080p"})
        assert body["model"] == "viduq3-pro"
        assert body["prompt"] == "test prompt"
        assert body["duration"] == 5
        assert body["resolution"] == "1080p"

    @pytest.mark.asyncio
    async def test_polls_creations_endpoint_and_extracts_url(self, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", AsyncMock())
        provider = DataEyesAIVideoProvider(api_key="test", base_url="https://platform.dataeyes.ai")
        submit = mock_resp(200, {"task_id": "vidu-123", "state": "created"})
        poll = mock_resp(200, {"state": "success", "creations": [{"url": "https://vidu-cdn.com/v.mp4"}]})
        mock = setup_mock_client(provider, submit, poll)

        req = VideoGenerationRequest(prompt="shoe", model="viduq3-pro", duration=5)
        result = await provider.generate(req)

        get_call = mock.get.call_args.args[0]
        assert get_call == "/vidu/ent/v2/tasks/vidu-123/creations"
        assert result.status == "succeeded"
        assert result.videos[0].url == "/uploads/generated/vidu-123.mp4"


# ── Jimeng (Action API) ──

class TestJimengAdapter:
    def test_config_correct(self):
        provider = DataEyesAIVideoProvider(api_key="test", base_url="https://platform.dataeyes.ai")
        j = provider.VENDORS["jimeng"]
        assert "Action=CVSync2AsyncSubmitTask" in j["submit_path"]
        assert j["success_statuses"] == ("done",)

    def test_body_builder(self):
        provider = DataEyesAIVideoProvider(api_key="test", base_url="https://platform.dataeyes.ai")
        body = provider.VENDORS["jimeng"]["build_submit_body"]("jimeng_t2v_v30", "fish", 5, {"frames": 241})
        assert body["req_key"] == "jimeng_t2v_v30"
        assert body["prompt"] == "fish"
        assert body["frames"] == 241


# ── Grok (request_id) ──

class TestGrokAdapter:
    @pytest.mark.asyncio
    async def test_handles_request_id(self, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", AsyncMock())
        provider = DataEyesAIVideoProvider(api_key="test", base_url="https://platform.dataeyes.ai")
        submit = mock_resp(200, {"request_id": "req-grok-123"})
        poll = mock_resp(200, {"request_id": "req-grok-123", "status": "done", "video": {"url": "https://grok-cdn.com/v.mp4"}})
        mock = setup_mock_client(provider, submit, poll)

        req = VideoGenerationRequest(prompt="sunset", model="grok-imagine-video", duration=10)
        result = await provider.generate(req)

        assert result.status == "succeeded"
        assert result.videos[0].url == "/uploads/generated/req-grok-123.mp4"

    def test_parse_task_id_uses_request_id(self):
        provider = DataEyesAIVideoProvider(api_key="test", base_url="https://platform.dataeyes.ai")
        tid = provider.VENDORS["grok"]["parse_task_id"]({"request_id": "req-abc"})
        assert tid == "req-abc"
