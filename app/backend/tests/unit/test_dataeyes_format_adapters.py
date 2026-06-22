"""Unit tests for DataEyesAIImageProvider format adapters (Fix 2B).

Tests that Gemini image models correctly route through chat/completions
and that URL-based responses (grok) are handled.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.image_generation_model import (
    GeneratedImage,
    ImageGenerationRequest,
    ImageGenerationResult,
)
from app.services.image_generation_service import DataEyesAIImageProvider


class TestGeminiChatCompletionsFormat:
    """Gemini image models use chat/completions, not /images/generations."""

    @pytest.mark.asyncio
    async def test_gemini_model_routes_through_chat_completions(self):
        """When model format is nanobanana_openai, the provider MUST
        call /v1/chat/completions and extract base64 from markdown response."""
        provider = DataEyesAIImageProvider(
            api_key="test-key",
            base_url="https://cloud.dataeyes.ai/v1"
        )
        provider._registry = {
            "gemini-2.5-flash-image": {
                "id": "gemini-2.5-flash-image",
                "name": "NanoBanana",
                "format": "nanobanana_openai",
            }
        }
        provider._api_key = "test-key"

        markdown_response = """Here is your image:\n![image](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==)"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-xxx",
            "choices": [{
                "message": {"content": markdown_response}
            }]
        }

        with patch.object(provider, '_get_client') as mock_client:
            mock_client.return_value.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)

            req = ImageGenerationRequest(
                provider="dataeyes",
                prompt="a red apple",
                model="gemini-2.5-flash-image",
                width=1024,
                height=1024,
            )
            result = await provider.generate(req)

            assert result.status == "succeeded"
            assert len(result.images) == 1
            assert result.images[0].url.startswith("/uploads/generated/")
            # Verify chat completions was called, not images/generations
            call_args = mock_client.return_value.post.call_args
            assert "/chat/completions" in str(call_args)

    @pytest.mark.asyncio
    async def test_gemini_model_no_image_in_response_raises(self):
        """If chat completions returns no image markdown, should raise error."""
        provider = DataEyesAIImageProvider(
            api_key="test-key",
            base_url="https://cloud.dataeyes.ai/v1"
        )
        provider._registry = {
            "gemini-2.5-flash-image": {
                "id": "gemini-2.5-flash-image",
                "format": "nanobanana_openai",
            }
        }
        provider._api_key = "test-key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-xxx",
            "choices": [{
                "message": {"content": "I cannot generate that image."}
            }]
        }

        with patch.object(provider, '_get_client') as mock_client:
            mock_client.return_value.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)

            from fastapi import HTTPException
            req = ImageGenerationRequest(
                provider="dataeyes",
                prompt="something inappropriate",
                model="gemini-2.5-flash-image",
            )
            with pytest.raises(HTTPException) as exc_info:
                await provider.generate(req)
            assert exc_info.value.status_code == 502
            assert "no image" in str(exc_info.value.detail).lower()


class TestUrlBasedImageResponse:
    """Some models (grok) return url instead of b64_json."""

    @pytest.mark.asyncio
    async def test_url_based_response_handled(self):
        """Provider should handle responses with url field (not b64_json)."""
        provider = DataEyesAIImageProvider(
            api_key="test-key",
            base_url="https://cloud.dataeyes.ai/v1"
        )
        provider._api_key = "test-key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{
                "url": "https://imgen.x.ai/xai-imgen/test.jpeg",
                "mime_type": "image/jpeg"
            }]
        }

        with patch.object(provider, '_get_client') as mock_client:
            mock_client.return_value.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)

            req = ImageGenerationRequest(
                provider="dataeyes",
                prompt="a cat",
                model="grok-imagine-image",
                width=1024,
                height=1024,
            )
            result = await provider.generate(req)

            assert result.status == "succeeded"
            assert len(result.images) == 1
            # URL-based models return the direct URL (not saved locally)
            assert "imgen.x.ai" in result.images[0].url or result.images[0].url.startswith("/uploads/")


class TestFormatDispatch:
    """Provider uses model registry format to dispatch to correct adapter."""

    @pytest.mark.asyncio
    async def test_unknown_model_falls_back_to_openai_format(self):
        """Models not in registry should use default openai format."""
        provider = DataEyesAIImageProvider(
            api_key="test-key",
            base_url="https://cloud.dataeyes.ai/v1"
        )
        provider._api_key = "test-key"
        provider._registry = {}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"b64_json": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}]
        }

        with patch.object(provider, '_get_client') as mock_client:
            mock_client.return_value.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)

            req = ImageGenerationRequest(
                provider="dataeyes",
                prompt="test",
                model="some-unknown-model",
            )
            result = await provider.generate(req)

            assert result.status == "succeeded"
            # Should have called /images/generations (openai format)
            call_args = mock_client.return_value.post.call_args
            assert "/images/generations" in str(call_args)
