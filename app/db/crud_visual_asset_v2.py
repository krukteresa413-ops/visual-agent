"""
视觉素材生成结果 CRUD。
Simplicity First：只实现 PRD 真正需要的操作。
"""
import json
from typing import Optional
from sqlalchemy.orm import Session
from app.models.visual_asset import VisualAsset


def save_asset_plan(
    db: Session,
    project_id: int,
    asset_plan: dict,
    brief_id: Optional[int] = None,
    model_used: Optional[str] = None,
    generation_seconds: Optional[int] = None,
) -> VisualAsset:
    """保存一次完整的六类素材生成结果"""
    record = VisualAsset(
        project_id=project_id,
        brief_id=brief_id,
        asset_plan_json=json.dumps(asset_plan, ensure_ascii=False),
        model_used=model_used,
        generation_seconds=generation_seconds,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_latest_by_project(db: Session, project_id: int) -> Optional[VisualAsset]:
    """获取某项目最新一次生成结果"""
    return (
        db.query(VisualAsset)
        .filter(VisualAsset.project_id == project_id)
        .order_by(VisualAsset.created_at.desc())
        .first()
    )


def list_by_project(db: Session, project_id: int, limit: int = 10) -> list:
    """获取某项目的历史生成记录（最新在前）"""
    return (
        db.query(VisualAsset)
        .filter(VisualAsset.project_id == project_id)
        .order_by(VisualAsset.created_at.desc())
        .limit(limit)
        .all()
    )
