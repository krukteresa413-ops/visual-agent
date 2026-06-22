"""
Vision / Image Recognition Service using DataEyesAI.

Supports: image description, object detection, text extraction,
style analysis, quality assessment, and custom prompts.

Provider: DataEyesAI (OpenAI-compatible vision API)
Models: configured vision-capable models
"""
import os
import base64
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class VisionService:
    """General-purpose image recognition via vision LLM."""

    def __init__(self):
        self._api_key = os.getenv("DATAEYES_API_KEY", "")
        self._base_url = os.getenv("DATAEYES_BASE_URL", "https://cloud.dataeyes.ai/v1").rstrip("/")
        self._default_model = os.getenv("VISION_MODEL", "gpt-4o")

    def _image_to_base64(self, image_path_or_url: str) -> str:
        """Convert image to data URL for vision API.

        Supports: local file paths, http URLs, already-base64 data URLs.
        """
        if image_path_or_url.startswith("data:"):
            return image_path_or_url
        if image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
            return image_path_or_url

        # Local file
        path = image_path_or_url
        app_root = Path("/opt/visual-agent").resolve()
        upload_root = (app_root / "uploads").resolve()
        if path.startswith("/uploads/") or path.startswith("uploads/"):
            relative = path.lstrip("/")
            target = (app_root / relative).resolve()
            if upload_root not in (target, *target.parents):
                raise ValueError("image path is outside uploads")
        elif not os.path.isabs(path):
            target = (app_root / path.lstrip("/")).resolve()
            if app_root not in (target, *target.parents):
                raise ValueError("invalid image path")
        else:
            target = Path(path).resolve()

        with open(target, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")

        ext = target.suffix.lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                     ".webp": "image/webp", ".gif": "image/gif"}
        mime = mime_map.get(ext, "image/png")
        return f"data:{mime};base64,{img_data}"

    async def analyze(
        self,
        images: list[str],
        prompt: str = "Describe this image in detail.",
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> dict:
        """Analyze one or more images with a custom prompt.

        Args:
            images: List of image paths, URLs, or base64 data URLs
            prompt: What to ask about the images
            model: Vision model name (default: gpt-4o)
            max_tokens: Max response tokens
            temperature: Response creativity (0.0-1.0)

        Returns:
            {"success": True, "content": "...", "model": "...", "usage": {...}}
        """
        import httpx

        # Build OpenAI Responses multimodal content array
        content = [{"type": "input_text", "text": prompt}]
        for img in images:
            data_url = self._image_to_base64(img)
            content.append({
                "type": "input_image",
                "image_url": data_url,
                "detail": "auto",
            })

        payload = {
            "model": model or self._default_model,
            "input": [{"role": "user", "content": content}],
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self._base_url}/responses",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if resp.status_code != 200:
            logger.error(f"Vision API error {resp.status_code}: {resp.text[:300]}")
            return {"success": False, "error": f"API error {resp.status_code}", "detail": resp.text[:300]}

        data = resp.json()
        content_text = self._extract_response_text(data)
        usage = data.get("usage", {})

        return {
            "success": True,
            "content": content_text,
            "model": data.get("model", ""),
            "usage": {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }

    def _extract_response_text(self, data: dict) -> str:
        """Extract text from OpenAI Responses API output."""
        if data.get("output_text"):
            return data["output_text"]

        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    return content.get("text", "")

        return ""

    async def describe(self, image: str, language: str = "zh") -> dict:
        """Describe an image in natural language."""
        prompt = "请详细描述这张图片的内容、风格、构图和关键元素。" if language == "zh" else "Describe this image in detail including content, style, composition, and key elements."
        return await self.analyze([image], prompt)

    async def extract_text(self, image: str) -> dict:
        """Extract all visible text from an image (OCR via vision)."""
        prompt = "Extract ALL text visible in this image. Return the text exactly as it appears, preserving layout and formatting where possible. If there is no text, say 'NO_TEXT'."
        return await self.analyze([image], prompt, max_tokens=2048)

    async def assess_quality(self, image: str) -> dict:
        """Assess image quality: sharpness, lighting, composition."""
        prompt = """Assess this image's technical quality. Rate each dimension 0-100 and explain briefly in Chinese:
1. 清晰度 (sharpness)
2. 曝光 (exposure/lighting)
3. 构图 (composition)
4. 色彩 (color balance)
5. 噪点 (noise level)

Return JSON:
{"sharpness": 0-100, "exposure": 0-100, "composition": 0-100, "color": 0-100, "noise": 0-100, "overall": 0-100, "verdict": "一句话总结"}"""
        return await self.analyze([image], prompt, max_tokens=512)

    async def detect_objects(self, image: str) -> dict:
        """Detect and list objects in an image."""
        prompt = """List all objects, people, text, logos, and notable elements visible in this image. Be specific and thorough. Return as JSON: {"objects": [], "people": [], "text_elements": [], "scene_type": "..."}"""
        return await self.analyze([image], prompt, max_tokens=1024)

    async def compare_images(self, image_a: str, image_b: str, criteria: str = "") -> dict:
        """Compare two images and determine which is better."""
        prompt = f"""Compare these two images (Image A first, then Image B).

Criteria: {criteria or 'overall visual quality, composition, and appeal'}

For each dimension below, score both 0-100 and explain in Chinese (1-2 sentences):
1. 风格匹配度
2. 视觉吸引力
3. 构图质量
4. 技术质量
5. 整体评分

Return JSON:
{{"winner": "A" or "B", "verdict": "一句话总结", "scores": {{"A": 0-100, "B": 0-100}}, "dimensions": [{{"name": "...", "score_a": 0-100, "score_b": 0-100, "note": "..."}}]}}"""
        return await self.analyze([image_a, image_b], prompt, max_tokens=1024)


# Global singleton
vision_service = VisionService()
