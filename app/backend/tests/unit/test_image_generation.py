"""Unit tests for image generation service."""
import pytest
from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.models.image_generation_model import (
    GeneratedImage,
    ImageGenerationRequest,
    ImageGenerationResult,
)
from app.services.image_generation_service import (
    ImageGenerationService,
    LocalPlaceholderProvider,
    PollinationsProvider,
)
from app.api.image_generation_routes import router


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestImageGenerationRequest:
    def test_defaults(self):
        req = ImageGenerationRequest(prompt="a cat")
        assert req.provider == "local"
        assert req.width == 1024
        assert req.height == 1024

    def test_custom_provider(self):
        req = ImageGenerationRequest(provider="comfyui", prompt="a cat")
        assert req.provider == "comfyui"

    def test_rejects_invalid_provider(self):
        with pytest.raises(ValueError):
            ImageGenerationRequest(provider="invalid_provider", prompt="test")

    def test_rejects_invalid_dimensions(self):
        with pytest.raises(ValueError):
            ImageGenerationRequest(prompt="test", width=3000)

    def test_full_params(self):
        req = ImageGenerationRequest(
            provider="pollinations",
            prompt="sunset over mountains",
            negative_prompt="blurry",
            width=512,
            height=512,
            seed=42,
            model="flux",
            options={"style": "photorealistic"},
        )
        assert req.seed == 42
        assert req.model == "flux"


class TestImageGenerationResult:
    def test_succeeded_result(self):
        result = ImageGenerationResult(
            provider="pollinations",
            status="succeeded",
            images=[GeneratedImage(url="https://example.com/img.png")],
        )
        assert result.provider == "pollinations"
        assert len(result.images) == 1

    def test_failed_result(self):
        result = ImageGenerationResult(
            provider="pollinations",
            status="failed",
        )
        assert result.images == []


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestImageGenerationService:
    def test_list_providers_includes_pollinations(self):
        service = ImageGenerationService()
        service.register(PollinationsProvider())
        providers = service.list_providers()
        names = [p["name"] for p in providers]
        assert "pollinations" in names

    async def test_unknown_provider_is_rejected(self):
        service = ImageGenerationService()
        service.register(PollinationsProvider())
        request = ImageGenerationRequest(provider="stability", prompt="test")
        with pytest.raises(HTTPException) as ctx:
            await service.generate(request)
        assert ctx.value.status_code == 400

    @patch.object(PollinationsProvider, "generate")
    async def test_known_provider_is_called(self, mock_generate):
        mock_generate.return_value = ImageGenerationResult(
            provider="pollinations",
            status="succeeded",
            images=[GeneratedImage(url="https://example.com/img.png")],
        )
        service = ImageGenerationService()
        service.register(PollinationsProvider())
        service.register(LocalPlaceholderProvider())
        request = ImageGenerationRequest(provider="pollinations", prompt="test")
        result = await service.generate(request)
        assert result.provider == "pollinations"
        assert result.status == "succeeded"


# ---------------------------------------------------------------------------
# Router tests
# ---------------------------------------------------------------------------


class TestImageGenerationRoutes:
    def test_list_providers_endpoint(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get("/api/v1/generation/providers")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        names = [p["name"] for p in data["providers"]]
        assert "pollinations" in names

    @patch(
        "app.services.image_generation_service.PollinationsProvider.generate",
        new_callable=AsyncMock,
    )
    def test_generate_image_returns_200(self, mock_generate):
        mock_generate.return_value = ImageGenerationResult(
            provider="pollinations",
            status="succeeded",
            images=[GeneratedImage(url="https://example.com/img.png")],
        )
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.post(
            "/api/v1/generation/image",
            json={"provider": "pollinations", "prompt": "a cat"},
        )
        assert response.status_code == 200
        assert response.json()["provider"] == "pollinations"

    def test_generate_image_unknown_provider_returns_400(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.post(
            "/api/v1/generation/image",
            json={"provider": "nonexistent", "prompt": "test"},
        )
        assert response.status_code == 422  # Pydantic validation rejects invalid provider
