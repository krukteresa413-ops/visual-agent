"""Video generation service — provider registry + local placeholder."""
import hashlib
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio
import httpx

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


# ---------------------------------------------------------------------------
# Lovart video provider
# ---------------------------------------------------------------------------


class LovartVideoProvider(VideoGenerationProvider):
    """Lovart AI video generation provider.

    Requires LOVART_ACCESS_KEY and LOVART_SECRET_KEY in environment.
    Uses X-Lovart-Access-Key and X-Lovart-Secret-Key headers for auth.
    Client is lazily initialized on first generate() call.
    """

    descriptor = VideoProviderDescriptor(
        name="lovart",
        display_name="Lovart AI",
        description="Lovart — AI 设计智能体, 高质量视频生成",
    )

    def __init__(self, access_key: str | None = None, secret_key: str | None = None):
        import os as _os
        self._access_key = access_key or _os.getenv("LOVART_ACCESS_KEY", "")
        self._secret_key = secret_key or _os.getenv("LOVART_SECRET_KEY", "")
        self._client = None

    def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                base_url="https://api.lovart.ai",
                headers={
                    "X-Lovart-Access-Key": self._access_key,
                    "X-Lovart-Secret-Key": self._secret_key,
                    "Content-Type": "application/json",
                },
                timeout=300.0,
            )
        return self._client

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        client = self._get_client()
        payload = {
            "prompt": request.prompt,
            "duration": request.duration,
            "width": request.width,
            "height": request.height,
            "fps": request.fps,
        }
        if request.seed is not None:
            payload["seed"] = request.seed
        if request.model:
            payload["model"] = request.model

        resp = await client.post("/v1/videos/generations", json=payload)
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Lovart video error ({resp.status_code}): {resp.text[:200]}",
            )
        data = resp.json()

        videos = []
        for item in data.get("data", []):
            videos.append(GeneratedVideo(
                url=item.get("url", ""),
                duration=request.duration,
                width=request.width,
                height=request.height,
                fps=request.fps,
                provider_asset_id=item.get("id"),
            ))

        return VideoGenerationResult(
            provider="lovart",
            status="succeeded",
            videos=videos,
        )


class MigeVideoProvider(VideoGenerationProvider):
    """MigeAPI video generation provider — async polling mode."""


    descriptor = VideoProviderDescriptor(
        name="mige",
        display_name="米格API (Video)",
        description="米格API — video generation via async polling",
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
                timeout=600.0,
                trust_env=False,
            )
        return self._client

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        client = self._get_client()
        model = request.model or "grok-video-3"

        payload = {
            "model": model,
            "prompt": request.prompt,
            "duration": request.duration,
            "width": request.width,
            "height": request.height,
        }
        if request.negative_prompt:
            payload["negative_prompt"] = request.negative_prompt

        resp = await client.post("/v1/video/generations?async=true", json=payload)
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"MigeAPI video submit error ({resp.status_code}): {resp.text[:200]}",
            )
        submit_data = resp.json()
        task_id = submit_data.get("task_id")
        if not task_id:
            raise HTTPException(status_code=502, detail=f"MigeAPI video: no task_id: {resp.text[:200]}")

        for _ in range(120):
            await asyncio.sleep(5)
            poll_resp = await client.get(f"/v1/images/tasks/{task_id}")
            if poll_resp.status_code >= 400:
                continue
            poll_data = poll_resp.json()
            task = poll_data.get("data", {})
            status = task.get("status", "")

            # Accept both completed/SUCCESS (dual-format compat)
            if status in ("SUCCESS", "completed"):
                videos = []

                # Format A: nested result.videos (video-specific — inside data.data.result)
                inner_data = task.get("data", {})
                if isinstance(inner_data, dict):
                    inner2 = inner_data.get("data", {})
                    result = inner2.get("result", {})
                    videos_raw = result.get("videos", [])
                    for item in videos_raw:
                        urls = item.get("url", [])
                        url = urls[0] if urls else ""
                        if url:
                            videos.append(GeneratedVideo(
                                url=url,
                                duration=request.duration,
                                width=request.width,
                                height=request.height,
                                provider_asset_id=str(task.get("id", "")),
                            ))

                # Format B: top-level result_url fallback
                if not videos:
                    result_url = task.get("result_url", "")
                    if result_url:
                        videos.append(GeneratedVideo(
                            url=result_url,
                            duration=request.duration,
                            width=request.width,
                            height=request.height,
                            provider_asset_id=str(task.get("id", "")),
                        ))

                if videos:
                    return VideoGenerationResult(
                        provider="mige",
                        status="succeeded",
                        videos=videos,
                    )

            elif status in ("FAILED", "ERROR", "failed", "error"):
                raise HTTPException(
                    status_code=502,
                    detail=f"MigeAPI video task failed: {task.get('fail_reason', 'unknown')}",
                )

        raise HTTPException(status_code=504, detail="MigeAPI video task timed out after 10 minutes")

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# DataEyesAI video provider - routes to 6 sub-platforms
# ---------------------------------------------------------------------------



