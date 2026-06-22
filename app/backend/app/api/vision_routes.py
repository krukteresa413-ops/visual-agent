"""
Vision / Image Recognition API routes.
"""
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
