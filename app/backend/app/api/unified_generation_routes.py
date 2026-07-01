"""Unified endpoint: upload document → parse → review → generate all 6 visual types."""
import os, uuid, time, re, json as _json, asyncio, logging
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.document_parser import parse_document
from app.services.text_prefilter import clean_pdf_text
from app.services.brief_parser import parse_brief_text
from app.services.brief_reviewer import BriefReviewer
from app.services.compliance import ComplianceChecker
from app.services.visual_agent import VisualAgent
from app.services.generation_tracker import GenerationTracker
from app.services.vision_service import vision_service
from app.services.product_library import upsert_product_brief_for_project

logger = logging.getLogger(__name__)

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

# In-memory store for async image generation results
_image_results: dict = {}  # project_id -> {"status": "pending"|"done", "images": ...}
_async_gen_tasks: dict = {}  # task_id -> {"status": "processing"|"complete"|"error", "result": ...}
agent = VisualAgent()


def _prepare_text_for_brief_parse(extracted_text: str, max_chars: int = 8000) -> str:
    """Conservatively clean document text before LLM brief parsing.

    Keep the original 8000-character parsing budget. Do not extract compact
    snippets here; parsing quality is more important than theatrical savings.
    """
    cleaned = clean_pdf_text(extracted_text)
    import logging
    logging.getLogger(__name__).info(
        "document_text_cleaner raw_chars=%s cleaned_chars=%s llm_chars=%s",
        len(extracted_text or ""),
        len(cleaned),
        min(len(cleaned), max_chars),
    )
    return cleaned[:max_chars]


class RoutePreviewRequest(BaseModel):
    prompt: str = Field(min_length=1)
    modality: str = "image"
    modelKey: str | None = None
    maxBudget: float | None = None


def _model_key_provider(model_key: str) -> str:
    return model_key.split(":", 1)[0] if ":" in model_key else model_key


def _estimate_route_cost(item) -> float:
    if item.cost_estimate is not None:
        return float(item.cost_estimate)
    if item.modality == "video":
        return 0.24
    return 0.04


def _preview_plan(modality: str) -> dict:
    if modality == "video":
        steps = [
            ("analyze", "分析需求"),
            ("route", "选择视频模型"),
            ("storyboard", "拆分镜头脚本"),
            ("generate_video", "生成视频资产"),
            ("deliver", "同步到画布"),
        ]
        plan_type = "multi_step_video"
    else:
        steps = [
            ("analyze", "分析需求"),
            ("route", "选择图像模型"),
            ("generate_image", "生成图像资产"),
            ("deliver", "同步到画布"),
        ]
        plan_type = "single_asset"
    return {
        "type": plan_type,
        "steps": [
            {"id": step_id, "label": label, "productionRoute": False}
            for step_id, label in steps
        ],
    }


def _route_preview(req: RoutePreviewRequest) -> dict:
    from app.services.provider_inventory import build_inventory

    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="prompt不能为空")
    modality = req.modality if req.modality in {"image", "video"} else "image"
    candidates = build_inventory(modality=modality)
    selected = None
    if req.modelKey:
        selected = next((item for item in candidates if item.model_key == req.modelKey), None)
    if selected is None:
        selected = next((item for item in candidates if item.production_usable), None)
    if selected is None and candidates:
        selected = candidates[0]
    if selected is None:
        model_key = f"dataeyes:{modality}" if modality == "image" else f"runway:{modality}"
        provider = _model_key_provider(model_key)
        display_name = provider
        cost = 0.04 if modality == "image" else 0.24
    else:
        model_key = selected.model_key
        provider = selected.provider
        display_name = selected.display_name
        cost = _estimate_route_cost(selected)
    halted = req.maxBudget is not None and cost > req.maxBudget
    return {
        "is_preview": True,
        "productionRoute": False,
        "recommendedRoute": {
            "modelKey": model_key,
            "provider": provider,
            "modality": modality,
            "displayName": display_name,
        },
        "estimatedCost": {
            "amount": round(cost, 4),
            "currency": "USD",
            "source": "moyag_inventory",
        },
        "plan": _preview_plan(modality),
        "budgetGate": {
            "halted": halted,
            "reason": "over_budget" if halted else "within_budget",
            "maxBudget": req.maxBudget,
        },
        "notes": ["preview_only", "does_not_change_generation_route"],
    }


@router.post("/generation/route-preview")
async def route_preview(req: RoutePreviewRequest):
    return _route_preview(req)


def _build_minimal_brand_prompt_context(brand) -> str:
    if not brand:
        return ""
    parts = []
    primary_color = getattr(brand, "primary_color", None)
    if primary_color:
        parts.append(f"品牌色:{primary_color}")
    keywords = (getattr(brand, "visual_keywords_list", None) or [])[:5]
    if keywords:
        parts.append(f"风格关键词:{','.join(str(k) for k in keywords if k)}")
    forbidden = getattr(brand, "forbidden_words_list", None) or []
    avoid = ",".join(str(w) for w in forbidden if w) or "艳俗廉价感"
    parts.append(f"避免:{avoid}")
    return ";".join(parts)


