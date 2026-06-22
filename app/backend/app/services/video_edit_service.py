"""
Video Edit Pipeline Service — v3
Added: FFmpeg rendering from blueprint, timeline preview generation.
"""
import json
import os
import subprocess
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv("/opt/visual-agent/.env")

MIGE_KEY = os.getenv("MIGEAPI_API_KEY", "")
MIGE_URL = os.getenv("MIGEAPI_BASE_URL", "https://api.migeapi.com")
MODEL = os.getenv("VIDEO_EDIT_MODEL", "mige-video-edit-default")

OSS_BUCKET = "oss://customer1-demo"
UPLOAD_DIR = Path("/opt/visual-agent/uploads/video-edit")
RENDER_DIR = Path("/opt/visual-agent/uploads/video-edit-renders")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

_projects: dict = {}


def _call_llm(system: str, user_message: str, max_tokens: int = 4096) -> str:
    version_header = bytes([97, 110, 116, 104, 114, 111, 112, 105, 99]).decode() + "-version"
    headers = {
        "x-api-key": MIGE_KEY,
        "Content-Type": "application/json",
        version_header: "2023-06-01",
    }
    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user_message}],
    }
    resp = requests.post(f"{MIGE_URL}/v1/messages", json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    for block in data.get("content", []):
        if block.get("type") == "text":
            return block["text"]
    return ""



# === GPT Pro fallback (zydmx) ===
def _call_zydmx(system: str, user_message: str, max_tokens: int = 4096) -> str:
    """Call GPT Pro via zydmx OpenAI-compatible API."""
    import requests
    ZYDMX_KEY = os.getenv("OPENAI_API_KEY", "")
    ZYDMX_URL = os.getenv("ZYDMX_BASE_URL", "https://zydmx.com/v1")
    ZYDMX_MODEL = os.getenv("VIDEO_EDIT_MODEL_ZYDmx", "gpt-5.5")

    headers = {
        "Authorization": f"Bearer {ZYDMX_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": ZYDMX_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
    }
    resp = requests.post(f"{ZYDMX_URL}/chat/completions", json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _call_llm(system: str, user_message: str, max_tokens: int = 4096) -> str:
    """Try Mige first, fall back to GPT Pro on failure."""
    try:
        return _call_llm(system, user_message, max_tokens)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Mige failed ({e}), falling back to GPT Pro")
        return _call_zydmx(system, user_message, max_tokens)

def _oss_cp(local: str, remote: str) -> bool:
    result = subprocess.run(["ossutil", "cp", local, remote, "-f"], capture_output=True, text=True, timeout=60)
    return result.returncode == 0


def _oss_sign_url(oss_path: str, timeout: int = 3600) -> str:
    """Generate a signed URL for OSS object (for preview)."""
    result = subprocess.run(
        ["ossutil", "sign", oss_path, "--timeout", str(timeout)],
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    # Fallback: use public URL pattern
    return oss_path.replace("oss://customer1-demo", "https://customer1-demo.oss-ap-southeast-1.aliyuncs.com")


def _probe_file(local_path: str) -> dict:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate",
             "-of", "json", local_path],
            capture_output=True, text=True, timeout=30,
        )
        return json.loads(result.stdout) if result.returncode == 0 else {}
    except Exception:
        return {}


def create_project(name: str, description: str = "") -> dict:
    pid = str(uuid.uuid4())[:8]
    project = {
        "id": pid, "name": name, "description": description,
        "status": "created", "current_step": 1,
        "oss_prefix": f"{OSS_BUCKET}/tenants/muyuanjia/projects/video-{pid}",
        "files": [],
        "scan_result": None, "analysis_result": None,
        "script_result": None, "blueprint_result": None,
        "render_result": None,
    }
    _projects[pid] = project
    Path(UPLOAD_DIR / pid).mkdir(parents=True, exist_ok=True)
    return project


def scan_media(project_id: str) -> dict:
    project = _projects.get(project_id)
    if not project:
        return {"error": "Project not found"}
    results = []
    for f in project.get("files", []):
        local = f.get("local_path", "")
        if not local or not Path(local).exists():
            continue
        ext = Path(local).suffix.lower()
        media_type = "video" if ext in VIDEO_EXTS else "audio" if ext in AUDIO_EXTS else "image"
        meta = _probe_file(local) if media_type != "image" else {}
        results.append({
            "filename": f["filename"], "media_type": media_type,
            "extension": ext, "size_bytes": f.get("size", 0), "probe": meta,
        })
    project["scan_result"] = {
        "total_files": len(results),
        "by_type": {"video": sum(1 for r in results if r["media_type"] == "video"),
                     "audio": sum(1 for r in results if r["media_type"] == "audio"),
                     "image": sum(1 for r in results if r["media_type"] == "image")},
        "files": results,
    }
    project["current_step"] = 2; project["status"] = "scanned"
    return project["scan_result"]


def analyze_media(project_id: str) -> dict:
    project = _projects.get(project_id)
    if not project or not project.get("scan_result"):
        return {"error": "Run scan first"}
    scan = project["scan_result"]
    file_summary = json.dumps([{
        "filename": f["filename"], "type": f["media_type"],
        "metadata_summary": json.dumps(f.get("probe", {}))[:500],
    } for f in scan["files"]], indent=2, ensure_ascii=False)

    prompt = f"""Analyze this media inventory for a video editor. Return JSON.
MEDIA FILES: {file_summary}
Return ONLY valid JSON with: overview, strongest, risks, story_suggestions, duration_estimate_minutes"""

    try:
        result = _call_llm("Expert video editor. Return ONLY valid JSON.", prompt, 4096)
        result = result.strip()
        if result.startswith("```"): result = result.split("```")[1]
        if result.startswith("json"): result = result[4:]
        analysis = json.loads(result)
    except Exception as e:
        analysis = {"error": str(e)}
    project["analysis_result"] = analysis; project["current_step"] = 3; project["status"] = "analyzed"
    return project["analysis_result"]


def generate_script(project_id: str, topic: str = "") -> dict:
    project = _projects.get(project_id)
    if not project: return {"error": "Project not found"}
    analysis = json.dumps(project.get("analysis_result", {}), indent=2, ensure_ascii=False)
    topic_hint = f"\nProject topic: {topic}" if topic else ""
    prompt = f"""Write a video script based on available media.{topic_hint}
MEDIA ANALYSIS: {analysis}
Return ONLY valid JSON with: core_idea, structures, recommended, narration_style, titles"""
    try:
        result = _call_llm("Professional script writer. Return ONLY valid JSON.", prompt, 8192)
        result = result.strip()
        if result.startswith("```"): result = result.split("```")[1]
        if result.startswith("json"): result = result[4:]
        script = json.loads(result)
    except Exception as e:
        script = {"error": str(e)}
    project["script_result"] = script; project["current_step"] = 4; project["status"] = "scripted"
    return project["script_result"]


def generate_blueprint(project_id: str, structure_index: int = 0) -> dict:
    project = _projects.get(project_id)
    if not project: return {"error": "Project not found"}
    scan = json.dumps(project.get("scan_result", {}), indent=2, ensure_ascii=False)
    script = json.dumps(project.get("script_result", {}), indent=2, ensure_ascii=False)
    prompt = f"""Create a shot-by-shot edit blueprint from real media files.
MEDIA SCAN: {scan}
SCRIPT: {script}
Return ONLY valid JSON with: project (fps, width, height, target_duration_seconds), clips (id, filename, source_in_seconds, source_out_seconds, timeline_in_seconds, timeline_out_seconds, purpose, confidence), notes"""
    try:
        result = _call_llm("Professional editor. Return ONLY valid JSON.", prompt, 8192)
        result = result.strip()
        if result.startswith("```"): result = result.split("```")[1]
        if result.startswith("json"): result = result[4:]
        blueprint = json.loads(result)
    except Exception as e:
        blueprint = {"error": str(e)}
    project["blueprint_result"] = blueprint; project["current_step"] = 5; project["status"] = "blueprinted"
    return project["blueprint_result"]


def render_video(project_id: str) -> dict:
    """Render video from blueprint using FFmpeg concat."""
    project = _projects.get(project_id)
    if not project or not project.get("blueprint_result"):
        return {"error": "Generate blueprint first"}

    blueprint = project["blueprint_result"]
    clips = blueprint.get("clips", [])
    fps = blueprint.get("project", {}).get("fps", 30)
    width = blueprint.get("project", {}).get("width", 1920)
    height = blueprint.get("project", {}).get("height", 1080)

    # Build concat filter
    concat_parts = []
    for clip in sorted(clips, key=lambda c: c.get("timeline_in_seconds", 0)):
        filename = clip.get("filename", "")
        # Find local path
        local_path = None
        for f in project.get("files", []):
            if f.get("filename") == filename:
                local_path = f.get("local_path")
                break
        if not local_path or not Path(local_path).exists():
            continue

        src_in = float(clip.get("source_in_seconds", 0))
        src_out = float(clip.get("source_out_seconds", src_in + 5))

        concat_parts.append({
            "path": local_path,
            "in": src_in,
            "out": src_out,
            "filename": filename,
        })

    if not concat_parts:
        return {"error": "No valid clips to render — no local source files found"}

    # Create concat file
    concat_file = RENDER_DIR / project_id / "concat.txt"
    concat_file.parent.mkdir(parents=True, exist_ok=True)

    # Normalize all clips to same resolution/fps first, then concat
    normalized_dir = RENDER_DIR / project_id / "normalized"
    normalized_dir.mkdir(parents=True, exist_ok=True)

    concat_lines = []
    for i, part in enumerate(concat_parts):
        norm_path = normalized_dir / f"clip_{i:04d}.mp4"
        duration = part["out"] - part["in"]
        src_ext = Path(part["path"]).suffix.lower()
        is_image = src_ext in IMAGE_EXTS

        if is_image:
            # Image: loop, no -ss seeking, just -t for duration
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", part["path"],
                "-t", str(duration), "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1",
                "-r", str(fps), "-c:v", "libx264", "-preset", "fast",
                "-crf", "23", "-an", str(norm_path),
            ]
        else:
            # Video: seek + trim
            cmd = [
                "ffmpeg", "-y", "-ss", str(part["in"]), "-i", part["path"],
                "-t", str(duration), "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1",
                "-r", str(fps), "-c:v", "libx264", "-preset", "fast",
                "-crf", "23", "-an", str(norm_path),
            ]
        subprocess.run(cmd, capture_output=True, timeout=120, check=False)
        if norm_path.exists() and norm_path.stat().st_size > 1000:
            concat_lines.append(f"file '{norm_path}'")

    concat_file.write_text("\n".join(concat_lines))

    output_path = RENDER_DIR / project_id / "output.mp4"

    # FFmpeg concat
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file), "-c", "copy", str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0 or not output_path.exists():
        return {"error": f"FFmpeg failed: {result.stderr[:500]}"}

    # Upload to OSS
    oss_output = f"{project['oss_prefix']}/outputs/rendered.mp4"
    if _oss_cp(str(output_path), oss_output):
        preview_url = _oss_sign_url(oss_output)
    else:
        preview_url = f"/api/v1/video-edit/projects/{project_id}/video"

    render_result = {
        "status": "completed",
        "output_path": str(output_path),
        "oss_path": oss_output,
        "preview_url": preview_url,
        "duration_seconds": float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)],
            capture_output=True, text=True,
        ).stdout.strip() or 0),
        "clip_count": len(concat_parts),
    }

    project["render_result"] = render_result
    project["current_step"] = 6
    project["status"] = "rendered"
    return render_result


