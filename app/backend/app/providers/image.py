"""Image provider 边界：re-export 现有 app.services.image_generation_service，行为不变。
第一阶段仅转发抽象基类与 6 个 image provider，不移动实现、不改现有 import 面。"""
from app.services.image_generation_service import (
    ImageGenerationProvider,
    LocalPlaceholderProvider,
    PollinationsProvider,
    OpenAIImageProvider,
    LovartImageProvider,
    MigeProvider,
    DataEyesAIImageProvider,
)

__all__ = [
    "ImageGenerationProvider",
    "LocalPlaceholderProvider",
    "PollinationsProvider",
    "OpenAIImageProvider",
    "LovartImageProvider",
    "MigeProvider",
    "DataEyesAIImageProvider",
]