def _canvas_elements_from_asset_plan(project_id: int, asset_plan: dict) -> list[dict]:
    """Build canvas elements for generated image/video assets."""
    elements: list[dict] = []
    images = []
    main = asset_plan.get("main_image") or {}
    if main.get("url"):
        images.append(("main_image", main.get("goal") or "Main Image", main))
    white_bg = asset_plan.get("white_bg") or {}
    if white_bg.get("url"):
        images.append(("white_bg", white_bg.get("goal") or "White Background", white_bg))
    for idx, scene in enumerate(asset_plan.get("scene_images") or [], start=1):
        if scene.get("url"):
            images.append(("scene_image", scene.get("scene_name") or f"Scene Image {idx}", scene))

    for idx, (asset_type, label, image) in enumerate(images):
        url = image.get("url")
        elements.append({
            "id": f"image_{project_id}_{asset_type}_{idx}",
            "type": "image",
            "label": label,
            "x": idx * 320,
            "y": 0,
            "width": 280,
            "height": 280,
            "thumbnail_url": url,
            "asset_ref": {"type": asset_type, "url": url},
            "metadata": {"auto_seeded": True, "source": "generate_all"},
        })

    video = asset_plan.get("video") if isinstance(asset_plan, dict) else None
    if isinstance(video, dict) and video.get("url"):
        task_id = video.get("task_id") or "latest"
        elements.append({
            "id": f"video_{project_id}_{task_id}",
            "type": "video",
            "label": "生成视频",
            "x": len(elements) * 320,
            "y": 0,
            "width": 360,
            "height": 260,
            "thumbnail_url": video.get("url"),
            "asset_ref": {"type": "video", "url": video.get("url"), "task_id": task_id},
            "metadata": {"auto_seeded": True, "source": "video_generation", "duration_seconds": video.get("duration"), "status": "complete"},
        })
    return elements


def _ensure_canvas_image_elements(db, project_id: int, asset_plan: dict, canvas_id: int | None = None) -> None:
    """Seed canvas-state with rendered assets so new projects are non-empty.

    Phase C: 落到 (project, canvas) 解析出的画布;canvas_id 缺省=项目默认画布(自愈遗留行)。
    """
    from datetime import datetime
    from app.services.canvas_service import get_canvas_state_for

    generated_elements = _canvas_elements_from_asset_plan(project_id, asset_plan)
    if not generated_elements:
        return

    _canvas, state = get_canvas_state_for(db, project_id, canvas_id, create_defaults=True)
    try:
        elements = _json.loads(state.elements_json or "[]")
    except Exception:
        elements = []

    existing_keys = {
        (el.get("thumbnail_url"), (el.get("asset_ref") or {}).get("task_id"))
        for el in elements if isinstance(el, dict)
    }
    for el in generated_elements:
        key = (el.get("thumbnail_url"), (el.get("asset_ref") or {}).get("task_id"))
        if key in existing_keys:
            continue
        elements.append(el)

    state.elements_json = _json.dumps(elements, ensure_ascii=False)
    state.updated_at = datetime.utcnow()
    db.commit()

def _history_prompt(asset_plan_json: str | None) -> str | None:
    if not asset_plan_json:
        return None
    try:
        asset_plan = _json.loads(asset_plan_json)
    except Exception:
        return None
    prompt = asset_plan.get("prompt") or asset_plan.get("original_prompt")
    if isinstance(prompt, str) and prompt.strip():
        return prompt.strip()
    main_image = asset_plan.get("main_image")
    if isinstance(main_image, dict):
        prompt = main_image.get("prompt") or main_image.get("goal")
        if isinstance(prompt, str) and prompt.strip():
            return prompt.strip()
    return None


def _history_model_used(asset_plan: dict, llm_model: str | None = None) -> str:
    provider_raw = asset_plan.get("_provider_raw") if isinstance(asset_plan, dict) else None
    provider_raw = provider_raw if isinstance(provider_raw, dict) else {}
    provider = provider_raw.get("provider")
    provider_model = provider_raw.get("model")
    if provider_model:
        return f"{provider}:{provider_model}" if provider else str(provider_model)

    main_image = asset_plan.get("main_image") if isinstance(asset_plan, dict) else None
    main_image = main_image if isinstance(main_image, dict) else {}
    requested_model = main_image.get("provider_model") or main_image.get("model")
    if requested_model:
        return str(requested_model)

    return llm_model or "unknown"

