"""OpenAI DALL-E 图片生成 Provider 测试 — TDD RED"""
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.image_generation_model import (
    GeneratedImage,
    ImageGenerationRequest,
    ImageGenerationResult,
)


class TestOpenAIImageProvider:
    """测试 DALL-E Provider 的核心行为。"""

    @patch("openai.AsyncOpenAI")
    async def test_generate_returns_image_url(self, mock_openai_cls):
        """DALL-E 生成成功返回图片 URL。"""
        from app.services.image_generation_service import OpenAIImageProvider

        # Mock OpenAI response
        mock_client = MagicMock()
        mock_image = MagicMock()
        mock_image.url = "https://oaidalleapiprodscus.blob.core.windows.net/private/img-abc.png"
        mock_image.revised_prompt = "A beautiful cat"
        mock_response = MagicMock()
        mock_response.data = [mock_image]
        mock_client.images.generate = AsyncMock(return_value=mock_response)
        mock_openai_cls.return_value = mock_client

        provider = OpenAIImageProvider()
        provider._client = mock_client  # bypass init

        request = ImageGenerationRequest(
            provider="dalle",
            prompt="A cute cat sitting on a sofa",
            width=1024,
            height=1024,
        )
        result = await provider.generate(request)

        assert result.provider == "dalle"
        assert result.status == "succeeded"
        assert len(result.images) == 1
        assert "oaidalleapi" in result.images[0].url
        assert result.images[0].width == 1024
        assert result.images[0].height == 1024

    @patch("openai.AsyncOpenAI")
    async def test_generate_respects_dimensions(self, mock_openai_cls):
        """DALL-E 调用使用请求中的尺寸。"""
        from app.services.image_generation_service import OpenAIImageProvider

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(url="https://dalle.example.com/x.png", revised_prompt="test")]
        mock_client.images.generate = AsyncMock(return_value=mock_response)
        mock_openai_cls.return_value = mock_client

        provider = OpenAIImageProvider()
        provider._client = mock_client

        request = ImageGenerationRequest(
            provider="dalle",
            prompt="landscape",
            width=1792,
            height=1024,
        )
        await provider.generate(request)

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["size"] == "1792x1024"
        assert call_kwargs["prompt"] == "landscape"

    def test_registered_in_service(self):
        """OpenAI provider 在服务中可注册和列出。"""
        from app.services.image_generation_service import (
            ImageGenerationService,
            OpenAIImageProvider,
        )
        service = ImageGenerationService()
        provider = OpenAIImageProvider(api_key="sk-test-dummy")
        service.register(provider)
        names = [p["name"] for p in service.list_providers()]
        assert "dalle" in names
