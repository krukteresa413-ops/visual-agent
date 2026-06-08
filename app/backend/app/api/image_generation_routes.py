"""Image generation API routes."""
from fastapi import APIRouter

from app.models.image_generation_model import ImageGenerationRequest, ImageGenerationResult
from app.services.image_generation_service import image_generation_service

router = APIRouter(prefix="/api/v1/generation", tags=["image-generation"])


@router.get("/providers")
async def list_providers() -> dict:
    return {"providers": image_generation_service.list_providers()}


@router.post("/image", response_model=ImageGenerationResult)
async def generate_image(request: ImageGenerationRequest) -> ImageGenerationResult:
    return await image_generation_service.generate(request)