VIDEO_MODEL_OPTIONS = {
    "doubao-seedance-1-5-pro-251215": {"platform": "seedance", "resolution": "720p"},
    "kling-v2-6": {"platform": "kling", "mode": "std", "aspect_ratio": "16:9", "sound": "off"},
    "kling-v3": {"platform": "kling", "mode": "std", "aspect_ratio": "16:9", "sound": "off"},
    "kling-v2-5-turbo": {"platform": "kling", "mode": "std", "aspect_ratio": "16:9", "sound": "off"},
    "viduq3-pro": {"platform": "vidu", "aspect_ratio": "16:9", "resolution": "720p"},
}

def _selected_video_model(req) -> tuple[str, dict]:
    requested = getattr(req, "image_model", None)
    if requested in VIDEO_MODEL_OPTIONS:
        return requested, dict(VIDEO_MODEL_OPTIONS[requested])
    return "doubao-seedance-1-5-pro-251215", dict(VIDEO_MODEL_OPTIONS["doubao-seedance-1-5-pro-251215"])


async def _quick_generate_video_asset(req, brief: dict) -> dict:
    """Generate video when user intent is video."""
    from app.services.video_generation_service import video_generation_service, VideoGenerationRequest

    prompt = req.prompt
    duration = 5
    resolution = "720p"
    # Try to extract duration from prompt (e.g. "30秒")
    import re
    dur_match = re.search(r"(\d+)\s*秒", prompt)
    if dur_match:
        duration = int(dur_match.group(1))

    model, base_options = _selected_video_model(req)
    base_options.setdefault("resolution", resolution)
    sel_platform = base_options.get("platform") or "seedance"

    # 用户选定的 (platform, model) 优先;其余作为“提交失败”时的快速回退。
    # 提交是秒级的,真正出片由后台 video_polling_worker 轮询(异步出片)。
    _fallback = [
        ("seedance", "doubao-seedance-1-5-pro-251215"),
        ("kling", "kling-v2-6"),
        ("vidu", "viduq3-pro"),
        ("hailuo", "MiniMax-Hailuo-2.3"),
    ]
    video_chain = [(sel_platform, model)] + [(p, m) for (p, m) in _fallback if p != sel_platform]
    last_err = None
    for platform, vmodel in video_chain:
        options = dict(base_options)
        options["platform"] = platform
        options["submit_only"] = True
        options["project_id"] = getattr(req, "project_id", None)
        if getattr(req, "reference_image_url", None):
            options["first_frame_url"] = req.reference_image_url
        try:
            result = await video_generation_service.generate(VideoGenerationRequest(
                provider="dataeyes",
                prompt=prompt,
                duration=duration,
                model=vmodel,
                options=options,
            ))
            if result.videos:
                v = result.videos[0]
                return {
                    "video": {"url": v.url, "duration": duration, "task_id": v.provider_asset_id},
                    "modality": "video",
                    "status": "submitted",
                    "message": "视频已提交，排队生成中",
                }
        except Exception as e:  # noqa: BLE001 — 换下一家厂商
            last_err = e
            continue
    return {
        "video": {"url": "", "duration": duration, "error": str(last_err) if last_err else "视频厂商均不可用"},
        "modality": "video",
        "_note": "所有视频厂商暂不可用,请稍后重试。",
    }


async def _generate_quick_asset_for_modality(req, brief: dict, is_video_intent: bool, progress) -> dict:
    """Route quick generation by modality.

    Phase 1 stop-bleed: video capability is not open yet, so video intent must
    return an explicit unavailable result and must not call the image path.
    """
    if is_video_intent:
        await progress.step("生成第一段视频", "generating", "视频已提交，排队生成中")
        return await _quick_generate_video_asset(req, brief)

    await progress.step("快速出图", "generating", "正在用 AI 模型生成第一张图...")
    return await _quick_generate_image_asset(req, brief)

