"""Image generation service — provider registry + real implementations."""
import io
import hashlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

import asyncio
import httpx
from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageFont

from app.models.image_generation_model import (
    GeneratedImage,
    ImageGenerationRequest,
    ImageGenerationResult,
)

# ---------------------------------------------------------------------------
# Provider descriptor
# ---------------------------------------------------------------------------

UPLOAD_DIR = "/opt/visual-agent/uploads/generated"


@dataclass(frozen=True)
class ProviderDescriptor:
    name: str
    display_name: str
    description: str


# ---------------------------------------------------------------------------
# Abstract provider
# ---------------------------------------------------------------------------


class ImageGenerationProvider(ABC):
    descriptor: ProviderDescriptor

    @abstractmethod
    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Local placeholder provider (works without any API key, uses PIL)
# ---------------------------------------------------------------------------


class LocalPlaceholderProvider(ImageGenerationProvider):
    """Generates a styled placeholder image locally using PIL.

    No API key needed — perfect for MVP demos and testing the generation pipeline.
    """

    descriptor = ProviderDescriptor(
        name="local",
        display_name="Local Placeholder",
        description="Generates styled placeholder images locally (no API key)",
    )

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        w, h = request.width, request.height
        img = Image.new("RGB", (w, h), color=(248, 251, 255))

        draw = ImageDraw.Draw(img)

        # Gradient-like top bar
        for y in range(h // 5):
            r = int(125 + (211 - 125) * y / (h // 5))
            g = int(211 + (252 - 211) * y / (h // 5))
            b = 252
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        # Prompt text (truncated)
        text = request.prompt[:80]
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=24)
        except OSError:
            font = ImageFont.load_default()

        # Word-wrap
        lines = []
        words = text.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if draw.textbbox((0, 0), test, font=font)[2] < w - 40:
                line = test
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)

        y_start = h // 3
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            draw.text(
                ((w - tw) // 2, y_start + i * 36),
                line,
                fill=(15, 23, 42),
                font=font,
            )

        # Footer badge
        badge = f"{w}x{h} • local placeholder"
        draw.text((20, h - 30), badge, fill=(148, 163, 184), font=font)

        # Save
        prompt_hash = hashlib.md5(request.prompt.encode()).hexdigest()[:12]
        filename = f"gen_{prompt_hash}_{w}x{h}.png"
        filepath = os.path.join(UPLOAD_DIR, filename)
        img.save(filepath, "PNG")

        return ImageGenerationResult(
            provider="local",
            status="succeeded",
            images=[
                GeneratedImage(
                    url=f"/uploads/generated/{filename}",
                    width=w,
                    height=h,
                )
            ],
        )


# ---------------------------------------------------------------------------
# Pollinations.ai provider (cloud, needs API access)
# ---------------------------------------------------------------------------


class PollinationsProvider(ImageGenerationProvider):
    descriptor = ProviderDescriptor(
        name="pollinations",
        display_name="Pollinations.ai",
        description="Cloud AI image generation via Pollinations.ai",
    )

    BASE = "https://image.pollinations.ai/prompt"

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        encoded = request.prompt.replace("/", " ")
        params = {
            "width": request.width,
            "height": request.height,
            "nologo": "true",
        }
        if request.seed is not None:
            params["seed"] = str(request.seed)
        if request.model:
            params["model"] = request.model

        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            resp = await client.get(
                f"{self.BASE}/{encoded}",
                params=params,
            )

        if resp.status_code == 402:
            raise HTTPException(
                status_code=402,
                detail="Pollinations.ai now requires payment. Use provider='local' for free placeholder generation.",
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Pollinations returned {resp.status_code}: {resp.text[:200]}",
            )

        return ImageGenerationResult(
            provider="pollinations",
            status="succeeded",
            images=[
                GeneratedImage(
                    url=str(resp.url),
                    width=request.width,
                    height=request.height,
                    seed=request.seed,
                )
            ],
        )


# ---------------------------------------------------------------------------
# Service registry
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# OpenAI DALL-E provider
# ---------------------------------------------------------------------------


class OpenAIImageProvider(ImageGenerationProvider):
    """OpenAI DALL-E 3 image generation provider.

    Requires OPENAI_API_KEY in environment.
    Client is lazily initialized on first generate() call.
    """

    descriptor = ProviderDescriptor(
        name="dalle",
        display_name="OpenAI DALL-E 3",
        description="OpenAI DALL-E 3 — high-quality text-to-image generation",
    )

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._client = None  # lazy init

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self._api_key)
        return self._client

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        client = self._get_client()
        response = await client.images.generate(
            model=request.model or "dall-e-3",
            prompt=request.prompt,
            size=f"{request.width}x{request.height}",
            quality="standard",
            n=1,
        )

        image_data = response.data[0]
        return ImageGenerationResult(
            provider="dalle",
            status="succeeded",
            images=[
                GeneratedImage(
                    url=image_data.url,
                    width=request.width,
                    height=request.height,
                    provider_asset_id=getattr(image_data, "revised_prompt", None),
                )
            ],
        )



# ---------------------------------------------------------------------------
# Lovart provider
# ---------------------------------------------------------------------------


class LovartImageProvider(ImageGenerationProvider):
    """Lovart AI image generation provider.

    Requires LOVART_ACCESS_KEY and LOVART_SECRET_KEY in environment.
    Uses X-Lovart-Access-Key and X-Lovart-Secret-Key headers for auth.
    Client is lazily initialized on first generate() call.
    """

    descriptor = ProviderDescriptor(
        name="lovart",
        display_name="Lovart AI",
        description="Lovart — AI 设计智能体, 高质量商品图/海报生成",
    )

    def __init__(self, access_key: str | None = None, secret_key: str | None = None):
        self._access_key = access_key or os.getenv("LOVART_ACCESS_KEY", "")
        self._secret_key = secret_key or os.getenv("LOVART_SECRET_KEY", "")
        self._client = None  # lazy init

    def _get_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.lovart.ai",
                headers={
                    "X-Lovart-Access-Key": self._access_key,
                    "X-Lovart-Secret-Key": self._secret_key,
                    "Content-Type": "application/json",
                },
                timeout=120.0,
            )
        return self._client

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        client = self._get_client()
        payload = {
            "prompt": request.prompt,
            "width": request.width,
            "height": request.height,
        }
        if request.seed is not None:
            payload["seed"] = request.seed
        if request.model:
            payload["model"] = request.model

        resp = await client.post("/v1/images/generations", json=payload)
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Lovart image error ({resp.status_code}): {resp.text[:200]}",
            )
        data = resp.json()

        images = []
        for item in data.get("data", []):
            images.append(GeneratedImage(
                url=item.get("url", ""),
                width=request.width,
                height=request.height,
                provider_asset_id=item.get("id"),
            ))

        return ImageGenerationResult(
            provider="lovart",
            status="succeeded",
            images=images,
            raw=data,
        )



class MigeProvider(ImageGenerationProvider):
    """MigeAPI (米格API) image generation provider — async polling mode.

    Uses ?async=true to submit, then polls /v1/images/tasks/{task_id}
    until status becomes SUCCESS.
    """

    descriptor = ProviderDescriptor(
        name="mige",
        display_name="米格API (GPT Image-2)",
        description="米格API — GPT Image-2 via NewAPI gateway, async polling",
    )

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self._api_key = api_key or os.getenv("MIGEAPI_API_KEY", "")
        self._base_url = (base_url or os.getenv("MIGEAPI_BASE_URL", "https://api.migeapi.com")).rstrip("/")
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=300.0,
            )
        return self._client

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        client = self._get_client()
        model = request.model or "gpt-image-2"

        # Step 1: Submit with ?async=true
        payload = {
            "model": model,
            "prompt": request.prompt,
            "n": 1,
            "size": f"{request.width}x{request.height}",
        }
        resp = await client.post("/v1/images/generations?async=true", json=payload)
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"MigeAPI submit error ({resp.status_code}): {resp.text[:200]}",
            )
        submit_data = resp.json()
        task_id = submit_data.get("task_id")
        if not task_id:
            raise HTTPException(status_code=502, detail=f"MigeAPI: no task_id in response: {resp.text[:200]}")

        # Step 2: Poll until SUCCESS
        for _ in range(60):  # max ~3 minutes
            await asyncio.sleep(3)
            poll_resp = await client.get(f"/v1/images/tasks/{task_id}")
            if poll_resp.status_code >= 400:
                continue
            poll_data = poll_resp.json()
            task = poll_data.get("data", {})
            status = task.get("status", "")

            if status == "SUCCESS":
                inner = task.get("data", {}).get("data", {})
                result = inner.get("result", {})
                images_raw = result.get("images", [])

                images = []
                for item in images_raw:
                    urls = item.get("url", [])
                    url = urls[0] if urls else ""
                    images.append(GeneratedImage(
                        url=url,
                        width=request.width,
                        height=request.height,
                        provider_asset_id=inner.get("id"),
                    ))

                return ImageGenerationResult(
                    provider="mige",
                    status="succeeded",
                    images=images,
                    raw=inner,
                )

            elif status == "FAILED":
                raise HTTPException(
                    status_code=502,
                    detail=f"MigeAPI task failed: {task.get('fail_reason', 'unknown')}",
                )

        raise HTTPException(status_code=504, detail="MigeAPI task timed out after 3 minutes")



class ImageGenerationService:
    def __init__(self) -> None:
        self._providers: dict[str, ImageGenerationProvider] = {}

    def register(self, provider: ImageGenerationProvider) -> None:
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

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        provider = self._providers.get(request.provider)
        if provider is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown image generation provider: {request.provider}. "
                f"Available: {list(self._providers.keys())}",
            )
        return await provider.generate(request)


# Global singleton
image_generation_service = ImageGenerationService()
image_generation_service.register(LocalPlaceholderProvider())
image_generation_service.register(PollinationsProvider())
image_generation_service.register(OpenAIImageProvider())
image_generation_service.register(LovartImageProvider())
image_generation_service.register(MigeProvider())
