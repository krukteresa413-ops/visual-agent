"""Dashboard API — enhanced stats with trends, distributions, agent metrics."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from app.db.session import SessionLocal

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


class TrendPoint(BaseModel):
    label: str
    value: int


class DistributionItem(BaseModel):
    name: str
    count: int
    color: str


class DashboardResponse(BaseModel):
    # Account/Project stats
    total_projects: int
    total_generations: int
    projects_with_activity: int

    # Generation stats
    generations_today: int
    generations_this_week: int
    success_rate: float

    # Agent stats
    active_agents: list[str]
    agent_distribution: list[DistributionItem]

    # Trends
    daily_trend: list[TrendPoint]
    type_distribution: list[DistributionItem]

    # Recent activity
    recent_activity: list[dict]

    # Greeting
    greeting: str
    user_name: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    """Return enhanced dashboard stats."""
    from app.models.project import Project
    from app.models.visual_asset import VisualAsset
    from app.models.product_brief import ProductBrief

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())

    # ── Project counts ──
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    projects_with_brief = (
        db.query(func.count(func.distinct(ProductBrief.project_id))).scalar() or 0
    )

    # ── Generation counts ──
    total_generations = db.query(func.count(VisualAsset.id)).scalar() or 0
    generations_today = (
        db.query(func.count(VisualAsset.id))
        .filter(VisualAsset.created_at >= today_start)
        .scalar() or 0
    )
    generations_this_week = (
        db.query(func.count(VisualAsset.id))
        .filter(VisualAsset.created_at >= week_start)
        .scalar() or 0
    )

    # ── Success rate (based on generation_seconds > 0 as proxy) ──
    total_with_gen = db.query(func.count(VisualAsset.id)).filter(
        VisualAsset.generation_seconds > 0
    ).scalar() or 0
    success_rate = round(min(total_with_gen / max(total_generations, 1) * 100, 100), 1)

    # ── Daily trend (last 14 days) ──
    daily_trend = []
    for i in range(13, -1, -1):
        day = today_start - timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = (
            db.query(func.count(VisualAsset.id))
            .filter(VisualAsset.created_at >= day, VisualAsset.created_at < next_day)
            .scalar() or 0
        )
        daily_trend.append(TrendPoint(
            label=day.strftime("%m-%d"),
            value=count,
        ))

    # ── Asset type distribution (from model_used as proxy) ──
    type_colors = {
        "deepseek": "#f97316", "openai": "#3b82f6",
        "gpt-image": "#10b981",
        "grok-video": "#f59e0b", "unknown": "#6b7280",
    }
    type_rows = (
        db.query(VisualAsset.model_used, func.count(VisualAsset.id))
        .filter(VisualAsset.model_used.isnot(None))
        .group_by(VisualAsset.model_used)
        .order_by(func.count(VisualAsset.id).desc())
        .limit(6)
        .all()
    )
    type_distribution = [
        DistributionItem(
            name=t[0] or "unknown",
            count=t[1],
            color=type_colors.get((t[0] or "").split("-")[0] if t[0] else "", "#6b7280"),
        )
        for t in type_rows
    ]

    # ── Agent distribution (model_used breakdown) ──
    agent_rows = (
        db.query(VisualAsset.model_used, func.count(VisualAsset.id))
        .filter(VisualAsset.model_used.isnot(None))
        .group_by(VisualAsset.model_used)
        .order_by(func.count(VisualAsset.id).desc())
        .limit(5)
        .all()
    )
    agent_colors = ["#f59e0b", "#8b5cf6", "#6b7280", "#3b82f6", "#ec4899"]
    agent_distribution = [
        DistributionItem(
            name=r[0] or "unknown",
            count=r[1],
            color=agent_colors[i % len(agent_colors)],
        )
        for i, r in enumerate(agent_rows)
    ]

    # ── Active agents ──
    try:
        from app.agents.orchestrator.agent_factory import AgentFactory
        active_agents = AgentFactory.list_registered() or ["visual", "layout", "mockup"]
    except Exception:
        active_agents = ["visual", "layout", "mockup", "brand", "campaign"]

    # ── Recent activity ──
    recent = (
        db.query(
            VisualAsset.id,
            VisualAsset.model_used,
            VisualAsset.generation_seconds,
            VisualAsset.created_at,
            Project.name.label("project_name"),
        )
        .join(Project, VisualAsset.project_id == Project.id, isouter=True)
        .order_by(VisualAsset.created_at.desc())
        .limit(8)
        .all()
    )
    recent_activity = [
        {
            "id": r.id,
            "project_name": r.project_name or "未知项目",
            "asset_type": "generation",
            "model_used": r.model_used or "unknown",
            "status": "completed" if (r.generation_seconds or 0) > 0 else "pending",
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recent
    ]

    # ── Greeting ──
    hour = now.hour
    if hour < 6:
        greeting_text = "夜深了"
    elif hour < 12:
        greeting_text = "早上好"
    elif hour < 14:
        greeting_text = "中午好"
    elif hour < 18:
        greeting_text = "下午好"
    else:
        greeting_text = "晚上好"

    return DashboardResponse(
        total_projects=total_projects,
        total_generations=total_generations,
        projects_with_activity=projects_with_brief,
        generations_today=generations_today,
        generations_this_week=generations_this_week,
        success_rate=success_rate,
        active_agents=active_agents,
        agent_distribution=agent_distribution,
        daily_trend=daily_trend,
        type_distribution=type_distribution,
        recent_activity=recent_activity,
        greeting=greeting_text,
        user_name="MOYAG",
    )