async def _download_video_to_local(url: str, task_id: str, *, tenant_id=None, project_id=None) -> str:
    """Download a vendor video URL immediately because vendor URLs expire.
    O1: 落盘走 storage 抽象层(local→/uploads/...；oss→OSS)，按 tenant/project 分区。"""
    import httpx as _httpx
    from app.services.storage import get_storage
    async with _httpx.AsyncClient(timeout=300.0, trust_env=False, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept": "video/mp4,video/*,*/*",
    }) as client:
        resp = await client.get(url)
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Video download error ({resp.status_code}): {resp.text[:200]}")
        return await get_storage().save_bytes(
            resp.content, tenant_id=tenant_id, project_id=project_id,
            category="generated", ext="mp4", content_type="video/mp4",
        )

class DataEyesAIVideoProvider(VideoGenerationProvider):
    """DataEyesAI video generation — per-vendor adapters for six platforms.

    Each vendor uses different endpoint paths, auth, task_id field,
    status values, and video_url extraction. All polling is done
    in-memory (up to 10 minutes). For production, task state should
    be persisted to DB.

    Base URL: https://platform.dataeyes.ai
    """

    descriptor = VideoProviderDescriptor(
        name="dataeyes",
        display_name="DataEyesAI",
        description="DataEyesAI - Seedance/Kling/Hailuo/Vidu/Jimeng/Grok",
    )

    # Per-vendor adapter configuration
    VENDORS = {
        "seedance": {
            "route": "/seedance",
            "submit_path": "/api/v3/contents/generations/tasks",
            "build_submit_body": lambda model, prompt, duration, opts: {
                "model": model or "doubao-seedance-1-5-pro-251215",
                "content": [{"type": "text", "text": prompt}],
                "resolution": opts.get("resolution", "720p"),
                "ratio": opts.get("ratio", "adaptive"),
                "duration": int(duration or 5),
                "watermark": False,
            },
            "build_i2v_body": lambda model, prompt, duration, image_url, opts: {
                "model": model or "doubao-seedance-1-5-pro-251215",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url, "role": "first_frame"}},
                ],
                "resolution": opts.get("resolution", "720p"),
                "ratio": opts.get("ratio", "adaptive"),
                "duration": int(duration or 5),
                "watermark": False,
            },
            "parse_task_id": lambda data: data.get("id", ""),
            "poll_path": lambda task_id: f"/api/v3/contents/generations/tasks/{task_id}",
            "parse_status": lambda data: data.get("status", ""),
            "success_statuses": ("succeeded",),
            "parse_video_url": lambda data: (data.get("content") or {}).get("video_url", ""),
            "auth_scheme": "Bearer",
        },
        "kling": {
            "route": "/kling",
            "submit_path": "/v1/videos/text2video",
            "build_submit_body": lambda model, prompt, duration, opts: {
                "model_name": model or "kling-v2-6",
                "prompt": prompt,
                "negative_prompt": opts.get("negative_prompt", ""),
                "duration": str(int(duration or 5)),
                "mode": opts.get("mode", "std"),
                "aspect_ratio": opts.get("aspect_ratio", "16:9"),
                "sound": opts.get("sound", "off"),
            },
            "build_i2v_body": lambda model, prompt, duration, image_url, opts: {
                "model_name": model or "kling-v2-6",
                "image": image_url,
                "prompt": prompt,
                "duration": str(int(duration or 5)),
                "mode": opts.get("mode", "pro"),
                "aspect_ratio": opts.get("aspect_ratio", "16:9"),
            },
            "i2v_submit_path": "/v1/videos/image2video",
            "i2v_poll_path": lambda task_id: f"/v1/videos/image2video/{task_id}",
            "parse_task_id": lambda data: (data.get("data") or {}).get("task_id", ""),
            "poll_path": lambda task_id: f"/v1/videos/text2video/{task_id}",
            "parse_status": lambda data: (data.get("data") or {}).get("task_status", ""),
            "success_statuses": ("succeed",),
            "parse_video_url": lambda data: (
                ((data.get("data") or {}).get("task_result") or {}).get("videos", [{}])[0].get("url", "")
            ),
            "auth_scheme": "Bearer",
        },
        "hailuo": {
            "route": "/hailuo",
            "submit_path": "/v1/video_generation",
            "build_submit_body": lambda model, prompt, duration, opts: {
                "model": model or "MiniMax-Hailuo-2.3",
                "prompt": prompt,
                "duration": int(duration or 6),
                "resolution": opts.get("resolution", "768P"),
            },
            "build_i2v_body": lambda model, prompt, duration, image_url, opts: {
                "model": model or "MiniMax-Hailuo-2.3",
                "prompt": prompt,
                "duration": int(duration or 6),
                "resolution": opts.get("resolution", "768P"),
                "first_frame_image": image_url,
            },
            "parse_task_id": lambda data: data.get("task_id", ""),
            "poll_path": lambda task_id: f"/v1/video_generation/status/{task_id}",
            "parse_status": lambda data: data.get("status", ""),
            "success_statuses": ("completed", "succeeded"),
            "parse_video_url": lambda data: data.get("video_url") or data.get("download_url", ""),
            # Hailuo two-step: after status=completed, need to fetch download URL
            "download_path": lambda data: f"/v1/video_generation/download",
            "auth_scheme": "Bearer",
            "two_step": True,
        },
        "vidu": {
            "route": "/vidu",
            "submit_path": "/ent/v2/text2video",
            "build_submit_body": lambda model, prompt, duration, opts: {
                "model": model or "viduq3-pro",
                "prompt": prompt,
                "duration": int(duration or 5),
                "aspect_ratio": opts.get("aspect_ratio", "16:9"),
                "resolution": opts.get("resolution", "720p"),
            },
            "build_i2v_body": lambda model, prompt, duration, image_url, opts: {
                "model": model or "viduq3-pro",
                "prompt": prompt,
                "duration": int(duration or 5),
                "aspect_ratio": opts.get("aspect_ratio", "16:9"),
                "resolution": opts.get("resolution", "720p"),
                "images": [image_url],
            },
            "i2v_submit_path": "/ent/v2/img2video",
            "i2v_poll_path": lambda task_id: f"/ent/v2/tasks/{task_id}/creations",
            "parse_task_id": lambda data: data.get("task_id", ""),
            "poll_path": lambda task_id: f"/ent/v2/tasks/{task_id}/creations",
            "parse_status": lambda data: data.get("state") or ("success" if data.get("creations") else ""),
            "success_statuses": ("success",),
            "parse_video_url": lambda data: (
                data.get("video_url")
                or ((data.get("creations") or [{}])[0].get("url", ""))
            ),
            "auth_scheme": "Bearer",
        },
        "grok": {
            "route": "/grok",
            "submit_path": "/v1/videos/generations",
            "build_submit_body": lambda model, prompt, duration, opts: {
                "model": model or "grok-imagine-video",
                "prompt": prompt,
                "duration": int(duration or 8),
                "aspect_ratio": opts.get("aspect_ratio", "16:9"),
                "resolution": opts.get("resolution", "720p"),
            },
            "build_i2v_body": lambda model, prompt, duration, image_url, opts: {
                "model": model or "grok-imagine-video",
                "prompt": prompt,
                "duration": int(duration or 8),
                "aspect_ratio": opts.get("aspect_ratio", "16:9"),
                "resolution": opts.get("resolution", "720p"),
                "image": image_url,
            },
            "parse_task_id": lambda data: data.get("request_id", ""),
            "poll_path": lambda task_id: f"/v1/videos/{task_id}",
            "parse_status": lambda data: data.get("status", ""),
            "success_statuses": ("done",),
            "parse_video_url": lambda data: (data.get("video") or {}).get("url", ""),
            "auth_scheme": "Bearer",
        },
        "jimeng": {
            "route": "/jimeng",
            "submit_path": "?Action=CVSync2AsyncSubmitTask&Version=2022-08-31",
            "build_submit_body": lambda model, prompt, duration, opts: {
                "req_key": model or "jimeng_t2v_v30",
                "prompt": prompt,
                "seed": opts.get("seed", -1),
                "frames": opts.get("frames", 121),
                "aspect_ratio": opts.get("aspect_ratio", "16:9"),
            },
            "build_i2v_body": lambda model, prompt, duration, image_url, opts: {
                "req_key": "jimeng_i2v_first_v30",
                "prompt": prompt,
                "seed": opts.get("seed", -1),
                "frames": opts.get("frames", 121),
                "aspect_ratio": opts.get("aspect_ratio", "16:9"),
                "image_urls": [image_url],
            },
            "parse_task_id": lambda data: (data.get("data") or {}).get("task_id", ""),
            "poll_path": None,  # Jimeng uses POST for both submit and query
            "poll_body_builder": lambda task_id, model: {
                "req_key": model or "jimeng_t2v_v30",
                "task_id": task_id,
            },
            "parse_status": lambda data: (data.get("data") or {}).get("status", ""),
            "success_statuses": ("done",),
            "parse_video_url": lambda data: (data.get("data") or {}).get("video_url", ""),
            "auth_scheme": "Bearer",
        },
    }

    def __init__(self, api_key=None, base_url=None):
        import os as _os
        self._api_key = api_key or _os.getenv("DATAEYES_API_KEY", "")  # same key works for video with browser headers
        self._video_base = (base_url or _os.getenv("DATAEYES_VIDEO_BASE_URL", "https://platform.dataeyes.ai")).rstrip("/")
        self._client = None

    def _get_client(self, auth_scheme="Bearer"):
        """Get or create httpx client with correct auth scheme."""
        import httpx
        import os as _os2; import re as _re2
        if not self._api_key or len(self._api_key.strip()) < 10:
            self._api_key = _os2.getenv("DATAEYES_API_KEY", "")
        auth_header = f"{auth_scheme} {self._api_key}" if auth_scheme == "Token" else f"Bearer {self._api_key}"
        # Recreate client if auth scheme changed (Vidu)
        cache_key = getattr(self, "_client_auth", "")
        if self._client is None or cache_key != auth_scheme:
            self._client = httpx.AsyncClient(
                base_url=self._video_base,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                    "Accept": "application/json",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
                timeout=600.0,
                trust_env=False,
            )
            self._client_auth = auth_scheme
        return self._client

    @classmethod
    def _platform_for_model(cls, model: str) -> str:
        normalized = (model or "").lower()
        if "seedance" in normalized or "doubao-" in normalized:
            return "seedance"
        if "kling" in normalized:
            return "kling"
        if "vidu" in normalized:
            return "vidu"
        if "hailuo" in normalized or "minimax" in normalized:
            return "hailuo"
        if "grok" in normalized:
            return "grok"
        if "jimeng" in normalized:
            return "jimeng"
        return "seedance"

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        model = request.model or "doubao-seedance-1-5-pro-251215"
        duration = request.duration
        opts = request.options or {}
        # O1: 视频落盘按项目分区；tenant 由 project 派生(集中一处，覆盖下面两个 download 调用点)。
        from app.services.tenant_resolver import resolve_tenant_id
        _pid = opts.get("project_id") or getattr(request, "project_id", None)
        _tid = resolve_tenant_id(_pid)
        platform_name = opts.get("platform") or self._platform_for_model(model)
        vendor = self.VENDORS.get(platform_name)
        if not vendor:
            raise HTTPException(status_code=400, detail=f"Unknown platform: {platform_name}")

        route = vendor["route"]
        auth = vendor["auth_scheme"]
        client = self._get_client(auth)

        # ── Submit (I2V if first_frame_url provided) ──
        first_frame = opts.get("first_frame_url", "")
        if first_frame and "build_i2v_body" in vendor:
            submit_body = vendor["build_i2v_body"](model, request.prompt, duration, first_frame, opts)
            i2v_path = vendor.get("i2v_submit_path")
            submit_path = f"{route}{i2v_path}" if i2v_path else f"{route}{vendor['submit_path']}"
        else:
            submit_body = vendor["build_submit_body"](model, request.prompt, duration, opts)
            submit_path = f"{route}{vendor['submit_path']}"
        resp = await client.post(submit_path, json=submit_body)
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"DataEyesAI/{platform_name} submit error ({resp.status_code}): {resp.text[:300]}")
        data = resp.json()
        task_id = vendor["parse_task_id"](data)
        if not task_id:
            raise HTTPException(status_code=502, detail=f"DataEyesAI/{platform_name}: no task_id in response: {str(data)[:200]}")

        # ── Persist task to DB (P2-11) ──
        try:
            from app.db.session import SessionLocal
            from app.models.video_task import VideoTask
            db = SessionLocal()
            vt = VideoTask(
                vendor=platform_name,
                provider_task_id=task_id,
                model=model,
                status="submitted",
                prompt=request.prompt,
                duration=duration,
                options_json=json.dumps(opts) if opts else None,
                project_id=opts.get("project_id") or getattr(request, 'project_id', None),
                canvas_id=opts.get("canvas_id"),   # Phase C Step3b: 落回发起画布(缺省 None→默认画布)
            )
            db.add(vt)
            db.commit()
            db.close()
        except Exception as _persist_err:
            import logging as _logging
            _logging.getLogger("uvicorn.error").warning("VideoTask persist failed: %s", _persist_err)

        # ── Submit-only: 提交即返回,交后台 worker 轮询(异步出片) ──
        if opts.get("submit_only"):
            return VideoGenerationResult(
                provider="dataeyes", status="submitted",
                videos=[GeneratedVideo(url="", duration=duration, provider_asset_id=task_id)],
            )

        # ── Poll ──
        import asyncio
        poll_model = model  # needed for jimeng poll body
        for _ in range(120):
            await asyncio.sleep(5)

            # Jimeng uses POST for polling
            if platform_name == "jimeng":
                poll_path = f"{route}?Action=CVSync2AsyncGetResult&Version=2022-08-31"
                poll_body = vendor.get("poll_body_builder", lambda tid, m: {})(task_id, poll_model)
                poll_resp = await client.post(poll_path, json=poll_body)
            else:
                poll_path = f"{route}{vendor['poll_path'](task_id)}"
                # Hailuo two-step: after initial status, fetch download URL
                if platform_name == "hailuo" and vendor.get("two_step"):
                    poll_resp = await client.get(poll_path)
                    if poll_resp.status_code < 400:
                        pd = poll_resp.json()
                        st = vendor["parse_status"](pd)
                        if st in vendor["success_statuses"]:
                            file_id = pd.get("file_id", "")
                            if file_id:
                                dl_path = f"{route}{vendor.get('download_path', lambda d: '')(pd)}"
                                dl_body = {"file_id": file_id}
                                dl_resp = await client.post(dl_path, json=dl_body)
                                if dl_resp.status_code < 400:
                                    dl_data = dl_resp.json()
                                    video_url = vendor["parse_video_url"](dl_data) or dl_data.get("download_url", "")
                                    if video_url:
                                        local_url = await _download_video_to_local(video_url, task_id, tenant_id=_tid, project_id=_pid)
                                        return VideoGenerationResult(
                                            provider="dataeyes", status="succeeded",
                                            videos=[GeneratedVideo(url=local_url, duration=duration, provider_asset_id=task_id)]
                                        )
                    continue
                else:
                    poll_resp = await client.get(poll_path)

            if poll_resp.status_code >= 400:
                continue

            poll_data = poll_resp.json()
            status = vendor["parse_status"](poll_data)

            if status in vendor["success_statuses"]:
                video_url = vendor["parse_video_url"](poll_data)
                if not video_url:
                    raise HTTPException(status_code=502, detail=f"DataEyesAI/{platform_name}: {status} but no video URL")
                local_url = await _download_video_to_local(video_url, task_id, tenant_id=_tid, project_id=_pid)
                # Update DB on success
                try:
                    from app.db.session import SessionLocal
                    from app.models.video_task import VideoTask
                    db2 = SessionLocal()
                    vt = db2.query(VideoTask).filter(VideoTask.provider_task_id == task_id).first()
                    if vt:
                        vt.status = "succeeded"
                        vt.video_url = video_url
                        vt.local_path = local_url
                        db2.commit()
                    db2.close()
                except Exception:
                    pass
                return VideoGenerationResult(
                    provider="dataeyes", status="succeeded",
                    videos=[GeneratedVideo(url=local_url, duration=duration, provider_asset_id=task_id)]
                )
            elif status in ("failed", "FAILED", "ERROR", "expired", "not_found"):
                raise HTTPException(status_code=502, detail=f"DataEyesAI/{platform_name} {status}")

        raise HTTPException(status_code=504, detail=f"DataEyesAI/{platform_name} timed out after 10 minutes")


class VideoGenerationService:
    def __init__(self) -> None:
        self._providers: dict[str, VideoGenerationProvider] = {}

    def register(self, provider: VideoGenerationProvider) -> None:
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

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        provider = self._providers.get(request.provider)
        if provider is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown video provider: {request.provider}. "
                f"Available: {list(self._providers.keys())}",
            )
        result = await provider.generate(request)
        if isinstance(result, VideoGenerationResult):
            return result
        if isinstance(result, dict) and result.get("url"):
            return VideoGenerationResult(
                provider=request.provider,
                status="succeeded",
                videos=[GeneratedVideo(
                    url=result["url"],
                    duration=request.duration,
                    width=request.width,
                    height=request.height,
                    fps=request.fps,
                    provider_asset_id=result.get("task_id"),
                )],
            )
        return result


video_generation_service = VideoGenerationService()
video_generation_service.register(LocalPlaceholderVideoProvider())
video_generation_service.register(RunwayVideoProvider())
video_generation_service.register(PikaVideoProvider())
video_generation_service.register(LovartVideoProvider())
video_generation_service.register(MigeVideoProvider())
video_generation_service.register(DataEyesAIVideoProvider())