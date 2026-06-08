"""Video generation request/response models."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


VideoProviderKind = Literal["local", "runway", "pika", "kling", "sora", "luma", "hailuo", "minimax"]


class VideoGenerationRequest(BaseModel):
    provider: VideoProviderKind = "local"
    prompt: str
    negative_prompt: Optional[str] = None
    duration: float = Field(default=15.0, ge=5.0, le=60.0)
    fps: int = Field(default=24, ge=12, le=60)
    width: int = Field(default=1024, ge=512, le=1920)
    height: int = Field(default=576, ge=256, le=1080)
    seed: Optional[int] = None
    model: Optional[str] = None
    options: dict[str, Any] = Field(default_factory=dict)


class GeneratedVideo(BaseModel):
    url: str
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None
    provider_asset_id: Optional[str] = None


class VideoGenerationResult(BaseModel):
    provider: str
    status: Literal["succeeded", "failed"]
    videos: list[GeneratedVideo] = Field(default_factory=list)