async def _quick_generate_image_asset(req, brief: dict) -> dict:
    """Generate the first visible image fast, without waiting for all six LLM assets."""
    from app.models.image_generation_model import ImageGenerationRequest
    from app.services.image_generation_service import image_generation_service

    prompt = req.prompt
    brand_context = (brief or {}).get("_brand_context")
    if brand_context:
        prompt = f"{prompt}\n{brand_context}"
    # 以图生图(需求二):有源图时保留主体、按用户指令做定制化修改,并把源图喂给吃图模型
    reference_image_url = getattr(req, "reference_image_url", None)
    if reference_image_url:
        prompt = f"在保留参考图中产品主体的前提下,按以下要求对其进行定制化修改:{prompt}"
    # 自动路由 + 失败回退:依次尝试 provider 链,任一成功即返回;最终回退 local 占位,保证不卡死/不 502
    chain: list[str] = []
    if req.image_provider:
        chain.append(req.image_provider)
    for p in ("dataeyes", "mige", "pollinations", "local"):
        if p not in chain:
            chain.append(p)
    if reference_image_url:
        # 以图生图只有 dataeyes(gemini)能真正吃图;不静默回退到会丢图的文生图 provider
        chain = ["dataeyes"]

    image_result = None
    image = None
    last_err = None
    for prov in chain:
        try:
            image_result = await image_generation_service.generate(ImageGenerationRequest(
                provider=prov,
                model=None if req.auto_model else req.image_model,
                prompt=prompt,
                width=1024,
                height=1024,
                reference_image_url=reference_image_url,
            ))
            image = image_result.images[0] if (image_result and image_result.images) else None
            if image is not None and image.url:
                if prov != chain[0]:
                    logger.warning("quick image fallback: %s -> %s", chain[0], prov)
                break
            image = None
        except Exception as e:  # noqa: BLE001 — 回退到下一个 provider
            last_err = e
            logger.warning("quick image provider %s failed: %s", prov, e)
            image_result = None
            image = None
            continue

    if image is None or not image.url:
        raise HTTPException(status_code=502, detail=f"图片生成失败：所有 provider 均未返回 url（尝试 {chain}，最后错误：{last_err}）")

    provider_raw = image_result.raw or {}
    requested_model = provider_raw.get("requested_model") or (None if req.auto_model else req.image_model) or "gpt-image-2"
    provider_model = provider_raw.get("model") or requested_model

    return {
        "project_id": req.project_id,
        "_provider_raw": {"model": provider_model, "requested_model": requested_model, "provider": image_result.provider},
        "main_image": {
            "asset_type": "main_image",
            "model": requested_model,
            "provider_model": provider_model,
            "goal": req.prompt[:80] or "快速出图",
            "composition": "快速出图",
            "background": "auto",
            "prompt": prompt,
            "url": image.url,
            "thumbnail_url": image.url,
            "width": image.width,
            "height": image.height,
            "status": "succeeded",
        },
        "white_bg": None,
        "scene_images": [],
        "selling_points": [],
        "video_scripts": [],
        "ad_material": {
            "ad_goal": "快速出图",
            "target_audience": "auto",
            "ad_angle": "image-first",
            "material_list": [],
            "shot_sequence": [],
            "hook": req.prompt,
            "key_selling_points": [],
            "cta": "",
            "platform_suggestion": "",
        },
    }


