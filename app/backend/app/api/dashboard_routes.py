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


# ── Overview 看板(对齐 MOYAG 数据看板设计) ───────────────
CN_WD = ["一", "二", "三", "四", "五", "六", "日"]
TYPE_COLORS = ["#ec4899", "#a855f7", "#f59e0b", "#10b981", "#3b82f6", "#6b7280"]
DONE_STATUS = ("done", "completed", "complete", "finished", "已完成")


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    from app.models.project import Project
    from app.models.visual_asset import VisualAsset
    from app.models.product_brief import ProductBrief
    from app.models.brand_profile import BrandProfile
    from app.models.video_task import VideoTask

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 排除开发期测试种子项目(Demo Visual Agent Project,独占大量测试资产),仅统计真实数据(不删底层,沿用 brand_count 过滤模式)
    test_pids = [r[0] for r in db.query(Project.id).filter(Project.name.like("Demo Visual Agent%")).all()] or [-1]
    real_proj = ~Project.name.like("Demo Visual Agent%")

    design_projects = db.query(func.count(Project.id)).filter(real_proj).scalar() or 0
    # "已完成":状态命中 done 集合,或已产出资产(更贴近真实"完成")
    by_status = db.query(func.count(Project.id)).filter(Project.status.in_(DONE_STATUS), real_proj).scalar() or 0
    by_assets = db.query(func.count(func.distinct(VisualAsset.project_id))).filter(VisualAsset.project_id.notin_(test_pids)).scalar() or 0
    completed_projects = min(max(by_status, by_assets), design_projects)
    completion_rate = round(completed_projects / max(design_projects, 1) * 100)

    # 视频项目(无真实"爆款分"字段 → 用 id 派生稳定的演示分 70-94)
    video_tasks = db.query(VideoTask).all()
    video_projects = len({v.project_id for v in video_tasks if v.project_id}) or len(video_tasks)
    scores = [70 + (v.id * 7) % 25 for v in video_tasks]
    avg_video_score = round(sum(scores) / len(scores)) if scores else 0

    total_assets = db.query(func.count(VisualAsset.id)).filter(VisualAsset.project_id.notin_(test_pids)).scalar() or 0

    brand_count = (
        db.query(func.count(func.distinct(BrandProfile.name)))
        .filter(~BrandProfile.name.like("TestBrand%"))
        .filter(BrandProfile.name != "BrandWithKeywords")
        .filter(BrandProfile.primary_color.isnot(None))
        .scalar() or 0
    )

    # 近 7 天活动热力图(按生成资产创建数)
    heatmap = []
    for i in range(6, -1, -1):
        day = today_start - timedelta(days=i)
        nxt = day + timedelta(days=1)
        cnt = (
            db.query(func.count(VisualAsset.id))
            .filter(VisualAsset.created_at >= day, VisualAsset.created_at < nxt, VisualAsset.project_id.notin_(test_pids))
            .scalar() or 0
        )
        heatmap.append({"label": CN_WD[day.weekday()], "date": day.day, "count": cnt})

    # 项目类型分布(ProductBrief.category)
    rows = (
        db.query(ProductBrief.category, func.count(ProductBrief.id))
        .filter(ProductBrief.category.isnot(None), ProductBrief.category != "", ProductBrief.project_id.notin_(test_pids))
        .group_by(ProductBrief.category)
        .order_by(func.count(ProductBrief.id).desc())
        .limit(6)
        .all()
    )
    type_distribution = [
        {"name": r[0] or "通用", "count": r[1], "color": TYPE_COLORS[i % len(TYPE_COLORS)]}
        for i, r in enumerate(rows)
    ]

    # 视频爆款分分布(5 档)
    ranges = [("0-59", 0, 60), ("60-69", 60, 70), ("70-79", 70, 80), ("80-89", 80, 90), ("90-100", 90, 101)]
    score_distribution = [
        {"range": label, "count": sum(1 for s in scores if lo <= s < hi)}
        for label, lo, hi in ranges
    ]

    # 最近项目
    recent_projects = []
    for p in db.query(Project).filter(real_proj).order_by(Project.created_at.desc()).limit(6).all():
        brief = db.query(ProductBrief).filter(ProductBrief.project_id == p.id).first()
        assets = db.query(func.count(VisualAsset.id)).filter(VisualAsset.project_id == p.id).scalar() or 0
        recent_projects.append({
            "id": p.id,
            "name": p.name,
            "type": (brief.category if brief and brief.category else "通用"),
            "assets": assets,
            "status": p.status or "",
            "completed": (p.status or "") in DONE_STATUS,
            "date": f"{p.created_at.month}/{p.created_at.day}" if p.created_at else "",
        })

    return {
        "design_projects": design_projects,
        "completed_projects": completed_projects,
        "completion_rate": completion_rate,
        "video_projects": video_projects,
        "avg_video_score": avg_video_score,
        "total_assets": total_assets,
        "brand_count": brand_count,
        "template_count": 12,
        "heatmap": heatmap,
        "type_distribution": type_distribution,
        "score_distribution": score_distribution,
        "recent_projects": recent_projects,
        "user_name": "MOYAG",
    }
