import re
"""Image generation service — provider registry + real implementations."""
import io
import base64
import uuid
import hashlib
import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import asyncio
import inspect
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

logger = logging.getLogger(__name__)


def _request_with_model(request: ImageGenerationRequest, model: str) -> ImageGenerationRequest:
    """复制请求并替换 model(兼容 pydantic v1/v2)。"""
    if hasattr(request, "model_copy"):
        return request.model_copy(update={"model": model})
    return request.copy(update={"model": model})


_UPLOAD_ROOT = "/opt/visual-agent/uploads"


def _coerce_image_ref(url: str) -> str:
    """把图片引用规整成 DataEyes 能取的形式。

    DataEyes(NanoBanana)只认完整 http(s) URL 或 base64 data URL,不认服务器本地
    相对路径(/uploads/...)——直接传会被当成 base64 解码而 500。本地图读盘转 data URL;
    http/data 原样透传。带 uploads 目录越权保护,读不到则原样返回(让上游错误可见)。
    """
    if not url or url.startswith(("http://", "https://", "data:")):
        return url
    try:
        rel = url.lstrip("/")
        full = os.path.realpath(os.path.join("/opt/visual-agent", rel))
        root = os.path.realpath(_UPLOAD_ROOT)
        if full != root and not full.startswith(root + os.sep):
            return url  # 越界,不读
        with open(full, "rb") as fh:
            raw = fh.read()
        ext = os.path.splitext(full)[1].lower().lstrip(".")
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp", "gif": "gif"}.get(ext, "png")
        return f"data:image/{mime};base64,{base64.b64encode(raw).decode()}"
    except Exception:
        return url