@router.post("/generate-from-document")
async def generate_from_document(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    parsed_brief_json: str | None = Form(None),
    project_id: int = Form(2),
    platform_id: str | None = Form(None),
    skip_review: bool = Form(False),
    strategy_first: bool = Form(False),
    answers: str | None = Form(None),
    generate_images: bool = Form(False),
    generate_videos: bool = Form(False),
    prompt_template: str | None = Form(None),
):
    if not file and not text and not parsed_brief_json:
        raise HTTPException(status_code=400, detail="请上传文件或输入产品文字")

    # Support review resubmit: use pre-parsed brief directly
    brief = None
    if parsed_brief_json:
        try:
            brief = _json.loads(parsed_brief_json)
            # Validate expected keys exist
            if not isinstance(brief, dict):
                raise HTTPException(status_code=400, detail="parsed_brief_json 必须是 JSON 对象")
        except _json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="parsed_brief_json 格式无效")
    else:
        extracted_text = ""
        if file:
            if file.content_type and file.content_type not in ALLOWED_TYPES:
                raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}")
            # Check size before reading to avoid memory exhaustion
            if file.size and file.size > MAX_SIZE:
                raise HTTPException(status_code=400, detail="文件超过 20MB")
            content = await file.read()
            if len(content) > MAX_SIZE:
                raise HTTPException(status_code=400, detail="文件超过 20MB")
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            # Safe extension extraction — prevent path traversal
            safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename or "upload")
            ext = safe_filename.rsplit(".", 1)[-1].lower() if "." in safe_filename else "bin"
            if "/" in ext or "\\" in ext or len(ext) > 10:
                ext = "bin"
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

        extracted_text = _prepare_text_for_brief_parse(extracted_text)

        try:
            brief = await parse_brief_text(extracted_text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI 解析失败: {str(e)}")

        try:
            from app.db.session import SessionLocal
            pdb = SessionLocal()
            upsert_product_brief_for_project(pdb, project_id, brief)
            pdb.close()
        except Exception as e:
            logger.warning("Product library upsert failed: %s", e)
            try:
                pdb.close()
            except Exception:
                pass

    # Load brand profile memory — project_id first, then brand name fallback
    brand_context = ""
    bp_id = None
    try:
        from app.db.session import SessionLocal
        from app.models.brand_profile import BrandProfile
        bdb = SessionLocal()
        bp = bdb.query(BrandProfile).filter(BrandProfile.project_id == project_id).first()
        if not bp:
            # Cross-project fallback: search by product name
            brand_name = brief.get("product_name", "") if isinstance(brief, dict) else ""
            if brand_name:
                from sqlalchemy import func as sa_func
                bp = bdb.query(BrandProfile).filter(
                    BrandProfile.name.ilike(sa_func.concat('%', brand_name, '%'))
                ).first()
        if bp:
            brand_context = bp.to_prompt_context()
            brief["_brand_context"] = brand_context
            bp_id = bp.id
        bdb.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Brand profile lookup failed: {e}")

    quality_report = None

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

    # Inject inspiration template if provided
    if prompt_template:
        brief["_inspiration_context"] = prompt_template

    # Review check
    if not skip_review:
        questions = BriefReviewer.generate_questions(brief)
        required_missing = [q for q in questions if q["level"] == "required"]
        if required_missing:
            return {
                "needs_review": True, "parsed_brief": brief,
                "questions": questions, "compliance_warnings": compliance_warnings,
                "quality_report": quality_report,
                "generation": None, "elapsed_seconds": 0,
            }
        if questions:
            brief["_review_questions"] = questions

    if strategy_first:
        # 策略优先模式：只返回解析结果，不生成
        return {
            "needs_review": False,
            "parsed_brief": brief,
            "generation": None,
            "elapsed_seconds": 0,
        }

    if not brief.get("product_name"):
        raise HTTPException(status_code=422, detail="未能识别产品名称，请提供更详细的产品资料或回答追问")

    # Generate
    try:
        start = time.time()
        result = await agent.generate_all(project_id=project_id, brief=brief, platform_id=platform_id)
        elapsed = round(time.time() - start, 1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

    # Auto-save brand profile memory
    if bp_id:
        try:
            bdb2 = SessionLocal()
            bp2 = bdb2.query(BrandProfile).filter(BrandProfile.id == bp_id).first()
            if bp2:
                # Update with latest strategy insights
                strategy_ctx = brief.get("_strategy_context", "")
                if strategy_ctx:
                    bp2.tone_of_voice = bp2.tone_of_voice or brief.get("brand_style", "")
                    bp2.updated_at = __import__("datetime").datetime.utcnow()
                    bdb2.commit()
            bdb2.close()
        except Exception:
            pass

    # Auto-save to history
    try:
        from app.db.session import SessionLocal
        from app.db.crud_visual_asset_v2 import save_asset_plan
        db = SessionLocal()
        asset_plan = result.model_dump()
        save_asset_plan(db=db, project_id=project_id, asset_plan=asset_plan,
                        model_used=_history_model_used(asset_plan, getattr(agent._llm, '_model', 'unknown')), generation_seconds=int(elapsed))
        _ensure_canvas_image_elements(db, project_id, asset_plan)
        db.close()
    except Exception:
        pass

    # Optional image generation — fire-and-forget (async background)
    images = None
    if generate_images:
        _image_results[project_id] = {"status": "pending", "images": None}
        async def _generate_images_bg():
            try:
                imgs = await agent.generate_images_from_plan(result, provider="mige")
                _image_results[project_id] = {"status": "done", "images": imgs}
            except Exception as e:
                _image_results[project_id] = {"status": "error", "images": None, "error": str(e)}
        asyncio.create_task(_generate_images_bg())

    # Optional video generation
    videos = None
    if generate_videos:
        try:
            videos = await agent.generate_videos_from_plan(result, provider="mige")
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



# ── Strategy preview ──────────────────────────────────────────────────

from pydantic import BaseModel as PydanticBase

class StrategyPreviewRequest(PydanticBase):
    brief: dict
    platform_id: str | None = None


async def _parse_brief_from_request(
    file: UploadFile | None,
    text: str | None,
    parsed_brief_json: str | None,
) -> dict:
    """Shared brief parsing logic reused by sync and async endpoints."""
    if parsed_brief_json:
        try:
            brief = _json.loads(parsed_brief_json)
            if not isinstance(brief, dict):
                raise HTTPException(status_code=400, detail="parsed_brief_json 必须是 JSON 对象")
            return brief
        except _json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="parsed_brief_json 格式无效")

    extracted_text = ""
    if file:
        if file.content_type and file.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}")
        if file.size and file.size > MAX_SIZE:
            raise HTTPException(status_code=400, detail="文件超过 20MB")
        content = await file.read()
        if len(content) > MAX_SIZE:
            raise HTTPException(status_code=400, detail="文件超过 20MB")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename or "upload")
        ext = safe_filename.rsplit(".", 1)[-1].lower() if "." in safe_filename else "bin"
        if "/" in ext or "\\" in ext or len(ext) > 10:
            ext = "bin"
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

    extracted_text = _prepare_text_for_brief_parse(extracted_text)

    try:
        brief = await parse_brief_text(extracted_text)
        return brief
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析简报失败: {e}")



