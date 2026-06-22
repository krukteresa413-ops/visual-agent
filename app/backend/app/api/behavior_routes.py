"""
Behavior API — user action tracking + calibration analysis.

POST /api/v1/behavior/event            — record user action
GET  /api/v1/behavior/events/{pid}     — query events
GET  /api/v1/behavior/calibrate/{pid}  — calibration report
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

from app.services.behavior_tracker import BehaviorTracker

router = APIRouter(prefix="/api/v1", tags=["behavior"])

_tracker: Optional[BehaviorTracker] = None


def get_tracker() -> BehaviorTracker:
    global _tracker
    if _tracker is None:
        _tracker = BehaviorTracker()
    return _tracker


# ── Schemas ────────────────────────────────────────────────────

class BehaviorEventRequest(BaseModel):
    project_id: int
    event_type: str  # viewed, exported, modified, regenerated, finalized
    generation_id: Optional[int] = None
    image_path: Optional[str] = None
    ai_score: Optional[float] = None
    metadata: Optional[dict] = None


# ── Endpoints ──────────────────────────────────────────────────

@router.post("/behavior/event")
def record_event(req: BehaviorEventRequest):
    """Record a user behavior event for calibration tracking."""
    tracker = get_tracker()
    return tracker.record_event(
        project_id=req.project_id,
        event_type=req.event_type,
        generation_id=req.generation_id,
        image_path=req.image_path,
        ai_score=req.ai_score,
        metadata=req.metadata,
    )


@router.get("/behavior/events/{project_id}")
def get_events(
    project_id: int,
    event_type: Optional[str] = Query(None),
    limit: int = Query(100),
):
    """Query behavior events for a project."""
    tracker = get_tracker()
    return {
        "project_id": project_id,
        "events": tracker.get_project_events(project_id, event_type, limit),
    }


@router.get("/behavior/calibrate/{project_id}")
def calibrate(project_id: int):
    """Compare AI aesthetic predictions against actual user behavior."""
    tracker = get_tracker()
    return tracker.calibrate(project_id)
