"""
灵感库 API — 浏览、筛选、获取单条灵感。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from urllib.parse import urlparse

from app.db.session import get_db
from app.models.inspiration import InspirationItem

router = APIRouter(prefix="/api/v1/inspirations", tags=["inspiration"])


def _normalize_preview_url(preview_url: str) -> str:
    parsed = urlparse(preview_url)
    if parsed.scheme and parsed.netloc and parsed.path.startswith("/static/"):
        return parsed.path
    return preview_url


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """
    返回灵感库的分类树：{category: [sub_category, ...], ...}
    """
    items = db.query(InspirationItem).all()
    tree = {}
    for item in items:
        tree.setdefault(item.category, set()).add(item.sub_category)
    return {k: sorted(list(v)) for k, v in tree.items()}


@router.get("")
def list_inspirations(
    category: Optional[str] = Query(None),
    sub_category: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="自然语言搜索关键词"),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    分页浏览灵感库，支持按分类筛选和自然语言搜索。
    q: 搜索关键词，匹配 category, sub_category 或 prompt_template
    """
    query = db.query(InspirationItem)
    if category:
        query = query.filter(InspirationItem.category == category)
    if sub_category:
        query = query.filter(InspirationItem.sub_category == sub_category)
    
    # 自然语言搜索：在 category, sub_category, prompt_template 中查找
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (InspirationItem.category.ilike(search_term)) |
            (InspirationItem.sub_category.ilike(search_term)) |
            (InspirationItem.prompt_template.ilike(search_term))
        )
    
    items = query.order_by(InspirationItem.id).limit(limit).all()
    return [
        {
            "id": item.id,
            "category": item.category,
            "sub_category": item.sub_category,
            "preview_url": _normalize_preview_url(item.preview_url),
            "prompt_template": item.prompt_template,
            "aspect_ratio": item.aspect_ratio,
            "source": item.source,
        }
        for item in items
    ]


@router.get("/{item_id}")
def get_inspiration(item_id: int, db: Session = Depends(get_db)):
    """
    获取单条灵感详情（含完整 Prompt 模板）。
    """
    item = db.query(InspirationItem).filter(InspirationItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="灵感项不存在")
    return {
        "id": item.id,
        "category": item.category,
        "sub_category": item.sub_category,
        "preview_url": _normalize_preview_url(item.preview_url),
        "prompt_template": item.prompt_template,
        "aspect_ratio": item.aspect_ratio,
        "source": item.source,
    }