@router.post("/generate-async")
async def generate_async(
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
    """Async full generation: returns task_id immediately, poll for results."""
    if not file and not text and not parsed_brief_json:
        raise HTTPException(status_code=400, detail="请上传文件或输入产品文字")

    brief = await _parse_brief_from_request(file, text, parsed_brief_json)

    # Compliance check
    compliance_warnings = ComplianceChecker.check_brief(brief)

    # Merge user answers
    if answers:
        try:
            user_answers = _json.loads(answers)
            for field, answer in user_answers.items():
                if answer and answer.strip():
                    brief[field] = answer
        except _json.JSONDecodeError:
            pass

    # Review check
    if not skip_review:
        questions = BriefReviewer.generate_questions(brief)
        if questions:
            return {
                "needs_review": True,
                "questions": questions,
                "compliance_warnings": compliance_warnings,
            }

    # Spawn background generation
    task_id = str(uuid.uuid4())
    _async_gen_tasks[task_id] = {"status": "processing"}

    async def _run_generation():
        try:
            import time
            start = time.time()
            gt = GenerationTracker.get()
            progress = gt.create(task_id, total_steps=9)
            pn = brief.get('product_name', '未知产品')

            await progress.step("分析需求", "thinking", f"分析「{pn}」的市场定位和视觉需求...")
            await progress.step("策略规划", "thinking", "确定创意方向和视觉风格...")

            async def on_progress(step_label, step_status="generating", msg=""):
                await progress.step(step_label, step_status, msg)

            result = await asyncio.wait_for(agent.generate_all(
                project_id=project_id,
                brief=brief,
                platform_id=platform_id,
                progress_callback=on_progress,
            ), timeout=420)
            elapsed = int(time.time() - start)

            # Build response matching generate_from_document format
            gen_result = {
                "main_image": result.main_image.model_dump() if result.main_image else None,
                "white_bg": result.white_bg.model_dump() if result.white_bg else None,
                "scene_images": [s.model_dump() for s in (result.scene_images or [])],
                "selling_points": [s.model_dump() for s in (result.selling_points or [])],
                "video_scripts": [v.model_dump() for v in (result.video_scripts or [])],
                "ad_material": result.ad_material.model_dump() if result.ad_material else None,
            }

            try:
                from app.db.session import SessionLocal
                from app.db.crud_visual_asset_v2 import save_asset_plan
                db = SessionLocal()
                save_asset_plan(db=db, project_id=project_id, asset_plan=gen_result,
                                model_used=_history_model_used(gen_result, getattr(agent._llm, '_model', 'unknown')), generation_seconds=elapsed)
                _ensure_canvas_image_elements(db, project_id, gen_result)
                db.close()
            except Exception:
                pass

            # Quality evaluation via small-model scoring (multi-agent assessment)
            quality_report = None
            try:
                await progress.step("质量评估", "evaluating", "正在评估素材质量（构图/色彩/商业适用性）...")
                from app.services.quality_evaluator import evaluate_assets, report_to_dict
                qr = await evaluate_assets(brief=brief, generation_result=gen_result)
                quality_report = report_to_dict(qr)
            except Exception as qe:
                quality_report = {"error": str(qe)[:200]}

            await progress.done({"elapsed_seconds": elapsed})

            _async_gen_tasks[task_id] = {
                "status": "complete",
                "parsed_brief": brief,
                "generation": gen_result,
                "compliance_warnings": compliance_warnings,
                "elapsed_seconds": elapsed,
                "quality_check": quality_report,
            }
        except Exception as e:
            try:
                await progress.error(str(e))
            except Exception:
                pass
            _async_gen_tasks[task_id] = {"status": "error", "error": str(e)}

    asyncio.create_task(_run_generation())
    return {"task_id": task_id, "status": "processing"}


@router.post("/generation/task/{task_id}/cancel")
async def cancel_generation_task(task_id: str):
    task = _async_gen_tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.get("status") == "processing":
        task.update({
            "status": "cancelled",
            "cancelled": True,
            "spent": {"amount": 0, "currency": "USD"},
        })
        return task
    return {
        "status": task.get("status"),
        "cancelled": False,
        "spent": task.get("spent", {"amount": 0, "currency": "USD"}),
    }

@router.get("/generation/task/{task_id}")
async def poll_generation_task(task_id: str):
    """Poll async generation task status."""
    if task_id not in _async_gen_tasks:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return _async_gen_tasks[task_id]


@router.post("/strategy/preview")
async def strategy_preview(req: StrategyPreviewRequest):
    """生成创意策略预览 — 不生成素材，只返回策略方向供用户确认。

    Note: generate_visual_strategy was removed (2026-06-16). Strategy is now
    implicit in sub-generators. This endpoint returns a lightweight strategy
    derived from brief fields, suitable for pre-generation UI preview.
    """
    brief = req.brief
    product = brief.get("product_name", "产品")
    category = brief.get("category", "")
    selling = brief.get("selling_points", [])
    market = brief.get("target_market", [])

    strategy = {
        "visual_positioning": f"{category or product}专业视觉方案",
        "visual_style": brief.get("brand_style", "专业风格"),
        "selling_points_priority": [
            {"rank": i + 1, "point": sp, "rationale": "核心卖点"}
            for i, sp in enumerate(selling[:3])
        ],
        "brand_tone": "Professional",
        "audience_type": "B2B" if "B2B" in str(market) else "B2C",
        "key_differentiators": ", ".join(selling[:3]) if selling else product,
    }

    display = f"产品: {product} | 风格: {strategy['visual_style']} | 受众: {strategy['audience_type']}"

    return {
        "strategy": strategy,
        "display_context": display,
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
            "prompt": _history_prompt(r.asset_plan_json),
            "created_at": r.created_at.isoformat() if hasattr(r.created_at, 'isoformat') else str(r.created_at) if r.created_at else None,
        } for r in records]}
    finally:
        db.close()



