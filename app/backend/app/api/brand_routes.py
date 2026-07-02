"""
品牌套件提取 API — 从文本/PDF 中提取品牌元素。
"""
import json
import os
import uuid
from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/brand", tags=["brand"])

# ── schemas ──────────────────────────────────────────

class BrandProfileCreate(BaseModel):
    project_id: Optional[int] = None
    name: str
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_style: Optional[str] = None
    tone_of_voice: Optional[str] = None
    visual_keywords: Optional[list[str]] = None
    forbidden_words: Optional[list[str]] = None


# ── db ───────────────────────────────────────────────

def get_db():
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── brand CRUD (existing) ────────────────────────────

@router.post("/")
def create_brand(req: BrandProfileCreate, db: Session = Depends(get_db)):
    from app.models.brand_profile import BrandProfile
    p = BrandProfile(
        project_id=req.project_id, name=req.name,
        primary_color=req.primary_color, secondary_color=req.secondary_color,
        accent_color=req.accent_color, font_style=req.font_style,
        tone_of_voice=req.tone_of_voice,
        visual_keywords=json.dumps(req.visual_keywords or [], ensure_ascii=False),
        forbidden_words=json.dumps(req.forbidden_words or [], ensure_ascii=False),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name}


@router.get("/project/{project_id}")
def get_brand(project_id: int, db: Session = Depends(get_db)):
    from app.models.brand_profile import BrandProfile
    p = db.query(BrandProfile).filter(BrandProfile.project_id == project_id).first()
    if not p:
        return {"brand": None}
    return {
        "id": p.id, "name": p.name,
        "primary_color": p.primary_color,
        "secondary_color": p.secondary_color,
        "accent_color": p.accent_color,
        "font_style": p.font_style,
        "tone_of_voice": p.tone_of_voice,
        "visual_keywords": p.visual_keywords_list,
        "forbidden_words": p.forbidden_words_list,
        "logo_url": p.logo_url,
    }


