"""
视觉任务 API 路由。
PRD 6.1 用户旅程 Step 4-6 的后端实现。
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.services.visual_agent import VisualAgent

router = APIRouter(prefix="/api/v1/visual-tasks", tags=["visual-tasks"])

agent = VisualAgent()


class VisualTaskRequest(BaseModel):
    task_types: list = None
    project_id: int
    brief: Dict[str, Any]


@router.post("/main-image")
async def generate_main_image(req: VisualTaskRequest):
    """PRD 8.3：生成主图方案"""
    try:
        result = await agent.generate_main_image(req.brief)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/white-bg")
async def generate_white_bg(req: VisualTaskRequest):
    """PRD 8.4：生成白底图方案"""
    try:
        result = await agent.generate_white_bg(req.brief)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/scene-images")
async def generate_scene_images(req: VisualTaskRequest):
    """PRD 8.5：生成场景图方案"""
    try:
        result = await agent.generate_scene_images(req.brief)
        return [item.model_dump() for item in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/selling-points")
async def generate_selling_points(req: VisualTaskRequest):
    """PRD 8.6：生成卖点图模块"""
    try:
        result = await agent.generate_selling_points(req.brief)
        return [item.model_dump() for item in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/video-scripts")
async def generate_video_scripts(req: VisualTaskRequest):
    """PRD 8.7：生成短视频脚本"""
    try:
        result = await agent.generate_video_scripts(req.brief)
        return [item.model_dump() for item in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/ad-material")
async def generate_ad_material(req: VisualTaskRequest):
    """PRD 8.8：生成广告素材方案"""
    try:
        result = await agent.generate_ad_material(req.brief)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/generate-all")
async def generate_all(req: VisualTaskRequest):
    """PRD 5.1：一次生成六类素材方案"""
    try:
        result = await agent.generate_all(
            project_id=req.project_id,
            task_types=req.task_types,
            brief=req.brief,
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

@router.post("/generate-all-and-save")
async def generate_all_and_save(req: VisualTaskRequest):
    """PRD 5.1：生成六类素材方案并保存到数据库"""
    from app.db.session import SessionLocal
    from app.db.crud_visual_asset import create_visual_asset_plan
    from app.schemas.visual_asset_plan import VisualAssetPlanCreate
    import json

    try:
        result = await agent.generate_all(
            project_id=req.project_id,
            task_types=req.task_types,
            brief=req.brief,
        )
        plan_dict = result.model_dump()

        db = SessionLocal()
        try:
            db_plan = create_visual_asset_plan(db, VisualAssetPlanCreate(
                project_id=req.project_id,
            task_types=req.task_types,
                main_image_json=json.dumps(plan_dict["main_image"]),
                white_bg_json=json.dumps(plan_dict["white_bg"]),
                scene_images_json=json.dumps(plan_dict["scene_images"]),
                selling_points_json=json.dumps(plan_dict["selling_points"]),
                video_scripts_json=json.dumps(plan_dict["video_scripts"]),
                ad_material_json=json.dumps(plan_dict["ad_material"]),
            ))
            return {"id": db_plan.id, "project_id": db_plan.project_id,
                    "main_image_json": db_plan.main_image_json,
                    "white_bg_json": db_plan.white_bg_json,
                    "scene_images_json": db_plan.scene_images_json,
                    "selling_points_json": db_plan.selling_points_json,
                    "video_scripts_json": db_plan.video_scripts_json,
                    "ad_material_json": db_plan.ad_material_json}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

@router.get("/export/{project_id}")
def export_markdown(project_id: int):
    """导出项目 visual_asset_plan 为 Markdown"""
    from app.db.session import SessionLocal
    from app.services.markdown_exporter import export_to_markdown
    from fastapi.responses import PlainTextResponse
    db = SessionLocal()
    try:
        md = export_to_markdown(db, project_id)
        if md is None:
            raise HTTPException(status_code=404, detail="No visual asset plan found")
        return PlainTextResponse(content=md, media_type="text/markdown; charset=utf-8")
    finally:
        db.close()

@router.get("/projects/{project_id}/export/markdown")
def export_as_markdown(project_id: int):
    """PRD：支持复制 Markdown。获取项目最新生成结果并转为 Markdown。"""
    from app.db.session import SessionLocal
    from app.db.crud_visual_asset_v2 import get_latest_by_project
    from app.services.exporter import to_markdown

    db = SessionLocal()
    try:
        record = get_latest_by_project(db=db, project_id=project_id)
        if not record:
            raise HTTPException(status_code=404, detail="该项目尚无生成结果")
        md_content = to_markdown(record.asset_plan)
        return {"project_id": project_id, "markdown": md_content}
    finally:
        db.close()

@router.post('/generate-all-fast')
async def generate_all_fast(req: VisualTaskRequest):
    try:
        result = await agent.generate_all(
            project_id=req.project_id,
            task_types=req.task_types,
            brief=req.brief,
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'生成失败: {str(e)}')

@router.get('/generations/{generation_id}')
def get_generation_detail(generation_id: int):
    from app.db.session import SessionLocal
    from app.models.visual_asset import VisualAsset
    db = SessionLocal()
    try:
        r = db.query(VisualAsset).filter(VisualAsset.id == generation_id).first()
        if not r: raise HTTPException(status_code=404, detail='Not found')
        return {'id':r.id,'project_id':r.project_id,'asset_plan':r.asset_plan,'model_used':r.model_used,'generation_seconds':r.generation_seconds,'created_at':r.created_at.isoformat() if r.created_at else None}
    finally: db.close()

@router.get('/projects/{project_id}/export/docx')
def export_as_docx(project_id: int):
    from app.db.session import SessionLocal
    from app.db.crud_visual_asset_v2 import get_latest_by_project
    from app.services.exporter_docx import to_docx
    from fastapi.responses import StreamingResponse
    import io
    db = SessionLocal()
    try:
        r = get_latest_by_project(db=db, project_id=project_id)
        if not r: raise HTTPException(status_code=404, detail='No generation found')
        docx_bytes = to_docx(r.asset_plan)
        return StreamingResponse(io.BytesIO(docx_bytes), media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', headers={'Content-Disposition': f'attachment; filename=visual_plan_project_{project_id}.docx'})
    finally: db.close()

@router.get('/platform-specs')
def get_platform_specs():
    from app.services.platform_specs import get_all_specs
    return get_all_specs()

@router.get('/templates')
def list_industry_templates():
    from app.services.industry_templates import list_templates
    return list_templates()

@router.get('/templates/{industry}')
def get_industry_template(industry: str):
    from app.services.industry_templates import get_template
    t = get_template(industry)
    if not t: raise HTTPException(status_code=404, detail=f'未知行业: {industry}')
    return t

class VariantRequest(BaseModel):
    asset_type: str
    original: dict
    brief: dict

@router.post('/generate-variants')
async def generate_variants_endpoint(req: VariantRequest):
    variants = await agent.generate_variants(asset_type=req.asset_type, original=req.original, brief=req.brief)
    return {'asset_type': req.asset_type, 'variants': variants}
