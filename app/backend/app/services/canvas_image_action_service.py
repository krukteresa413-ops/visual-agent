"""Canvas image action service for right-click image operations."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import httpx
from PIL import Image
from rembg import remove

UPLOAD_ROOT = Path("/opt/visual-agent/uploads")
GENERATED_DIR = UPLOAD_ROOT / "generated"


class CanvasImageActionService:
    """Pixel-based canvas image actions.

    Cutout must preserve the selected source image. It must not call
    text-to-image generation providers because that can create unrelated
    replacement images.
    """

    async def run(self, action: str, image_url: str, instruction: str = "", provider: str = "rembg", model: str | None = None, *, tenant_id: int | None = None, project_id: int | None = None) -> dict:
        if action == "cutout":
            return await self._run_cutout(image_url, tenant_id=tenant_id, project_id=project_id)
        raise ValueError(f"unsupported canvas image action: {action}")

    async def _run_cutout(self, image_url: str, *, tenant_id: int | None = None, project_id: int | None = None) -> dict:
        source_bytes = await self._read_source_image(image_url)
        subject = self._remove_background(source_bytes)
        subject_url, width, height = self._save_png(subject, tenant_id=tenant_id, project_id=project_id)
        return {
            "url": subject_url,
            "width": width,
            "height": height,
            "provider": "rembg",
            "raw": {"source_image_url": image_url},
        }

    def _remove_background(self, source_bytes: bytes) -> Image.Image:
        output_bytes = remove(source_bytes)
        return Image.open(BytesIO(output_bytes)).convert("RGBA")

    def _save_png(self, image: Image.Image, *, tenant_id: int | None = None, project_id: int | None = None) -> tuple[str, int, int]:
        # O1: 落盘走 storage 抽象层(sync helper，被 async _run_cutout 调)。
        from app.services.storage import get_storage
        image = image.convert("RGBA")
        url = get_storage().save_pil_sync(
            image, tenant_id=tenant_id, project_id=project_id, category="generated", fmt="PNG",
        )
        return url, image.width, image.height

    async def _read_source_image(self, image_url: str) -> bytes:
        if image_url.startswith("/uploads/"):
            local_path = (Path("/opt/visual-agent") / image_url.lstrip("/")).resolve()
            upload_root = UPLOAD_ROOT.resolve()
            if not local_path.is_relative_to(upload_root):
                raise ValueError("source image path is outside uploads")
            if not local_path.exists():
                raise FileNotFoundError(f"source image not found: {image_url}")
            return local_path.read_bytes()

        if image_url.startswith("http://") or image_url.startswith("https://"):
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(image_url)
                resp.raise_for_status()
                return resp.content

        raise ValueError("source image must be /uploads/... or http(s) URL")


canvas_image_action_service = CanvasImageActionService()
