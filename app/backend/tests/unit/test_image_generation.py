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
    DataEyesAIImageProvider,
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


class TestDataEyesAIProvider:
    @patch("app.services.image_generation_service.UPLOAD_DIR", "/tmp/moyag-test-generated")
    @patch("httpx.AsyncClient.post")
    async def test_dataeyes_b64_response_is_saved_as_static_url(self, mock_post):
        import base64
        from pathlib import Path
        from PIL import Image
        import io

        image = Image.new("RGB", (16, 16), color=(255, 0, 0))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"created": 123, "data": [{"b64_json": b64}]}

        provider = DataEyesAIImageProvider(api_key="test-key", base_url="https://cloud.dataeyes.ai/v1")
        result = await provider.generate(ImageGenerationRequest(provider="dataeyes", prompt="red shoe", model="gpt-image-2"))

        assert result.provider == "dataeyes"
        assert result.images[0].url.startswith("/uploads/generated/")
        assert not result.images[0].url.startswith("data:")
        saved = Path("/tmp/moyag-test-generated") / Path(result.images[0].url).name
        assert saved.exists()

    @patch("app.services.image_generation_service.UPLOAD_DIR", "/tmp/moyag-test-generated")
    @patch("httpx.AsyncClient.post")
    async def test_dataeyes_default_model_is_verified_fast_image_model(self, mock_post):
        import base64
        from PIL import Image
        import io

        image = Image.new("RGB", (16, 16), color=(255, 0, 0))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"created": 123, "data": [{"b64_json": b64}]}

        provider = DataEyesAIImageProvider(api_key="test-key", base_url="https://cloud.dataeyes.ai/v1")
        await provider.generate(ImageGenerationRequest(provider="dataeyes", model="gpt-image-1-sp", prompt="red shoe"))

        payload = mock_post.call_args.kwargs["json"]
        assert payload["model"] == "gpt-image-1-sp"

    async def test_dataeyes_model_selector_returns_verified_curated_models_only(self):
        provider = DataEyesAIImageProvider(api_key="test-key", base_url="https://cloud.dataeyes.ai/v1")
        remote = [
            {"id": "gpt-image-1"},
            {"id": "gpt-image-1-sp"},
            {"id": "gpt-image-1.5"},
            {"id": "gpt-image-1.5-sp"},
            {"id": "gpt-image-2"},
            {"id": "gpt-image-2-sp"},
            {"id": "gemini-2.5-flash-image"},
            {"id": "chatgpt-image-latest"},
            {"id": "veo-3.1-generate-preview"},
        ]

        import httpx
        with patch.object(httpx.AsyncClient, "get") as mock_get:
            mock_resp = httpx.Response(200, json={"data": remote})
            mock_get.return_value = mock_resp
            models = await provider.list_remote_models()

        image_ids = [m["id"] for m in models if m["kind"] == "image"]
        assert "gpt-image-1" in image_ids
        assert "gpt-image-1-sp" in image_ids
        assert "gpt-image-2" in image_ids
        assert "gpt-image-1.5-sp" in image_ids
        assert "gemini-2.5-flash-image" not in image_ids
        assert "chatgpt-image-latest" not in image_ids
        assert all(m.get("available") is True for m in models if m["kind"] == "image")
        video = [m for m in models if m["kind"] == "video"]
        assert video and video[0]["available"] is False
        assert video[0]["label"] == "未接入"


class TestModelPreferenceRoutes:
    @patch("app.services.image_generation_service.image_generation_service.list_models")
    def test_models_endpoint_returns_kind_tabs_and_real_ids(self, mock_list_models):
        mock_list_models.return_value = [
            {"kind": "image", "id": "gpt-image-2", "label": "gpt-image-2", "available": True},
            {"kind": "video", "id": "veo-test", "label": "veo-test", "available": False, "desc": "未接入"},
        ]
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get("/api/v1/generation/models")
        assert response.status_code == 200
        data = response.json()
        assert {tab["kind"] for tab in data["tabs"]} == {"image", "video", "3d"}
        first = data["models"][0]
        assert {"modelKey", "provider", "modality", "source", "productionUsable", "id", "kind"} <= set(first)
