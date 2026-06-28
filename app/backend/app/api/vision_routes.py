"""
Vision / Image Recognition API routes.
"""
import json
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.vision_service import vision_service

router = APIRouter(prefix="/api/v1/vision", tags=["vision"])


class VisionRequest(BaseModel):
    images: list[str]  # paths, URLs, or base64 data URLs
    prompt: str = "Describe this image in detail."
    model: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.3


class VisionResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None
    usage: Optional[dict] = None


@router.post("/analyze", response_model=VisionResponse)
async def analyze_images(req: VisionRequest):
    """Analyze images with a custom prompt using vision AI."""
    if not req.images:
        raise HTTPException(status_code=400, detail="No images provided")
    return await vision_service.analyze(
        images=req.images,
        prompt=req.prompt,
        model=req.model,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )


@router.post("/describe")
async def describe_image(image: str, language: str = "zh"):
    """Describe an image in natural language."""
    return await vision_service.describe(image, language)


@router.post("/ocr")
async def extract_text(image: str):
    """Extract text from an image (vision-based OCR)."""
    return await vision_service.extract_text(image)


@router.post("/quality")
async def assess_quality(image: str):
    """Assess image technical quality."""
    return await vision_service.assess_quality(image)


@router.post("/objects")
async def detect_objects(image: str):
    """Detect objects in an image."""
    return await vision_service.detect_objects(image)


# ── 图二:识别图片内容 -> 自动填充问卷基础字段 ──
class BriefSuggestRequest(BaseModel):
    image_url: str


def _parse_loose_json(text: str) -> dict:
    """从模型输出里宽松提取 JSON 对象(容忍 ```json 围栏与多余文字)。"""
    if not text:
        return {}
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        m = re.search(r"\{.*\}", cleaned, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return {}
    return {}


_BRIEF_SUGGEST_PROMPT = (
    "你是电商营销视觉分析助手。仔细观察这张图片(产品图或营销图),推断下列字段,"
    "只返回 JSON(不要代码块、不要多余文字、不要解释):\n"
    '{"product_name":"产品名,简短","category":"从[美妆护肤,食品饮料,3C数码,服饰鞋包,'
    '家居家电,母婴亲子,宠物用品,其他]里选最贴近的一个","target_audience":"目标受众,简短",'
    '"brand_style":"画面风格,简短","selling_points":["卖点1","卖点2","卖点3"]}\n'
    "看不出的字段用空字符串或空数组。"
)


@router.post("/brief-suggest")
async def brief_suggest(req: BriefSuggestRequest):
    """识别图片内容,返回可预填问卷的基础 brief 字段(尽力而为,失败返回空)。"""
    if not req.image_url:
        raise HTTPException(status_code=400, detail="image_url is required")
    result = await vision_service.analyze(
        images=[req.image_url],
        prompt=_BRIEF_SUGGEST_PROMPT,
        max_tokens=400,
        temperature=0.3,
    )
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "vision unavailable"), "fields": {}}
    fields = _parse_loose_json(result.get("content", "") or "")
    allowed = {"product_name", "category", "target_audience", "brand_style", "selling_points"}
    fields = {k: v for k, v in fields.items() if k in allowed and v not in (None, "", [])}
    return {"success": True, "fields": fields}
