"""Video Edit Pipeline API Routes — v3."""
import re
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from app.services.video_edit_service import (
    create_project, scan_media, analyze_media,
    generate_script, generate_blueprint, render_video,
    generate_timeline_preview, get_project_status,
    _oss_cp, _projects, RENDER_DIR,
)

router = APIRouter(prefix="/api/v1/video-edit", tags=["video-edit"])

UPLOAD_DIR = Path("/opt/visual-agent/uploads/video-edit")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAFE_VIDEO_EDIT_FILENAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _safe_video_edit_filename(filename: str | None) -> str:
    if not filename or "/" in filename or "\\" in filename or not SAFE_VIDEO_EDIT_FILENAME_RE.fullmatch(filename):
        raise HTTPException(status_code=400, detail="invalid filename")
    if filename in {".", ".."}:
        raise HTTPException(status_code=400, detail="invalid filename")
    return filename


@router.post("/projects")
async def api_create_project(name: str = Form(...), description: str = Form("")):
    return create_project(name, description)


@router.post("/projects/{project_id}/upload")
async def api_upload_files(project_id: str, files: list[UploadFile] = File(...)):
    project = _projects.get(project_id)
    if not project: raise HTTPException(404, "Project not found")
    project_dir = UPLOAD_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    uploaded = []
    for f in files:
        safe_name = _safe_video_edit_filename(f.filename)
        local_path = (project_dir / safe_name).resolve()
        if local_path.parent != project_dir.resolve():
            raise HTTPException(status_code=400, detail="invalid filename")
        with open(local_path, "wb") as buffer:
            shutil.copyfileobj(f.file, buffer)
        oss_path = f"{project['oss_prefix']}/source/{safe_name}"
        _oss_cp(str(local_path), oss_path)
        uploaded.append({
            "filename": safe_name, "local_path": str(local_path),
            "oss_path": oss_path, "size": local_path.stat().st_size,
        })
    project["files"].extend(uploaded)
    return {"uploaded": len(uploaded), "files": uploaded}


@router.post("/projects/{project_id}/scan")
async def api_scan(project_id: str):
    return scan_media(project_id)


@router.post("/projects/{project_id}/analyze")
async def api_analyze(project_id: str):
    return analyze_media(project_id)


@router.post("/projects/{project_id}/script")
async def api_script(project_id: str, topic: str = Form("")):
    return generate_script(project_id, topic)


@router.post("/projects/{project_id}/blueprint")
async def api_blueprint(project_id: str, structure_index: int = 0):
    return generate_blueprint(project_id, structure_index)


@router.post("/projects/{project_id}/render")
async def api_render(project_id: str):
    """Render video from blueprint using FFmpeg."""
    result = render_video(project_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(500, result["error"])
    return result


@router.post("/demo")
async def api_create_demo_project():
    """Create a demo project with built-in example video."""
    import shutil, os
    from app.services.video_edit_service import create_project

    demo_video = "/opt/visual-agent/static/demo/shoe_video.mp4"
    if not os.path.exists(demo_video):
        raise HTTPException(status_code=404, detail="Demo video not found")

    project = create_project("范例项目 · 轻量跑鞋", "内置演示项目")
    pid = project["id"]; from pathlib import Path; dest_dir = Path("/opt/visual-agent/uploads/video-edit") / pid
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy(demo_video, os.path.join(dest_dir, "shoe_video.mp4"))

    return {"project_id": pid, "name": "范例项目 · 轻量跑鞋", "files": ["shoe_video.mp4"]}

@router.get("/projects/{project_id}/timeline")
async def api_timeline(project_id: str):
    """Get visual timeline preview data."""
    result = generate_timeline_preview(project_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/projects/{project_id}/video")
async def api_video(project_id: str):
    """Serve rendered video file."""
    project = _projects.get(project_id)
    if not project or not project.get("render_result"):
        raise HTTPException(404, "No rendered video")
    output_path = project["render_result"].get("output_path")
    if not output_path or not Path(output_path).exists():
        raise HTTPException(404, "Render file not found")
    return FileResponse(output_path, media_type="video/mp4")


@router.get("/projects/{project_id}/status")
async def api_status(project_id: str):
    return get_project_status(project_id)


@router.get("/projects/{project_id}")
async def api_get(project_id: str):
    project = _projects.get(project_id)
    if not project: raise HTTPException(404, "Project not found")
    return project
