"""Test Mige Video Provider."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _r(json_data):
    r = MagicMock()
    r.status_code = 200
    r.json = MagicMock(return_value=json_data)
    return r


class TestMigeVideoProvider:

    def test_mige_provider_registered(self):
        from app.services.video_generation_service import video_generation_service
        assert "mige" in [p["name"] for p in video_generation_service.list_providers()]

    @pytest.mark.asyncio
    async def test_mige_provider_submit_and_poll(self):
        from app.services.video_generation_service import MigeVideoProvider, VideoGenerationRequest
        provider = MigeVideoProvider(api_key="k", base_url="https://x.com")
        req = VideoGenerationRequest(provider="mige", prompt="猫", duration=5.0, width=1024, height=576)

        mock = AsyncMock()
        mock.post.return_value = _r({"task_id": "t1"})
        mock.get.side_effect = [
            _r({"data": {"status": "PROCESSING"}}),
            _r({"data": {"status": "SUCCESS", "data": {"data": {"result": {"videos": [{"url": ["http://x.mp4"]}]}, "id": "g1"}}}}),
        ]

        with patch.object(provider, "_get_client", return_value=mock):
            with patch("asyncio.sleep", return_value=None):
                result = await provider.generate(req)

        assert result.provider == "mige"
        assert result.status == "succeeded"
        assert len(result.videos) == 1

    @pytest.mark.asyncio
    async def test_mige_provider_handles_failure(self):
        from app.services.video_generation_service import MigeVideoProvider, VideoGenerationRequest
        from fastapi import HTTPException
        provider = MigeVideoProvider(api_key="k", base_url="https://x.com")
        req = VideoGenerationRequest(provider="mige", prompt="test")

        mock = AsyncMock()
        mock.post.return_value = _r({"task_id": "t1"})
        mock.get.side_effect = [_r({"data": {"status": "FAILED", "fail_reason": "bad"}})]

        with patch.object(provider, "_get_client", return_value=mock):
            with patch("app.services.video_generation_service.asyncio.sleep", return_value=None):
                with pytest.raises(HTTPException):
                    await provider.generate(req)
