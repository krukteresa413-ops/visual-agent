"""Image generation request/response models."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


ImageProviderKind = Literal["local", "pollinations", "comfyui", "stability", "dalle", "lovart", "mige", "dataeyes"]


class ImageGenerationRequest(BaseModel):
    """Unified request for any image generation provider."""

    provider: ImageProviderKind = "local"
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = Field(default=1024, ge=64, le=2048)
    height: int = Field(default=1024, ge=64, le=2048)
    seed: Optional[int] = None
    model: Optional[str] = None
    reference_image_url: Optional[str] = None
    options: dict[str, Any] = Field(default_factory=dict)

    # OSS 多租户分区(Phase O1)：落盘 key 用 t/{tenant_id}/p/{project_id}/{category}/...
    # 端点/agent 构造请求时带上作用域内的 project_id；tenant_id 通常由
    # ImageGenerationService.generate 从 project_id 集中派生(见 tenant_resolver)。
    # 缺失 → None → storage 归 _misc/(有租户无项目)或 shared/(无租户)，合法降级。
    project_id: Optional[int] = None
    tenant_id: Optional[int] = None
    category: Optional[str] = None  # None → provider 落盘按 "generated"；字体传 "font"


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
