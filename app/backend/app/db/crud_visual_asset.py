"""
Visual Asset Plan CRUD 操作。
"""
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.visual_asset_plan import VisualAssetPlan
from app.schemas.visual_asset_plan import VisualAssetPlanCreate


def create_visual_asset_plan(
    db: Session,
    plan: VisualAssetPlanCreate,
) -> VisualAssetPlan:
    db_plan = VisualAssetPlan(
        project_id=plan.project_id,
        main_image_json=plan.main_image_json,
        white_bg_json=plan.white_bg_json,
        scene_images_json=plan.scene_images_json,
        selling_points_json=plan.selling_points_json,
        video_scripts_json=plan.video_scripts_json,
        ad_material_json=plan.ad_material_json,
    )

    try:
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)
        return db_plan
    except IntegrityError as e:
        db.rollback()
        if "duplicate key" in str(e):
            raise ValueError(f"Visual asset plan already exists for project {plan.project_id}")
        raise
    except SQLAlchemyError:
        db.rollback()
        raise


def get_visual_asset_plan_by_project(db: Session, project_id: int):
    return (
        db.query(VisualAssetPlan)
        .filter(VisualAssetPlan.project_id == project_id)
        .first()
    )
