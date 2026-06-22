"""Platform & scene template API routes. PRD 7.1, 7.7"""
from fastapi import APIRouter

from app.services.platform_specs import get_all_specs, get_all_scenes, get_platform_spec, get_scene

router = APIRouter(prefix="/api/v1", tags=["platforms"])


@router.get("/platforms")
async def list_platforms():
    """返回所有支持的平台及规格。"""
    return {"platforms": list(get_all_specs().keys()), "specs": get_all_specs()}


@router.get("/platforms/{platform_id}")
async def get_platform(platform_id: str):
    """获取单个平台规格。"""
    spec = get_platform_spec(platform_id)
    if not spec:
        return {"error": f"Unknown platform: {platform_id}"}, 404
    return spec


@router.get("/scenes")
async def list_scenes():
    """返回10个行业场景模板（PRD 7.1）。"""
    return {"scenes": get_all_scenes()}


@router.get("/scenes/{scene_id}")
async def get_scene_detail(scene_id: str):
    """获取单个场景模板详情。"""
    scene = get_scene(scene_id)
    if not scene:
        return {"error": f"Unknown scene: {scene_id}"}, 404
    return scene
