"""History API — paginated generation history with filters (P3.2)."""
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional

from app.db.session import SessionLocal

router = APIRouter(prefix="/api/v1/history", tags=["history"])


class HistoryItem(BaseModel):
    id: int
    project_name: str
    model_used: str
    generation_seconds: Optional[int]
    created_at: Optional[str]
    main_image_url: Optional[str]


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=HistoryResponse)
def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Return paginated generation history, optionally filtered by project."""
    from app.models.visual_asset import VisualAsset
    from app.models.project import Project

    base_query = db.query(
        VisualAsset.id,
        VisualAsset.model_used,
        VisualAsset.generation_seconds,
        VisualAsset.created_at,
        VisualAsset.asset_plan_json,
        Project.name.label("project_name"),
    ).join(Project, VisualAsset.project_id == Project.id, isouter=True)

    if project_id:
        base_query = base_query.filter(VisualAsset.project_id == project_id)

    total = base_query.count()
    offset = (page - 1) * page_size

    records = (
        base_query
        .order_by(VisualAsset.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = []
    for r in records:
        # Derive main image URL from asset_plan_json (already loaded — no N+1)
        main_image_url = None
        try:
            plan = json.loads(r.asset_plan_json) if r.asset_plan_json else {}
            main_img = plan.get("main_image", {})
            url = main_img.get("url", "") if isinstance(main_img, dict) else ""
            if url:
                main_image_url = url
        except Exception:
            pass

        items.append(HistoryItem(
            id=r.id,
            project_name=r.project_name or "未知",
            model_used=r.model_used or "unknown",
            generation_seconds=r.generation_seconds,
            created_at=r.created_at.isoformat() if r.created_at else None,
            main_image_url=main_image_url,
        ))

    return HistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