@router.get("/project-images/{project_id}")
def get_project_images(project_id: int):
    """Poll for async image generation results."""
    result = _image_results.get(project_id, {})
    return {
        "status": result.get("status", "not_found"),
        "images": result.get("images"),
        "error": result.get("error"),
    }

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


# ── Quick Generate (T5: 快速生成直达画布) ──────────────────────────────────

class QuickGenerateRequest(BaseModel):
    prompt: str
    project_id: int = 2
    prompt_template: str | None = None
    reference_image_url: str | None = None  # Day 3.3: reference image for style matching
    image_provider: str | None = "dataeyes"
    image_model: str | None = None
    auto_model: bool = True
    brief: dict | None = None
    agent_mode: str | None = None


@router.post("/quick-generate")
async def quick_generate(req: QuickGenerateRequest):
    """
    T5: 快速生成直达画布 — Plan A
    用户输入prompt，直接生成画布，跳过AI解析和手动填写字段。

    工作流程：
    1. 将prompt包装成最小化brief（不调用LLM解析）
    2. 跳过review检查
    3. 直接调用generate_all生成六类素材
    4. 返回task_id，前端轮询结果
    """
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt不能为空")

    # Prefer parsed brief from homepage document/text parsing when available.
    # Fall back to a minimal prompt-derived brief for direct quick generation.
    if req.brief:
        brief = dict(req.brief)
        brief["_quick_generate_prompt"] = req.prompt
    else:
        brief = {
            "product_name": req.prompt[:50],  # Use first 50 chars as product name
            "category": "未分类",
            "specifications": [],
            "selling_points": [req.prompt],  # Full prompt as main selling point
            "target_market": [],
            "usage_scenarios": [],
            "brand_style": "",
            "_quick_generate_prompt": req.prompt,  # Keep original prompt for context
        }

    # Inject inspiration template if provided
    if req.prompt_template:
        brief["_inspiration_context"] = req.prompt_template

    try:
        from app.db.session import SessionLocal
        from app.models.brand_profile import BrandProfile
        bdb = SessionLocal()
        try:
            brand = bdb.query(BrandProfile).filter(BrandProfile.project_id == req.project_id).first()
            brand_context = _build_minimal_brand_prompt_context(brand)
            if brand_context:
                brief["_brand_context"] = brand_context
        finally:
            bdb.close()
    except Exception:
        pass

    # Day 3.3: Real vision analysis via DataEyesAI
    style_description = ""
    if req.reference_image_url:
        brief["_reference_image"] = req.reference_image_url
        try:
            vision_result = await vision_service.analyze(
                images=[req.reference_image_url],
                prompt="请详细分析这张参考图的视觉风格，包括：1.色调和配色方案 2.构图和布局 3.光影和氛围 4.设计风格（如极简、赛博朋克、复古等）5.关键视觉元素。用中文回答，控制在200字以内。",
                max_tokens=512,
                temperature=0.3,
            )
            if vision_result.get("success"):
                style_description = vision_result["content"]
        except Exception as e:
            # Vision failure is non-blocking — fall back to URL-only
            style_description = f"[参考图片: {req.reference_image_url}]"

        # Build augmented prompt with real style analysis
        if style_description:
            augmented = f"[参考风格分析] {style_description}\n\n[原需求] {req.prompt}\n\n请基于上述参考风格分析，生成同风格的视觉素材。"
        else:
            augmented = f"[参考风格: {req.reference_image_url}] 请分析这张参考图的视觉风格，生成同风格的视觉素材。原需求: {req.prompt}"
        brief["selling_points"] = [augmented]
        brief["_style_reference"] = True
        brief["_style_description"] = style_description

    # ── Modal routing: detect video intent ──
    user_prompt = (req.prompt or "").lower()
    if req.agent_mode == "video-gen":
        is_video_intent = True
    elif req.agent_mode == "image-gen":
        is_video_intent = False
    else:
        is_video_intent = any(kw in user_prompt for kw in [
            "视频", "video", "动画", "镜头", "运镜", "短片", "movie", "clip", "footage",
            "生成一段", "拍摄", "录制",
        ])

    # Spawn background generation (same pattern as generate-async)
    task_id = str(uuid.uuid4())
    _async_gen_tasks[task_id] = {"status": "processing"}

    async def _run_generation():
        try:
            start = time.time()
            gt = GenerationTracker.get()
            progress = gt.create(task_id, total_steps=8)

            await progress.step("分析需求", "thinking", f"分析「{req.prompt[:30]}...」的视觉需求")

            async def on_progress(step_label, step_status="generating", msg=""):
                await progress.step(step_label, step_status, msg)

            gen_result = await _generate_quick_asset_for_modality(req, brief, is_video_intent, progress)
            elapsed = int(time.time() - start)

            try:
                from app.db.session import SessionLocal
                from app.db.crud_visual_asset_v2 import save_asset_plan
                db = SessionLocal()
                save_asset_plan(db=db, project_id=req.project_id, asset_plan=gen_result,
                                model_used=_history_model_used(gen_result, getattr(agent._llm, '_model', 'unknown')), generation_seconds=elapsed)
                _ensure_canvas_image_elements(db, req.project_id, gen_result)
                db.close()
            except Exception:
                pass

            await progress.done({"elapsed_seconds": elapsed})
            _async_gen_tasks[task_id] = {
                "status": "complete",
                "parsed_brief": brief,
                "generation": gen_result,
                "elapsed_seconds": elapsed,
            }
        except Exception as e:
            error_message = str(e) or e.__class__.__name__
            _async_gen_tasks[task_id] = {"status": "error", "error": error_message}

    asyncio.create_task(_run_generation())
    return {"task_id": task_id, "status": "processing"}


