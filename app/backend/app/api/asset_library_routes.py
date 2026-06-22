"""Auto Asset Library API — per-project auto-categorized assets (P4.3)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import SessionLocal

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


class AssetItem(BaseModel):
    id: int
    type: str  # image, video, graphic, doc
    label: str
    url: Optional[str] = None
    preview: Optional[str] = None
    text: Optional[str] = None
    created_at: Optional[str] = None


class AssetLibraryResponse(BaseModel):
    project_id: int
    project_name: str
    categories: dict[str, list[AssetItem]]  # type → assets
    total: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=AssetLibraryResponse)
def get_asset_library(
    project_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Return auto-categorized assets for a project."""
    from app.models.project import Project
    from app.models.visual_asset import VisualAsset

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all generations for this project
    generations = (
        db.query(VisualAsset)
        .filter(VisualAsset.project_id == project_id)
        .order_by(VisualAsset.created_at.desc())
        .all()
    )

    categories: dict[str, list[AssetItem]] = {
        "images": [],
        "videos": [],
        "graphics": [],
        "docs": [],
    }

    asset_id = 0
    for gen in generations:
        try:
            plan = gen.asset_plan if gen.asset_plan else {}
        except Exception:
            plan = {}

        created = gen.created_at.isoformat() if gen.created_at else None

        # Images
        for img_key in ["main_image", "white_bg"]:
            img = plan.get(img_key, {})
            if isinstance(img, dict) and img.get("url"):
                asset_id += 1
                categories["images"].append(AssetItem(
                    id=asset_id, type="image", label=img_key,
                    url=img["url"], created_at=created,
                ))

        # Scene images
        scenes = plan.get("scene_images", [])
        if isinstance(scenes, list):
            for scene in scenes:
                if isinstance(scene, dict) and scene.get("url"):
                    asset_id += 1
                    categories["images"].append(AssetItem(
                        id=asset_id, type="image", label="scene_image",
                        url=scene["url"], created_at=created,
                    ))

        # Videos
        for vid_key in ["video_scripts"]:
            vid = plan.get(vid_key, {})
            if isinstance(vid, dict) and vid:
                asset_id += 1
                categories["videos"].append(AssetItem(
                    id=asset_id, type="video", label=vid_key,
                    preview=vid.get("preview", ""), created_at=created,
                ))

        # Graphics / copy
        for copy_key in ["selling_points", "ad_material"]:
            copy_data = plan.get(copy_key, {})
            if isinstance(copy_data, dict) and copy_data:
                asset_id += 1
                categories["graphics"].append(AssetItem(
                    id=asset_id, type="graphic", label=copy_key,
                    text=str(copy_data)[:200], created_at=created,
                ))

    total = sum(len(v) for v in categories.values())

    return AssetLibraryResponse(
        project_id=project_id,
        project_name=project.name,
        categories=categories,
        total=total,
    )
