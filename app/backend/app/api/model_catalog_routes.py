"""Curated model catalog API for canvas model selector."""
from fastapi import APIRouter

from app.config.model_registry import enabled_catalog

router = APIRouter(prefix="/api/v1/models", tags=["model-catalog"])


@router.get("/catalog")
def get_models_catalog() -> dict:
    return enabled_catalog()
