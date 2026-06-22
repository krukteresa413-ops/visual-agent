"""Video provider 边界：re-export 现有 app.services.video_generation_service，行为不变。
第一小步仅转发抽象基类与 6 个 video provider，不移动实现、不改现有 import 面。
（video_polling_worker ↔ DataEyesAIVideoProvider 的耦合迁移留第二小步。）"""
from app.services.video_generation_service import (
    VideoGenerationProvider,
    LocalPlaceholderVideoProvider,
    RunwayVideoProvider,
    PikaVideoProvider,
    LovartVideoProvider,
    MigeVideoProvider,
    DataEyesAIVideoProvider,
)

__all__ = [
    "VideoGenerationProvider",
    "LocalPlaceholderVideoProvider",
    "RunwayVideoProvider",
    "PikaVideoProvider",
    "LovartVideoProvider",
    "MigeVideoProvider",
    "DataEyesAIVideoProvider",
]