class OrchestrateRequest(BaseModel):
    prompt: str | None = None
    project_id: int = 2
    brief: dict | None = None
    platforms: list[str] | None = None


@router.post("/generate/orchestrate")
async def generate_orchestrate(req: OrchestrateRequest):
    """真·十 Agent 编排:PM→Research→Brand→Copy→Visual→Image→Layout→Mockup→Compliance→Export。
    每个 Agent 通过 GenerationTracker SSE 上报具名进度;图片/Mockup 产物落库到画布。返回 task_id 轮询。
    """
    if not (req.prompt and req.prompt.strip()) and not req.brief:
        raise HTTPException(status_code=400, detail="请提供 prompt 或 brief")

    if req.brief:
        brief = dict(req.brief)
    else:
        brief = {
            "product_name": req.prompt[:50],
            "category": "未分类",
            "selling_points": [req.prompt],
            "description": req.prompt,
        }
    if req.platforms:
        brief["platforms"] = req.platforms
    if req.prompt:
        brief.setdefault("description", req.prompt)

    task_id = str(uuid.uuid4())
    _async_gen_tasks[task_id] = {"status": "processing"}
    # 同步创建进度任务,避免前端订阅 SSE 时任务尚未建立(竞态 → 404 → 进度卡死)。
    # total_steps≈每 Agent running+done 两事件 × 10。
    progress = GenerationTracker.get().create(task_id, total_steps=20)

    async def _run_orchestration():
        try:
            from app.agents.orchestrator.pipeline import run_pipeline, build_generation_result
            from app.agents.orchestrator.ten_agents import build_default_agents
            start = time.time()

            async def on_progress(name, status="generating", msg=""):
                await progress.step(name, status, msg)

            result = await run_pipeline(
                brief, req.project_id, progress_callback=on_progress,
                agents=build_default_agents(), timeout_seconds=45.0,
            )
            gen_result = build_generation_result(brief, result.get("results", {}))
            elapsed = int(time.time() - start)

            try:
                from app.db.session import SessionLocal
                from app.db.crud_visual_asset_v2 import save_asset_plan
                db = SessionLocal()
                save_asset_plan(
                    db=db, project_id=req.project_id, asset_plan=gen_result,
                    model_used=(gen_result.get("main_image") or {}).get("model") or "orchestrator",
                    generation_seconds=elapsed,
                )
                _ensure_canvas_image_elements(db, req.project_id, gen_result)
                db.close()
            except Exception:
                pass

            await progress.done({"elapsed_seconds": elapsed})
            _async_gen_tasks[task_id] = {
                "status": "complete",
                "parsed_brief": brief,
                "generation": gen_result,
                "agents": result.get("agents", []),
                "elapsed_seconds": elapsed,
            }
        except Exception as e:
            _async_gen_tasks[task_id] = {"status": "error", "error": str(e) or e.__class__.__name__}

    asyncio.create_task(_run_orchestration())
    return {"task_id": task_id, "status": "processing"}
