"""Video generation API routes."""
from fastapi import APIRouter

from app.models.video_generation_model import VideoGenerationRequest, VideoGenerationResult
from app.services.video_generation_service import video_generation_service

router = APIRouter(prefix="/api/v1/generation", tags=["video-generation"])


@router.get("/video-providers")
async def list_video_providers() -> dict:
    return {"providers": video_generation_service.list_providers()}


@router.post("/video", response_model=VideoGenerationResult)
async def generate_video(request: VideoGenerationRequest) -> VideoGenerationResult:
    return await video_generation_service.generate(request)