@router.post("/{brand_id}/logo")
async def upload_logo(brand_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    p = db.query(BrandProfile).filter(BrandProfile.id == brand_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    ext = file.filename.split(".")[-1] if "." in (file.filename or "") else "png"
    from app.services.storage import get_storage
    p.logo_url = await get_storage().save_bytes(
        await file.read(), tenant_id=p.tenant_id, category="logo", ext=ext,
        project_id=p.project_id, content_type=file.content_type,
    )  # O1: logo 按品牌所属租户/项目分区
    db.commit()
    return {"logo_url": p.logo_url}


# ── brand extraction (NEW) ────────────────────────────

EXTRACT_SYSTEM = """你是一个品牌设计师。从产品文本中提取品牌元素，返回纯 JSON（不要 markdown 代码块）：

{
  "brand_name": "品牌名称（必须）",
  "tagline": "品牌标语/口号",
  "primary_color": "主色 hex（如 #FF6900）",
  "secondary_color": "辅色 hex",
  "accent_color": "强调色 hex",
  "font_headings": "标题字体",
  "font_body": "正文字体",
  "tone_of_voice": "品牌调性描述（简短）",
  "visual_style": "视觉风格（如 极简科技/奢华经典/年轻潮流）",
  "iconography": "图标风格（如 线性/面性/拟物）",
  "brand_story": "品牌故事（1-2句）"
}

规则：
- 如果文本中没明确提到某个字段，填 null
- 颜色从文本中推断（科技→蓝黑、环保→绿、餐饮→暖色）
- 字体从风格推断（科技→无衬线、奢侈→衬线）
- 只返回 JSON，不要任何其他文字"""


from app.services.llm_client import LLMClient


@router.post("/extract")
async def extract_brand(
    text: str = Form(default=""),
    project_id: int = Form(default=0),
    file: Optional[UploadFile] = File(default=None),
):
    """从文本中提取品牌元素。支持 text 或 file 输入。"""
    content = text.strip()
    if file and not content:
        upload_dir = "/opt/visual-agent/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        safe_name = (file.filename or "brand_upload").replace("/", "_").replace("\\", "_")
        ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else "bin"
        tmp = os.path.join(upload_dir, f"brand_extract_{uuid.uuid4().hex[:8]}.{ext}")
        content_bytes = await file.read()
        with open(tmp, "wb") as f:
            f.write(content_bytes)
        try:
            from app.services.document_parser import parse_document
            content = (await parse_document(tmp, file.content_type or ""))[:10000]
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
    if not content.strip():
        raise HTTPException(status_code=400, detail="请提供文本或文件")

    llm = LLMClient()

    try:
        result = await llm.call(
            system_prompt=EXTRACT_SYSTEM,
            user_prompt=f"产品文本：\n{content}",
            temperature=0.3,
            max_tokens=1024,
        )
    except Exception:
        result = {"brand_name": content[:50] if content else "Unknown"}

    from app.schemas.brand_kit import BrandKitOut
    brand_kit = BrandKitOut(
        brand_name=result.get("brand_name", content[:50] if content else "Unknown"),
        tagline=result.get("tagline"),
        primary_color=result.get("primary_color"),
        secondary_color=result.get("secondary_color"),
        accent_color=result.get("accent_color"),
        font_headings=result.get("font_headings"),
        font_body=result.get("font_body"),
        tone_of_voice=result.get("tone_of_voice"),
        visual_style=result.get("visual_style"),
        iconography=result.get("iconography"),
        brand_story=result.get("brand_story"),
    )

    # 缓存到 DB
    if project_id:
        try:
            db = next(get_db())
            _cache_brand_kit(project_id, brand_kit, db)
            db.close()
        except Exception:
            pass

    return brand_kit.model_dump()


def _cache_brand_kit(project_id: int, kit, db: Session):
    """将品牌套件缓存到 brand_profile 表。"""
    from app.models.brand_profile import BrandProfile
    p = db.query(BrandProfile).filter(BrandProfile.project_id == project_id).first()
    if p:
        p.name = kit.brand_name
        p.primary_color = kit.primary_color
        p.secondary_color = kit.secondary_color
        p.accent_color = kit.accent_color
        p.font_style = kit.font_headings
        p.tone_of_voice = kit.tone_of_voice
        p.visual_keywords = json.dumps(
            [kit.visual_style, kit.iconography] if kit.visual_style else [],
            ensure_ascii=False,
        )
        p.tagline = kit.tagline
        p.brand_story = kit.brand_story
    else:
        p = BrandProfile(
            project_id=project_id,
            name=kit.brand_name,
            primary_color=kit.primary_color,
            secondary_color=kit.secondary_color,
            accent_color=kit.accent_color,
            font_style=kit.font_headings,
            tone_of_voice=kit.tone_of_voice,
            visual_keywords=json.dumps(
                [kit.visual_style, kit.iconography] if kit.visual_style else [],
                ensure_ascii=False,
            ),
            tagline=kit.tagline,
            brand_story=kit.brand_story,
        )
        db.add(p)
    db.commit()


# ── brand kit cache read (NEW) ────────────────────────

@router.get("/{project_id}")
def get_brand_kit(project_id: int, db: Session = Depends(get_db)):
    """读取缓存的品牌套件。"""
    from app.models.brand_profile import BrandProfile
    from app.schemas.brand_kit import BrandKitOut
    p = db.query(BrandProfile).filter(BrandProfile.project_id == project_id).first()
    if not p:
        return {"brand_kit": None}
    kit = BrandKitOut(
        brand_name=p.name,
        tagline=p.tagline if hasattr(p, "tagline") else None,
        primary_color=p.primary_color,
        secondary_color=p.secondary_color,
        accent_color=p.accent_color,
        font_headings=p.font_style,
        font_body=None,
        tone_of_voice=p.tone_of_voice,
        visual_style=p.visual_keywords_list[0] if p.visual_keywords_list else None,
        iconography=p.visual_keywords_list[1] if len(p.visual_keywords_list) > 1 else None,
        brand_story=p.brand_story if hasattr(p, "brand_story") else None,
    )
    return {"brand_kit": kit.model_dump()}


# ── multi-brand library management (NEW) ──────────────
# 路由放在 /manage/* 二级路径下,避免与单段 /{project_id} 冲突
from app.models.auth import Tenant


def _default_tenant_id(db: Session) -> Optional[int]:
    t = db.query(Tenant).filter(Tenant.slug == "muyuanjia").first()
    return t.id if t else None


def _brand_to_dict(p) -> dict:
    return {
        "id": p.id,
        "tenant_id": p.tenant_id,
        "project_id": p.project_id,
        "is_canonical": bool(p.is_canonical),
        "name": p.name,
        "primary_color": p.primary_color,
        "secondary_color": p.secondary_color,
        "accent_color": p.accent_color,
        "font_style": p.font_style,
        "tone_of_voice": p.tone_of_voice,
        "visual_keywords": p.visual_keywords_list,
        "forbidden_words": p.forbidden_words_list,
        "logo_url": p.logo_url,
        "tagline": p.tagline,
        "target_audience": p.target_audience,
        "product_images": p.product_images_list,
        "memory_summary": p.memory_summary,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


class BrandManualInput(BaseModel):
    name: str
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_style: Optional[str] = None
    tone_of_voice: Optional[str] = None
    visual_keywords: Optional[list[str]] = None
    forbidden_words: Optional[list[str]] = None
    tagline: Optional[str] = None
    target_audience: Optional[str] = None
    product_images: Optional[list[str]] = None
    memory_summary: Optional[str] = None


@router.get("/manage/list")
def list_brands(db: Session = Depends(get_db), tenant_id: Optional[int] = None):
    """列出当前租户的品牌(按名称去重,保留最近更新的一条)。"""
    from app.models.brand_profile import BrandProfile
    tid = tenant_id if tenant_id is not None else _default_tenant_id(db)
    q = db.query(BrandProfile)
    if tid is not None:
        q = q.filter(BrandProfile.tenant_id == tid)
    # 展示用:隐藏自动化测试脏数据,仅展示有主色的完整真实品牌(不删除底层数据)
    q = q.filter(~BrandProfile.name.like("TestBrand%"))
    q = q.filter(BrandProfile.name != "BrandWithKeywords")
    q = q.filter(BrandProfile.primary_color.isnot(None))
    rows = q.order_by(BrandProfile.updated_at.desc()).all()
    seen: dict = {}
    for r in rows:
        key = (r.name or "").strip().lower()
        if key and key not in seen:
            seen[key] = r
    return {"brands": [_brand_to_dict(r) for r in seen.values()]}


@router.post("/manage/create")
def create_brand_manual(req: BrandManualInput, db: Session = Depends(get_db)):
    from app.models.brand_profile import BrandProfile
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="品牌名不能为空")
    p = BrandProfile(
        tenant_id=_default_tenant_id(db),
        name=req.name.strip(),
        primary_color=req.primary_color,
        secondary_color=req.secondary_color,
        accent_color=req.accent_color,
        font_style=req.font_style,
        tone_of_voice=req.tone_of_voice,
        visual_keywords=json.dumps(req.visual_keywords or [], ensure_ascii=False),
        forbidden_words=json.dumps(req.forbidden_words or [], ensure_ascii=False),
        tagline=req.tagline,
        target_audience=req.target_audience,
        product_images=json.dumps(req.product_images or [], ensure_ascii=False),
        memory_summary=req.memory_summary,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _brand_to_dict(p)


@router.patch("/manage/{brand_id}")
def update_brand_manual(brand_id: int, req: BrandManualInput, db: Session = Depends(get_db)):
    from app.models.brand_profile import BrandProfile
    p = db.query(BrandProfile).filter(BrandProfile.id == brand_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="品牌不存在")
    p.name = req.name.strip() or p.name
    p.primary_color = req.primary_color
    p.secondary_color = req.secondary_color
    p.accent_color = req.accent_color
    p.font_style = req.font_style
    p.tone_of_voice = req.tone_of_voice
    p.visual_keywords = json.dumps(req.visual_keywords or [], ensure_ascii=False)
    p.forbidden_words = json.dumps(req.forbidden_words or [], ensure_ascii=False)
    p.tagline = req.tagline
    p.target_audience = req.target_audience
    p.product_images = json.dumps(req.product_images or [], ensure_ascii=False)
    p.memory_summary = req.memory_summary
    db.commit()
    db.refresh(p)
    return _brand_to_dict(p)


@router.delete("/manage/{brand_id}")
def delete_brand_manual(brand_id: int, db: Session = Depends(get_db)):
    from app.models.brand_profile import BrandProfile
    p = db.query(BrandProfile).filter(BrandProfile.id == brand_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="品牌不存在")
    db.delete(p)
    db.commit()
    return {"ok": True, "id": brand_id}
