"""Tests for video generation service."""
import pytest
from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.models.video_generation_model import (
    GeneratedVideo,
    VideoGenerationRequest,
    VideoGenerationResult,
)
from app.services.video_generation_service import (
    LocalPlaceholderVideoProvider,
    VideoGenerationService,
)


class TestVideoGenerationRequest:
    def test_defaults(self):
        req = VideoGenerationRequest(prompt="product demo")
        assert req.provider == "local"
        assert req.duration == 15.0
        assert req.fps == 24
        assert req.width == 1024

    def test_custom_params(self):
        req = VideoGenerationRequest(
            provider="runway",
            prompt="cinematic shot",
            duration=30.0,
            fps=30,
            width=1920,
            height=1080,
        )
        assert req.fps == 30
        assert req.width == 1920


class TestVideoGenerationService:
    def test_list_providers(self):
        service = VideoGenerationService()
        service.register(LocalPlaceholderVideoProvider())
        names = [p["name"] for p in service.list_providers()]
        assert "local" in names

    async def test_unknown_provider_rejected(self):
        service = VideoGenerationService()
        service.register(LocalPlaceholderVideoProvider())
        request = VideoGenerationRequest(provider="kling", prompt="test")
        with pytest.raises(HTTPException) as ctx:
            await service.generate(request)
        assert ctx.value.status_code == 400

    @patch.object(LocalPlaceholderVideoProvider, "generate")
    async def test_known_provider_called(self, mock_generate):
        mock_generate.return_value = VideoGenerationResult(
            provider="local",
            status="succeeded",
            videos=[GeneratedVideo(url="/uploads/test.mp4")],
        )
        service = VideoGenerationService()
        service.register(LocalPlaceholderVideoProvider())
        request = VideoGenerationRequest(provider="local", prompt="test")
        result = await service.generate(request)
        assert result.provider == "local"
        assert result.status == "succeeded"
