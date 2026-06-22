"""Campaign API — serve campaign status and results for Agent Canvas (P4.2)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import SessionLocal

router = APIRouter(prefix="/api/v1/campaign", tags=["campaign"])


class StepInfo(BaseModel):
    step: str
    label: str
    status: str
    progress: int
    output: Optional[dict] = None


class CampaignResponse(BaseModel):
    project_id: int
    project_name: str
    status: str
    steps: list[StepInfo]
    assets: list[dict]


STEP_LABELS = {
    "creative_brief": "创意简报",
    "mood_direction": "风格定位",
    "concept_generation": "概念生成",
    "refinement": "精修优化",
    "adapt_extend": "多格式适配",
    "export": "导出交付",
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{project_id}", response_model=CampaignResponse)
def get_campaign_status(project_id: int, db: Session = Depends(get_db)):
    """Return campaign pipeline status and generated assets for a project."""
    from app.models.project import Project
    from app.models.visual_asset import VisualAsset

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get latest generation
    latest = (
        db.query(VisualAsset)
        .filter(VisualAsset.project_id == project_id)
        .order_by(VisualAsset.created_at.desc())
        .first()
    )

    # Determine pipeline steps from asset_plan
    steps = []
    try:
        plan = latest.asset_plan if latest and latest.asset_plan else {}
        gen_progress = plan.get("generation_progress", {})
    except Exception:
        plan = {}
        gen_progress = {}

    pipeline_keys = ["creative_brief", "mood_direction", "concept_generation", "refinement", "adapt_extend", "export"]

    for i, key in enumerate(pipeline_keys):
        done = gen_progress.get(key, False) if gen_progress else False
        steps.append(StepInfo(
            step=key,
            label=STEP_LABELS.get(key, key),
            status="completed" if done else ("in_progress" if i == 0 or (i > 0 and gen_progress.get(pipeline_keys[i-1], False)) else "pending"),
            progress=100 if done else 0,
            output=plan.get(key) if plan else None,
        ))

    # Extract assets from plan
    assets = []
    if plan:
        for img_key in ["main_image", "white_bg", "scene_images"]:
            img_data = plan.get(img_key, {})
            if isinstance(img_data, dict) and img_data.get("url"):
                assets.append({"type": "image", "label": img_key, "url": img_data["url"]})
        for vid_key in ["video_scripts"]:
            vid = plan.get(vid_key, {})
            if isinstance(vid, dict) and vid:
                assets.append({"type": "video", "label": vid_key, "preview": vid.get("preview", "")})
        for copy_key in ["selling_points", "ad_material"]:
            copy_data = plan.get(copy_key, {})
            if isinstance(copy_data, dict) and copy_data:
                assets.append({"type": "copy", "label": copy_key, "text": str(copy_data)[:100]})

    status = "in_progress"
    if all(s.status == "completed" for s in steps):
        status = "completed"
    elif any(s.status == "failed" for s in steps):
        status = "failed"

    return CampaignResponse(
        project_id=project_id,
        project_name=project.name,
        status=status,
        steps=steps,
        assets=assets,
    )
