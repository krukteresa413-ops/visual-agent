"""Video generation request/response models."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


VideoProviderKind = Literal["local", "runway", "pika", "kling", "sora", "luma", "hailuo", "minimax", "lovart", "mige", "dataeyes"]


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


# ---------------------------------------------------------------------------
# P2.2: Storyboard / Keyframe / Subtitle models
# ---------------------------------------------------------------------------

class StoryboardShot(BaseModel):
    """A single shot in a storyboard."""
    shot_number: int
    description: str
    visual_prompt: str  # prompt for keyframe image generation
    camera_angle: str = "medium"
    duration: float = 5.0
    transition: str = "cut"
    dialogue: str = ""


class Storyboard(BaseModel):
    """Full storyboard with shots for a video brief."""
    title: str
    shots: list[StoryboardShot]
    total_duration: float


class Keyframe(BaseModel):
    """A keyframe image associated with a storyboard shot."""
    shot_number: int
    image_url: str
    prompt: str


class SubtitleEntry(BaseModel):
    """A single timed subtitle entry."""
    start_time: float
    end_time: float
    text: str


class Subtitle(BaseModel):
    """Full subtitle track with language and entries."""
    language: str
    entries: list[SubtitleEntry]
