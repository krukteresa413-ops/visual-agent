"""Image generation request/response models."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


ImageProviderKind = Literal["local", "pollinations", "comfyui", "stability", "dalle"]


class ImageGenerationRequest(BaseModel):
    """Unified request for any image generation provider."""

    provider: ImageProviderKind = "local"
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = Field(default=1024, ge=64, le=2048)
    height: int = Field(default=1024, ge=64, le=2048)
    seed: Optional[int] = None
    model: Optional[str] = None
    options: dict[str, Any] = Field(default_factory=dict)


class GeneratedImage(BaseModel):
    """A single generated image result."""

    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    seed: Optional[int] = None
    provider_asset_id: Optional[str] = None


class ImageGenerationResult(BaseModel):
    """Unified generation result."""

    provider: str
    status: Literal["succeeded", "failed"]
    images: list[GeneratedImage] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)