# 图三: DataEyes 自动出图默认模型。历史默认是 gemini-2.5-flash-image(NanoBanana),
# 用户要求图片优先使用 gpt-image-2。集中一处定义, 可用 env 覆盖。
DEFAULT_DATAEYES_IMAGE_MODEL = os.getenv("DATAEYES_DEFAULT_IMAGE_MODEL", "gpt-image-2")


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

        # 占位图不再渲染 prompt 文本:DejaVuSans 无中文字形,会把中文 prompt 画成乱码方块。
        # 仅画一个居中的中性英文标签。
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=22)
        except OSError:
            font = ImageFont.load_default()
        label = "image placeholder"
        lbbox = draw.textbbox((0, 0), label, font=font)
        lw = lbbox[2] - lbbox[0]
        draw.text(((w - lw) // 2, h // 2 - 12), label, fill=(148, 163, 184), font=font)

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
    until status becomes "completed".
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
        size = request.options.get("size", f"{request.width}x{request.height}")
        # Determine if size should be included (openai_nosize models reject size)
        _nosize_models = {"ByteDance-Seedream-4.5", "ByteDance-Seedream-5.0", "doubao-seedream-4-5-251128", "doubao-seedream-5-0-260128"}

        payload = {
            "model": model,
            "prompt": request.prompt,
            "n": request.options.get("n", 1),
        }
        if model not in _nosize_models:
            payload["size"] = size
        resp = await client.post("/v1/images/generations?async=true", json=payload)
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"MigeAPI submit error ({resp.status_code}): {resp.text[:200]}",
            )

        submit_data = resp.json()
        # Actual format: {"code": 200, "data": [{"status": "submitted", "task_id": "..."}]}
        task_id = submit_data.get("task_id")  # top-level first
        data_items = submit_data.get("data", [])
        if isinstance(data_items, list) and len(data_items) > 0:
            task_id = data_items[0].get("task_id")
        if not task_id:
            raise HTTPException(
                status_code=502,
                detail=f"MigeAPI: no task_id in response: {resp.text[:200]}",
            )

        # Step 2: Poll until "completed" or "failed"
        for _ in range(60):  # max ~3 minutes
            await asyncio.sleep(3)
            poll_resp = await client.get(f"/v1/images/tasks/{task_id}")
            if poll_resp.status_code >= 400:
                continue

            poll_data = poll_resp.json()
            task = poll_data.get("data", {})
            status = task.get("status", "")

            if status in ("completed", "SUCCESS"):
                images = []
                result = task.get("result", {})
                images_raw = result.get("images", [])
                if images_raw:
                    for item in images_raw:
                        urls = item.get("url", [])
                        url = urls[0] if urls else ""
                        images.append(GeneratedImage(
                            url=url,
                            width=request.width,
                            height=request.height,
                            provider_asset_id=str(task.get("id", "")),
                        ))
                else:
                    # Fallback: use result_url directly
                    result_url = task.get("result_url", "")
                    if result_url:
                        images.append(GeneratedImage(
                            url=result_url,
                            width=request.width,
                            height=request.height,
                            provider_asset_id=str(task.get("id", "")),
                        ))

                return ImageGenerationResult(
                    provider="mige",
                    status="succeeded",
                    images=images,
                    raw=task,
                )

            elif status in ("failed", "FAILED", "ERROR"):
                error_msg = task.get("error", task.get("fail_reason", "unknown"))
                raise HTTPException(
                    status_code=502,
                    detail=f"MigeAPI task failed: {error_msg}",
                )

        raise HTTPException(status_code=504, detail="MigeAPI task timed out after 3 minutes")


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# DataEyesAI image provider (OpenAI-compatible, returns b64_json)
# ---------------------------------------------------------------------------


class DataEyesAIImageProvider(ImageGenerationProvider):
    """DataEyesAI image generation - OpenAI compatible, returns base64 PNG.

    POST /v1/images/generations
    Response: {"data": [{"b64_json": "iVBORw0..."}]}
    """

    descriptor = ProviderDescriptor(
        name="dataeyes",
        display_name="DataEyesAI",
        description="DataEyesAI - gpt-image-2 and other models",
    )

        # ── Model registry for format dispatch (Fix 2B) ──
    MODEL_REGISTRY = {
        # Gemini / NanoBanana models → chat/completions
        "gemini-2.5-flash-image": {
            "id": "gemini-2.5-flash-image",
            "name": "NanoBanana",
            "format": "nanobanana_openai",
        },
        "gemini-2.5-flash-image-preview": {
            "id": "gemini-2.5-flash-image-preview",
            "name": "NanoBanana Preview",
            "format": "nanobanana_openai",
        },
        "gemini-3-pro-image-preview": {
            "id": "gemini-3-pro-image-preview",
            "name": "NanoBanana Pro",
            "format": "nanobanana_openai",
        },
        "gemini-3.1-flash-image": {
            "id": "gemini-3.1-flash-image",
            "name": "NanoBanana Flash",
            "format": "nanobanana_openai",
        },
        "gemini-3.1-flash-image-preview-4k": {
            "id": "gemini-3.1-flash-image-preview-4k",
            "name": "NanoBanana Flash 4K",
            "format": "nanobanana_openai",
        },
        "gemini-3.1-flash-image": {
            "id": "gemini-3.1-flash-image",
            "name": "NanoBanana Flash",
            "format": "nanobanana_openai",
        },
        "gemini-2.5-flash-image-preview": {
            "id": "gemini-2.5-flash-image-preview",
            "name": "NanoBanana Preview",
            "format": "nanobanana_openai",
        },
    }

    VERIFIED_IMAGE_MODELS = [
        {"id": "gpt-image-1", "label": "GPT Image 1", "est_seconds": 45},
        {"id": "gpt-image-1-sp", "label": "GPT Image 1 SP", "est_seconds": 45},
        {"id": "gpt-image-1.5", "label": "GPT Image 1.5", "est_seconds": 60},
        {"id": "gpt-image-1.5-sp", "label": "GPT Image 1.5 SP", "est_seconds": 60},
        {"id": "gpt-image-2", "label": "GPT Image 2", "est_seconds": 75},
        {"id": "gpt-image-2-sp", "label": "GPT Image 2 SP", "est_seconds": 75},
        {"id": "imagen-4.0-generate-001", "label": "Imagen 4", "est_seconds": 60},
        {"id": "grok-imagine-image", "label": "Grok Imagine", "est_seconds": 10},
        {"id": "grok-imagine-image-pro", "label": "Grok Imagine Pro", "est_seconds": 12},
        {"id": "ByteDance-Seedream-4.0", "label": "Seedream 4.0", "est_seconds": 8},
        {"id": "ByteDance-Seedream-4.5", "label": "Seedream 4.5", "est_seconds": 8},
        {"id": "ByteDance-Seedream-5.0", "label": "Seedream 5.0", "est_seconds": 10},
        {"id": "doubao-seedream-4-0-250828", "label": "Doubao Seedream 4.0", "est_seconds": 8},
        {"id": "doubao-seedream-4-5-251128", "label": "Doubao Seedream 4.5", "est_seconds": 8},
        {"id": "doubao-seedream-5-0-260128", "label": "Doubao Seedream 5.0", "est_seconds": 10},
    ]
    FALLBACK_MODELS = [
        {"kind": "image", "id": model["id"], "label": model["label"], "desc": "DataEyes verified image model", "est_seconds": model["est_seconds"], "available": True}
        for model in VERIFIED_IMAGE_MODELS[:3]
    ]

    def __init__(self, api_key=None, base_url=None):
        self._api_key = api_key or os.getenv("DATAEYES_API_KEY", "")
        self._base_url = (base_url or os.getenv("DATAEYES_BASE_URL", "https://cloud.dataeyes.ai/v1")).rstrip("/")
        self._client = None

    def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=300.0,
            )
        return self._client

    async def list_remote_models(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self._base_url}/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
        if resp.status_code >= 400:
            return [*self.FALLBACK_MODELS, self._unavailable_model("video"), self._unavailable_model("3d")]
        data = resp.json()
        models = data.get("data", []) if isinstance(data, dict) else []
        remote_ids = {model.get("id", "") for model in models if isinstance(model, dict)}
        result = []
        for model in self.VERIFIED_IMAGE_MODELS:
            if model["id"] in remote_ids:
                result.append({
                    "kind": "image",
                    "id": model["id"],
                    "label": model["label"],
                    "desc": "DataEyes verified image model",
                    "est_seconds": model["est_seconds"],
                    "available": True,
                })
        if not result:
            result.extend(self.FALLBACK_MODELS)
        result.append(self._unavailable_model("video"))
        result.append(self._unavailable_model("3d"))
        return result

    @staticmethod
    def _unavailable_model(kind: str) -> dict:
        return {
            "kind": kind,
            "id": f"{kind}-not-connected",
            "label": "未接入",
            "desc": "未接入",
            "est_seconds": None,
            "available": False,
        }

    def _extract_base64_from_markdown(self, text_content: str) -> str | None:
        """Extract base64 image data from markdown image syntax.

        Gemini models return: ![image](data:image/png;base64,iVBORw0...)
        """
        match = re.search(
            r'!\[.*?\]\(data:image/\w+;base64,([A-Za-z0-9+/=]+)\)',
            text_content,
        )
        return match.group(1) if match else None

    async def _generate_nanobanana_openai(
        self, request: ImageGenerationRequest, client, image_urls: list[str] | None = None
    ) -> ImageGenerationResult:
        """Generate image via chat/completions for Gemini/NanoBanana models.

        These models do NOT support /images/generations — they return images
        as base64 markdown in chat completion responses.
        """
        import base64 as _b64

        source_image_urls = image_urls or request.options.get("image_urls") or []
        if source_image_urls:
            content = [{"type": "text", "text": request.prompt}]
            content.extend(
                {"type": "image_url", "image_url": {"url": _coerce_image_ref(url)}}
                for url in source_image_urls
            )
        else:
            content = request.prompt

        chat_payload = {
            "model": request.model or "gemini-2.5-flash-image",
            "messages": [{
                "role": "user",
                "content": content,
            }],
            "max_tokens": 4096,
        }

        resp = await client.post("/chat/completions", json=chat_payload)
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"DataEyesAI NanoBanana error ({resp.status_code}): {resp.text[:300]}",
            )

        data = resp.json()
        if inspect.isawaitable(data):
            data = await data

        content = ""
        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")

        b64 = self._extract_base64_from_markdown(content)
        if not b64:
            raise HTTPException(
                status_code=502,
                detail=f"DataEyesAI NanoBanana returned no image in response: {content[:200]}",
            )

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"dataeyes_nb_{uuid.uuid4().hex[:12]}_{request.width}x{request.height}.png"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as image_file:
            image_file.write(_b64.b64decode(b64))

        return ImageGenerationResult(
            provider="dataeyes",
            status="succeeded",
            images=[GeneratedImage(
                url=f"/uploads/generated/{filename}",
                width=request.width,
                height=request.height,
                provider_asset_id=str(data.get("id", "")),
            )],
            raw=data,
        )

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        client = self._get_client()
        model = request.model or DEFAULT_DATAEYES_IMAGE_MODEL

        # ── Format dispatch (Fix 2B) ──
        model_meta = self.MODEL_REGISTRY.get(model, {})
        fmt = model_meta.get("format", "openai")

        # ── 以图生图路由(需求二) ──
        # reference_image_url / options.image_urls 是源图。gpt-image-2 走的
        # /images/generations 不接收图片输入,只有 gemini/NanoBanana(chat/completions)
        # 能真正读取源图做编辑。因此凡带源图的请求,一律路由到吃图模型并把图喂进去;
        # 调用方指定的模型若本身不吃图,自动换成 gemini(env 可覆盖),并带 gemini 兜底回退,
        # 确保"务必以图生图"不静默退化成文生图。
        source_image_urls: list[str] = []
        if request.reference_image_url:
            source_image_urls.append(request.reference_image_url)
        for u in (request.options.get("image_urls") or []):
            if u and u not in source_image_urls:
                source_image_urls.append(u)

        if source_image_urls:
            i2i_models: list[str] = []
            if fmt == "nanobanana_openai":
                i2i_models.append(model)  # 调用方已选了能吃图的模型
            i2i_models.append(os.getenv("DATAEYES_IMG2IMG_MODEL", "gemini-3-pro-image-preview"))
            i2i_models.append("gemini-2.5-flash-image")  # 兜底吃图模型
            seen: set[str] = set()
            i2i_models = [m for m in i2i_models if m and not (m in seen or seen.add(m))]
            last_exc: Exception | None = None
            for m in i2i_models:
                try:
                    return await self._generate_nanobanana_openai(
                        _request_with_model(request, m), client, image_urls=source_image_urls
                    )
                except Exception as exc:  # noqa: BLE001 — 换下一个吃图模型重试
                    last_exc = exc
                    logger.warning("img2img model %s failed: %s", m, exc)
                    continue
            assert last_exc is not None
            raise last_exc

        if fmt == "nanobanana_openai":
            return await self._generate_nanobanana_openai(request, client)

        size = request.options.get("size", f"{request.width}x{request.height}")

        # Determine if size should be included (openai_nosize models reject size)
        _nosize_models = {"ByteDance-Seedream-4.5", "ByteDance-Seedream-5.0", "doubao-seedream-4-5-251128", "doubao-seedream-5-0-260128"}

        payload = {
            "model": model,
            "prompt": request.prompt,
            "n": request.options.get("n", 1),
        }
        if model not in _nosize_models:
            payload["size"] = size

        # Retry on intermittent DataEyes routing bug (tool_choice 400)
        _TOOL_CHOICE_400_SIG = "Tool choice 'image_generation' not found in 'tools'"
        _MAX_RETRIES = 5
        for _attempt in range(_MAX_RETRIES + 1):
            resp = await client.post("/images/generations", json=payload)
            if resp.status_code == 200:
                break
            if resp.status_code == 400 and _TOOL_CHOICE_400_SIG in resp.text and _attempt < _MAX_RETRIES:
                await asyncio.sleep(0.3 * (_attempt + 1))
                continue
            raise HTTPException(
                status_code=502,
                detail=f"DataEyesAI image error ({resp.status_code}): {resp.text[:300]}",
            )

        data = resp.json()
        if inspect.isawaitable(data):
            data = await data
        if isinstance(data, dict):
            data.setdefault("requested_model", model)
        items = data.get("data", [])
        images = []
        for item in items:
            b64 = item.get("b64_json", "")
            url = item.get("url", "")
            # Handle URL-based responses (grok, etc.)
            if url and not b64:
                images.append(GeneratedImage(
                    url=url,
                    width=request.width,
                    height=request.height,
                    provider_asset_id=str(data.get("created", "")),
                ))
                continue
            if b64:
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                filename = f"dataeyes_{uuid.uuid4().hex[:12]}_{request.width}x{request.height}.png"
                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, "wb") as image_file:
                    image_file.write(base64.b64decode(b64))
                url = f"/uploads/generated/{filename}"
            images.append(GeneratedImage(
                url=url,
                width=request.width,
                height=request.height,
                provider_asset_id=str(data.get("created", "")),
            ))

        return ImageGenerationResult(
            provider="dataeyes",
            status="succeeded",
            images=images,
            raw=data,
        )

class ImageGenerationService:
    def __init__(self) -> None:
        self._providers: dict[str, ImageGenerationProvider] = {}

    def register(self, provider: ImageGenerationProvider) -> None:
        self._providers[provider.descriptor.name] = provider

    def registered_providers(self):
        return list(self._providers.values())

    def list_providers(self) -> list[dict[str, str]]:
        return [
            {
                "name": p.descriptor.name,
                "display_name": p.descriptor.display_name,
                "description": p.descriptor.description,
            }
            for p in self._providers.values()
        ]

    async def list_models(self) -> list[dict]:
        provider = self._providers.get("dataeyes")
        models = []
        if provider and hasattr(provider, "list_remote_models"):
            models = await provider.list_remote_models()
        tabs = {"image", "video", "3d"}
        existing = {model.get("kind") for model in models}
        for kind in sorted(tabs - existing):
            models.append({
                "kind": kind,
                "id": f"{kind}-not-connected",
                "label": "未接入",
                "desc": "未接入",
                "est_seconds": None,
                "available": False,
            })
        return models

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
image_generation_service.register(DataEyesAIImageProvider())
