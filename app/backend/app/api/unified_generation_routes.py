"""Unified endpoint: upload document → parse → review → generate all 6 visual types."""
import os, uuid, time, json as _json
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.document_parser import parse_document
from app.services.brief_parser import parse_brief_text
from app.services.brief_reviewer import BriefReviewer
from app.services.compliance import ComplianceChecker
from app.services.visual_agent import VisualAgent

router = APIRouter(prefix="/api/v1", tags=["unified-generation"])

ALLOWED_TYPES = {
    "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/msword", "application/vnd.ms-excel", "application/vnd.ms-powerpoint",
    "text/plain", "text/csv", "image/png", "image/jpeg", "image/webp",
}
MAX_SIZE = 20 * 1024 * 1024
UPLOAD_DIR = "/opt/visual-agent/uploads"
agent = VisualAgent()


@router.post("/generate-from-document")
async def generate_from_document(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    parsed_brief_json: str | None = Form(None),
    project_id: int = Form(2),
    platform_id: str | None = Form(None),
    skip_review: bool = Form(False),
    answers: str | None = Form(None),
    generate_images: bool = Form(False),
    generate_videos: bool = Form(False),
):
    if not file and not text and not parsed_brief_json:
        raise HTTPException(status_code=400, detail="请上传文件或输入产品文字")

    # Support review resubmit: use pre-parsed brief directly
    brief = None
    if parsed_brief_json:
        try:
            brief = _json.loads(parsed_brief_json)
        except _json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="parsed_brief_json 格式无效")
    else:
        extracted_text = ""
        if file:
            if file.content_type and file.content_type not in ALLOWED_TYPES:
                raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}")
            content = await file.read()
            if len(content) > MAX_SIZE:
                raise HTTPException(status_code=400, detail="文件超过 20MB")
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "bin"
            tmp = os.path.join(UPLOAD_DIR, f"unified_{uuid.uuid4().hex[:8]}.{ext}")
            with open(tmp, "wb") as f:
                f.write(content)
            try:
                extracted_text = await parse_document(tmp, file.content_type or "")
                if not extracted_text.strip():
                    raise HTTPException(status_code=422, detail="无法从文件中提取文本")
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
        else:
            extracted_text = text or ""

        MAX_TEXT_LENGTH = 8000
        if len(extracted_text) > MAX_TEXT_LENGTH:
            extracted_text = extracted_text[:MAX_TEXT_LENGTH] + "\n...(内容已截断)"

        try:
            brief = await parse_brief_text(extracted_text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI 解析失败: {str(e)}")

    # Load brand profile memory
    brand_context = ""
    try:
        from app.db.session import SessionLocal
        from app.models.brand_profile import BrandProfile
        bdb = SessionLocal()
        bp = bdb.query(BrandProfile).filter(BrandProfile.project_id == project_id).first()
        if bp:
            brand_context = bp.to_prompt_context()
            brief["_brand_context"] = brand_context
        bdb.close()
    except Exception:
        pass

    # Compliance check
    compliance_warnings = ComplianceChecker.check_brief(brief)

    # Merge user answers into brief
    if answers:
        try:
            user_answers = _json.loads(answers)
            for field, answer in user_answers.items():
                if answer and answer.strip():
                    if isinstance(answer, list):
                        brief[field] = answer
                    elif field in ("specifications", "selling_points", "target_market",
                                   "usage_scenarios", "target_customer", "materials", "compliance_notes"):
                        brief[field] = [s.strip() for s in answer.split(",") if s.strip()]
                    else:
                        brief[field] = answer.strip()
        except _json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="answers 格式无效，需要 JSON")

    # Review check
    if not skip_review:
        questions = BriefReviewer.generate_questions(brief)
        required_missing = [q for q in questions if q["level"] == "required"]
        if required_missing:
            return {
                "needs_review": True, "parsed_brief": brief,
                "questions": questions, "compliance_warnings": compliance_warnings,
                "generation": None, "elapsed_seconds": 0,
            }
        if questions:
            brief["_review_questions"] = questions

    if not brief.get("product_name"):
        raise HTTPException(status_code=422, detail="未能识别产品名称，请提供更详细的产品资料或回答追问")

    # Generate
    try:
        start = time.time()
        result = await agent.generate_all_parallel(project_id=project_id, brief=brief, platform_id=platform_id)
        elapsed = round(time.time() - start, 1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

    # Auto-save to history
    try:
        from app.db.session import SessionLocal
        from app.db.crud_visual_asset_v2 import save_asset_plan
        db = SessionLocal()
        save_asset_plan(db=db, project_id=project_id, asset_plan=result.model_dump(),
                        model_used=getattr(agent._llm, '_model', 'unknown'), generation_seconds=int(elapsed))
        db.close()
    except Exception:
        pass

    # Optional image generation
    images = None
    if generate_images:
        try:
            images = await agent.generate_images_from_plan(result, provider="dalle")
        except Exception:
            images = None

    # Optional video generation
    videos = None
    if generate_videos:
        try:
            videos = await agent.generate_videos_from_plan(result, provider="local")
        except Exception:
            videos = None

    return {
        "needs_review": False,
        "compliance_warnings": compliance_warnings,
        "filename": file.filename if file else None,
        "extracted_text_preview": extracted_text[:300] if not parsed_brief_json else None,
        "parsed_brief": brief,
        "review_questions": brief.pop("_review_questions", []),
        "images": images,
        "videos": videos,
        "generation": {
            "main_image": result.main_image.model_dump() if result.main_image else None,
            "white_bg": result.white_bg.model_dump() if result.white_bg else None,
            "scene_images": [s.model_dump() for s in (result.scene_images or [])],
            "selling_points": [s.model_dump() for s in (result.selling_points or [])],
            "video_scripts": [v.model_dump() for v in (result.video_scripts or [])],
            "ad_material": result.ad_material.model_dump() if result.ad_material else None,
        },
        "elapsed_seconds": elapsed,
    }


# ── History endpoints ──────────────────────────────────────────────────

@router.get("/projects/{project_id}/history")
def list_history(project_id: int, limit: int = 20):
    from app.db.session import SessionLocal
    from app.models.visual_asset import VisualAsset
    db = SessionLocal()
    try:
        records = (db.query(VisualAsset).filter(VisualAsset.project_id == project_id)
                   .order_by(VisualAsset.created_at.desc()).limit(limit).all())
        return {"records": [{
            "id": r.id, "project_id": r.project_id, "brief_id": r.brief_id,
            "model_used": r.model_used, "generation_seconds": r.generation_seconds,
            "created_at": r.created_at.isoformat() if hasattr(r.created_at, 'isoformat') else str(r.created_at) if r.created_at else None,
        } for r in records]}
    finally:
        db.close()


@router.get("/projects/{project_id}/history/{record_id}")
def get_history_detail(project_id: int, record_id: int):
    from app.db.session import SessionLocal
    from app.models.visual_asset import VisualAsset
    db = SessionLocal()
    try:
        record = (db.query(VisualAsset)
                  .filter(VisualAsset.id == record_id, VisualAsset.project_id == project_id).first())
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        return {
            "id": record.id, "project_id": record.project_id, "brief_id": record.brief_id,
            "model_used": record.model_used, "generation_seconds": record.generation_seconds,
            "created_at": record.created_at.isoformat() if hasattr(record.created_at, 'isoformat') else str(record.created_at) if record.created_at else None,
            "asset_plan": _json.loads(record.asset_plan_json),
        }
    finally:
        db.close()