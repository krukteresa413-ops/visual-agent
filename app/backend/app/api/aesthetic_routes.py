"""
Aesthetic API — pairwise comparison + multi-image ranking.

POST /api/v1/aesthetic/compare   — compare two images
POST /api/v1/aesthetic/rank      — rank multiple images
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.aesthetic_ranker import AestheticRanker

router = APIRouter(prefix="/api/v1", tags=["aesthetic"])

_ranker: Optional[AestheticRanker] = None


def get_ranker() -> AestheticRanker:
    global _ranker
    if _ranker is None:
        _ranker = AestheticRanker()
    return _ranker


# ── Schemas ────────────────────────────────────────────────────

class CompareRequest(BaseModel):
    image_a: str  # file path on server
    image_b: str
    brief: dict = {}


class RankRequest(BaseModel):
    image_paths: list[str]
    brief: dict = {}


# ── Endpoints ──────────────────────────────────────────────────

@router.post("/aesthetic/compare")
def compare_images(req: CompareRequest):
    """Compare two images against brief requirements.

    Returns winner (A/B/tie), reasoning, and scores.
    When brief has style info, uses vision LLM for aesthetic judgment.
    Otherwise falls back to technical quality (MUSIQ).
    """
    ranker = get_ranker()
    return ranker.compare_pair(req.image_a, req.image_b, req.brief)


@router.post("/aesthetic/rank")
def rank_images(req: RankRequest):
    """Rank multiple images by aesthetic quality.

    Returns ordered list with scores and per-image quality metrics.
    """
    ranker = get_ranker()
    return ranker.rank_images(req.image_paths, req.brief)


@router.get("/aesthetic/health")
def aesthetic_health():
    """Check aesthetic ranker status."""
    ranker = get_ranker()
    return {
        "status": "ok",
        "musiq_loaded": ranker._musiq_metric is not None,
    }
