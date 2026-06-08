"""Video generation service — provider registry + local placeholder."""
import hashlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from fastapi import HTTPException

from app.models.video_generation_model import (
    GeneratedVideo,
    VideoGenerationRequest,
    VideoGenerationResult,
)

UPLOAD_DIR = "/opt/visual-agent/uploads/generated"


@dataclass(frozen=True)
class VideoProviderDescriptor:
    name: str
    display_name: str
    description: str


class VideoGenerationProvider(ABC):
    descriptor: VideoProviderDescriptor

    @abstractmethod
    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        raise NotImplementedError


class LocalPlaceholderVideoProvider(VideoGenerationProvider):
    """Local placeholder — returns a static image as video stand-in."""

    descriptor = VideoProviderDescriptor(
        name="local",
        display_name="Local Placeholder",
        description="Placeholder video generation (no real video API yet)",
    )

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Reuse the image generation local provider for a placeholder image
        from app.services.image_generation_service import LocalPlaceholderProvider

        img_provider = LocalPlaceholderProvider()
        img_result = await img_provider.generate(
            type(
                "ImgReq",
                (),
                {
                    "prompt": f"Video: {request.prompt}",
                    "width": request.width,
                    "height": request.height,
                    "seed": request.seed,
                },
            )
        )

        return VideoGenerationResult(
            provider="local",
            status="succeeded",
            videos=[
                GeneratedVideo(
                    url=img_result.images[0].url,
                    duration=request.duration,
                    width=request.width,
                    height=request.height,
                    fps=request.fps,
                )
            ],
        )



# ---------------------------------------------------------------------------
# Runway provider
# ---------------------------------------------------------------------------


class RunwayVideoProvider(VideoGenerationProvider):
    """Runway Gen-3 video generation.

    Requires RUNWAY_API_KEY in environment.
    https://docs.runwayml.com/
    """

    descriptor = VideoProviderDescriptor(
        name="runway",
        display_name="Runway Gen-3",
        description="Runway Gen-3 Alpha — high-quality text-to-video",
    )

    def __init__(self, api_key: str | None = None):
        import os as _os
        self._api_key = api_key or _os.getenv("RUNWAY_API_KEY", "")
        self._client = None

    def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                base_url="https://api.runwayml.com/v1",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
            )
        return self._client

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        client = self._get_client()
        resp = await client.post("/generate", json={
            "prompt": request.prompt,
            "duration": request.duration,
            "width": request.width,
            "height": request.height,
            "seed": request.seed,
        })
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Runway error: {resp.text[:200]}")
        data = resp.json()
        return VideoGenerationResult(
            provider="runway",
            status="succeeded",
            videos=[GeneratedVideo(
                url=data.get("video_url", f"https://runwayml.com/v/{data.get('id','')}"),
                duration=request.duration,
                width=request.width,
                height=request.height,
                provider_asset_id=data.get("id"),
            )],
        )


# ---------------------------------------------------------------------------
# Pika provider
# ---------------------------------------------------------------------------


class PikaVideoProvider(VideoGenerationProvider):
    """Pika Labs video generation.

    Requires PIKA_API_KEY in environment.
    https://pika.art/
    """

    descriptor = VideoProviderDescriptor(
        name="pika",
        display_name="Pika Labs",
        description="Pika Labs — AI video generation",
    )

    def __init__(self, api_key: str | None = None):
        import os as _os
        self._api_key = api_key or _os.getenv("PIKA_API_KEY", "")
        self._client = None

    def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                base_url="https://api.pika.art/v1",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
            )
        return self._client

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        client = self._get_client()
        resp = await client.post("/generate", json={
            "prompt": request.prompt,
            "duration": request.duration,
            "width": request.width,
            "height": request.height,
            "fps": request.fps,
            "seed": request.seed,
        })
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Pika error: {resp.text[:200]}")
        data = resp.json()
        return VideoGenerationResult(
            provider="pika",
            status="succeeded",
            videos=[GeneratedVideo(
                url=data.get("video_url", ""),
                duration=request.duration,
                width=request.width,
                height=request.height,
                provider_asset_id=data.get("id"),
            )],
        )



class VideoGenerationService:
    def __init__(self) -> None:
        self._providers: dict[str, VideoGenerationProvider] = {}

    def register(self, provider: VideoGenerationProvider) -> None:
        self._providers[provider.descriptor.name] = provider

    def list_providers(self) -> list[dict[str, str]]:
        return [
            {
                "name": p.descriptor.name,
                "display_name": p.descriptor.display_name,
                "description": p.descriptor.description,
            }
            for p in self._providers.values()
        ]

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        provider = self._providers.get(request.provider)
        if provider is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown video provider: {request.provider}. "
                f"Available: {list(self._providers.keys())}",
            )
        return await provider.generate(request)


video_generation_service = VideoGenerationService()
video_generation_service.register(LocalPlaceholderVideoProvider())
video_generation_service.register(RunwayVideoProvider())
video_generation_service.register(PikaVideoProvider())