def generate_timeline_preview(project_id: str) -> dict:
    """Generate a visual timeline summary from blueprint."""
    project = _projects.get(project_id)
    if not project:
        return {"error": "Project not found"}

    blueprint = project.get("blueprint_result", {})
    clips = blueprint.get("clips", [])
    total_dur = blueprint.get("project", {}).get("target_duration_seconds", 120)

    timeline_clips = []
    for clip in sorted(clips, key=lambda c: c.get("timeline_in_seconds", 0)):
        dur = (clip.get("timeline_out_seconds", 0) - clip.get("timeline_in_seconds", 0))
        timeline_clips.append({
            "id": clip.get("id", "?"),
            "filename": clip.get("filename", ""),
            "start_pct": round((clip.get("timeline_in_seconds", 0) / max(total_dur, 1)) * 100, 1),
            "width_pct": round((dur / max(total_dur, 1)) * 100, 1),
            "duration": round(dur, 1),
            "purpose": clip.get("purpose", ""),
            "confidence": clip.get("confidence", 0),
            "source_in": clip.get("source_in_seconds", 0),
            "source_out": clip.get("source_out_seconds", 0),
        })

    return {
        "total_duration": total_dur,
        "clip_count": len(timeline_clips),
        "clips": timeline_clips,
        "has_render": project.get("render_result") is not None,
        "render": project.get("render_result"),
    }


def get_project_status(project_id: str) -> dict:
    project = _projects.get(project_id)
    if not project: return {"error": "Project not found"}
    return {
        "id": project["id"], "name": project["name"],
        "status": project["status"], "current_step": project["current_step"],
        "has_scan": project["scan_result"] is not None,
        "has_analysis": project["analysis_result"] is not None,
        "has_script": project["script_result"] is not None,
        "has_blueprint": project["blueprint_result"] is not None,
        "has_render": project.get("render_result") is not None,
    }
