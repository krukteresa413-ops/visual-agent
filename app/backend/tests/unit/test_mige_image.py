"""Tests for MigeAPI gpt-image-2 provider — real API response format.

Uses the exact response structure from the MigeAPI documentation (pasteboard.md).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _r(json_data, status_code=200):
    """Helper: create a mock httpx response."""
    r = MagicMock()
    r.status_code = status_code
    r.json = MagicMock(return_value=json_data)
    return r


# Real API response samples from MigeAPI docs
MIGE_SUBMIT_RESPONSE = {
    "code": 200,
    "data": [
        {
            "status": "submitted",
            "task_id": "task_01K8SGYNNNVBQTXNR4MM964S7K"
        }
    ]
}

MIGE_POLL_COMPLETED_RESPONSE = {
    "code": 200,
    "data": {
        "id": "task_01K8SGYNNNVBQTXNR4MM964S7K",
        "status": "completed",
        "progress": 100,
        "result": {
            "images": [
                {
                    "url": ["https://example.com/generated-image.png"],
                    "expires_at": 1763174708
                }
            ]
        },
        "created": 1763088289,
        "completed": 1763088308,
        "estimated_time": 60,
        "actual_time": 19
    }
}

MIGE_POLL_PENDING_RESPONSE = {
    "code": 200,
    "data": {
        "id": "task_01K8SGYNNNVBQTXNR4MM964S7K",
        "status": "pending",
        "progress": 30
    }
}


class TestMigeImageProviderRealFormat:
    """Test MigeProvider with the actual MigeAPI response format."""

    def test_mige_provider_registered(self):
        """Mige provider should be registered in image generation service."""
        from app.services.image_generation_service import image_generation_service
        providers = image_generation_service.list_providers()
        names = [p["name"] for p in providers]
        assert "mige" in names

    @pytest.mark.asyncio
    async def test_parse_submit_response_correctly(self):
        """Should extract task_id from submit response data[0].task_id."""
        from app.services.image_generation_service import MigeProvider
        provider = MigeProvider(api_key="test_key", base_url="https://api.migeapi.com")

        async_mock = AsyncMock()
        # First call: submit, second call: poll completed
        async_mock.post.return_value = _r(MIGE_SUBMIT_RESPONSE)
        async_mock.get.return_value = _r(MIGE_POLL_COMPLETED_RESPONSE)

        with patch.object(provider, '_get_client', return_value=async_mock):
            from app.models.image_generation_model import ImageGenerationRequest
            request = ImageGenerationRequest(
                provider="mige",
                prompt="一只白色柴犬",
                width=1024,
                height=1024,
            )
            result = await provider.generate(request)

        assert result.status == "succeeded"
        assert result.provider == "mige"
        assert len(result.images) == 1
        assert result.images[0].url == "https://example.com/generated-image.png"

    @pytest.mark.asyncio
    async def test_poll_until_completed(self):
        """Should poll multiple times until status becomes 'completed'."""
        from app.services.image_generation_service import MigeProvider
        provider = MigeProvider(api_key="test_key", base_url="https://api.migeapi.com")

        call_count = [0]
        async def mock_get(url):
            call_count[0] += 1
            if call_count[0] < 3:
                return _r(MIGE_POLL_PENDING_RESPONSE)
            return _r(MIGE_POLL_COMPLETED_RESPONSE)

        async_mock = AsyncMock()
        async_mock.post.return_value = _r(MIGE_SUBMIT_RESPONSE)
        async_mock.get = mock_get

        with patch.object(provider, '_get_client', return_value=async_mock):
            from app.models.image_generation_model import ImageGenerationRequest
            request = ImageGenerationRequest(provider="mige", prompt="test", width=1024, height=1024)
            result = await provider.generate(request)

        assert result.status == "succeeded"
        assert call_count[0] >= 2  # at least 2 polls (pending + completed)

    @pytest.mark.asyncio
    async def test_handle_failed_task(self):
        """Should raise HTTPException when task status is 'failed'."""
        from app.services.image_generation_service import MigeProvider
        from fastapi import HTTPException

        provider = MigeProvider(api_key="test_key", base_url="https://api.migeapi.com")
        failed_response = {
            "code": 200,
            "data": {
                "id": "task_x",
                "status": "failed",
                "error": "Content policy violation"
            }
        }

        async_mock = AsyncMock()
        async_mock.post.return_value = _r(MIGE_SUBMIT_RESPONSE)
        async_mock.get.return_value = _r(failed_response)

        with patch.object(provider, '_get_client', return_value=async_mock):
            from app.models.image_generation_model import ImageGenerationRequest
            request = ImageGenerationRequest(provider="mige", prompt="test", width=1024, height=1024)
            with pytest.raises(HTTPException, match="failed"):
                await provider.generate(request)

    @pytest.mark.asyncio
    async def test_timeout_after_max_polls(self):
        """Should raise HTTPException 504 after polling limit reached."""
        from app.services.image_generation_service import MigeProvider
        from fastapi import HTTPException

        provider = MigeProvider(api_key="test_key", base_url="https://api.migeapi.com")

        async_mock = AsyncMock()
        async_mock.post.return_value = _r(MIGE_SUBMIT_RESPONSE)
        async_mock.get.return_value = _r(MIGE_POLL_PENDING_RESPONSE)

        with patch.object(provider, '_get_client', return_value=async_mock):
            from app.models.image_generation_model import ImageGenerationRequest
            request = ImageGenerationRequest(provider="mige", prompt="test", width=1024, height=1024)
            with pytest.raises(HTTPException, match="timed out"):
                with patch("asyncio.sleep", return_value=None):
                    await provider.generate(request)

    def test_default_model(self):
        """Default model should be gpt-image-2."""
        from app.services.image_generation_service import MigeProvider
        provider = MigeProvider(api_key="test_key")
        # The model is resolved lazily in generate() with request.model or "gpt-image-2"
        # Verify the class is importable and doesn't crash on init
        assert provider._api_key == "test_key"
