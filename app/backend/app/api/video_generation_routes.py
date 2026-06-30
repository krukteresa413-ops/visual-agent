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


@router.get("/video-task/{task_id}")
async def video_task_status(task_id: str) -> dict:
    """查询视频任务状态(供前端轮询出片完成)。"""
    from app.db.session import SessionLocal
    from app.models.video_task import VideoTask
    db = SessionLocal()
    try:
        vt = (
            db.query(VideoTask)
            .filter(VideoTask.provider_task_id == task_id)
            .order_by(VideoTask.id.desc())
            .first()
        )
        if not vt:
            return {"status": "unknown", "url": None}
        return {"status": vt.status, "url": vt.local_path or vt.video_url, "error": vt.error_message, "vendor": vt.vendor}
    finally:
        db.close()
