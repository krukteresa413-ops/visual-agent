"""Image generation API routes."""
from fastapi import APIRouter, Query

from app.models.image_generation_model import ImageGenerationRequest, ImageGenerationResult
from app.services.image_generation_service import image_generation_service
from app.services.provider_inventory import build_inventory

router = APIRouter(prefix="/api/v1/generation", tags=["image-generation"])


@router.get("/providers")
async def list_providers() -> dict:
    return {"providers": image_generation_service.list_providers()}


@router.get("/models")
async def list_models(modality: str | None = Query(default=None, pattern="^(image|video)$")) -> dict:
    models = [item.to_camel() for item in build_inventory(modality=modality)]
    return {
        "tabs": [
            {"kind": "image", "label": "Image"},
            {"kind": "video", "label": "Video"},
            {"kind": "3d", "label": "3D"},
        ],
        "models": models,
    }


@router.post("/image", response_model=ImageGenerationResult)
async def generate_image(request: ImageGenerationRequest) -> ImageGenerationResult:
    return await image_generation_service.generate(request)
