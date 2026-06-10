"""Canvas routes — asset grouping and modification."""
from fastapi import APIRouter, Depends
from app.api.canvas import group_assets_by_type

router = APIRouter(prefix="/api/v1", tags=["canvas"])


def get_latest_asset_for_project(project_id: int):
    """Fetch the latest VisualAsset for a project. Mockable for tests."""
    from app.db.session import SessionLocal
    from app.models.visual_asset import VisualAsset
    db = SessionLocal()
    try:
        return db.query(VisualAsset).filter(
            VisualAsset.project_id == project_id
        ).order_by(VisualAsset.created_at.desc()).first()
    finally:
        db.close()


@router.get("/projects/{project_id}/canvas")
def get_canvas(project_id: int):
    """Return assets grouped by type for canvas display."""
    asset = get_latest_asset_for_project(project_id)
    if not asset:
        return {"groups": []}
    groups = group_assets_by_type(asset.asset_plan)
    return {"groups": groups}
