from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from app.services.image_generation_service import image_generation_service
from app.services.video_generation_service import video_generation_service

Source = Literal["production", "benchmark", "experimental", "local"]
Modality = Literal["image", "video"]

SOURCE_BY_PROVIDER: dict[str, Source] = {
    "lovart": "benchmark",
    "local": "local",
    "pollinations": "experimental",
}

PRODUCTION_PROVIDERS = {"dataeyes", "mige", "dalle", "openai", "runway", "pika"}

ENV_BY_PROVIDER = {
    "dataeyes": "DATAEYES_API_KEY",
    "mige": "MIGEAPI_API_KEY",
    "dalle": "OPENAI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "runway": "RUNWAY_API_KEY",
    "pika": "PIKA_API_KEY",
    "lovart": "LOVART_API_KEY",
}


@dataclass(frozen=True)
class ProviderInventoryItem:
    model_key: str
    provider: str
    modality: Modality
    display_name: str
    available: bool
    configured: bool
    tested_at: str | None
    cost_estimate: float | None
    notes: str | None
    source: Source
    production_usable: bool

    def to_camel(self) -> dict:
        return {
            "modelKey": self.model_key,
            "provider": self.provider,
            "modality": self.modality,
            "displayName": self.display_name,
            "available": self.available,
            "configured": self.configured,
            "testedAt": self.tested_at,
            "costEstimate": self.cost_estimate,
            "notes": self.notes,
            "source": self.source,
            "productionUsable": self.production_usable,
            "id": self.model_key,
            "kind": self.modality,
            "label": self.display_name,
            "desc": self.notes,
        }


def _provider_name(provider) -> str:
    return getattr(getattr(provider, "descriptor", None), "name", "").strip()


def _provider_display_name(provider, name: str) -> str:
    descriptor = getattr(provider, "descriptor", None)
    return (getattr(descriptor, "display_name", None) or getattr(descriptor, "description", None) or name).strip()


def _source_for(provider_name: str) -> Source:
    for prefix, source in SOURCE_BY_PROVIDER.items():
        if provider_name.startswith(prefix):
            return source
    if provider_name in PRODUCTION_PROVIDERS:
        return "production"
    return "experimental"


def _configured(provider_name: str, source: Source) -> bool:
    if source == "local":
        return True
    env_name = ENV_BY_PROVIDER.get(provider_name)
    if not env_name:
        return False
    return bool(os.getenv(env_name, ""))


def _item(provider, modality: Modality) -> ProviderInventoryItem | None:
    name = _provider_name(provider)
    if not name:
        return None
    source = _source_for(name)
    configured = _configured(name, source)
    production_usable = source == "production" and configured
    available = configured and production_usable
    if source in {"benchmark", "experimental", "local"}:
        available = source == "local"
        production_usable = False
    return ProviderInventoryItem(
        model_key=f"{name}:{modality}",
        provider=name,
        modality=modality,
        display_name=_provider_display_name(provider, name),
        available=available,
        configured=configured,
        tested_at=None,
        cost_estimate=None,
        notes=None if source == "production" else f"{source} provider",
        source=source,
        production_usable=production_usable,
    )


def build_inventory(modality: Modality | None = None) -> list[ProviderInventoryItem]:
    items: list[ProviderInventoryItem] = []
    if modality in (None, "image"):
        for provider in image_generation_service.registered_providers():
            item = _item(provider, "image")
            if item:
                items.append(item)
    if modality in (None, "video"):
        for provider in video_generation_service.registered_providers():
            item = _item(provider, "video")
            if item:
                items.append(item)
    return items
