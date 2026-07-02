"""Video task polling worker (P2-11 gap).

Runs as a background task in the FastAPI app.
- Scans DB for submitted/polling tasks
- Polls the vendor for status
- On success: downloads video, saves local path, updates DB
- On failure: records error
- Recovers unfinished tasks on startup
"""
import asyncio
import json
import os
import httpx
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.video_task import VideoTask
from app.services.video_generation_service import DataEyesAIVideoProvider

UPLOAD_DIR = "/opt/visual-agent/uploads/generated"
POLL_INTERVAL = 10  # seconds between polls
MAX_POLLS = 120      # max polls per task (20 minutes)


async def _download_video(url: str, task_id: str, *, tenant_id=None, project_id=None) -> str | None:
    """Download video and persist via storage 抽象层(O1). Returns URL or None."""
    from app.services.storage import get_storage
    try:
        async with httpx.AsyncClient(timeout=300, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return await get_storage().save_bytes(
                    resp.content, tenant_id=tenant_id, project_id=project_id,
                    category="generated", ext="mp4", content_type="video/mp4",
                )
    except Exception:
        pass
    return None


def _seed_video_to_canvas(task: VideoTask, db: Session) -> None:
    """成功后把视频作为元素落到项目画布(CanvasState)。失败不影响任务状态。"""
    if not task.project_id or not (task.local_path or task.video_url):
        return
    try:
        from app.api.unified_generation_routes import _ensure_canvas_image_elements
        _ensure_canvas_image_elements(db, int(task.project_id), {
            "video": {
                "url": task.local_path or task.video_url,
                "duration": task.duration,
                "task_id": task.provider_task_id,
            }
        }, canvas_id=task.canvas_id)   # Phase C Step3b: 落回发起时的画布
    except Exception:
        pass


async def poll_single_task(task: VideoTask, db: Session) -> bool:
    """Poll a single video task. Returns True if terminal (success/fail)."""
    provider = DataEyesAIVideoProvider()
    vendor = provider.VENDORS.get(task.vendor)
    if not vendor:
        task.status = "failed"
        task.error_message = f"Unknown vendor: {task.vendor}"
        db.commit()
        return True

    route = vendor["route"]
    auth = vendor["auth_scheme"]
    client = provider._get_client(auth)

    try:
        # Build poll request per vendor
        if task.vendor == "jimeng":
            poll_path = f"{route}?Action=CVSync2AsyncGetResult&Version=2022-08-31"
            poll_body = {"req_key": task.model, "task_id": task.provider_task_id}
            resp = await client.post(poll_path, json=poll_body)
        else:
            poll_path = f"{route}{vendor['poll_path'](task.provider_task_id)}"
            resp = await client.get(poll_path)

        if resp.status_code >= 400:
            task.poll_count += 1
            db.commit()
            return task.poll_count >= MAX_POLLS

        data = resp.json()
        status = vendor["parse_status"](data)

        if status in vendor["success_statuses"]:
            video_url = vendor["parse_video_url"](data)
            if not video_url:
                task.status = "failed"
                task.error_message = "No video URL in success response"
                db.commit()
                return True

            # Download video (O1: 落盘按项目分区；tenant 从 Project 派生，孤儿任务→None→shared/)
            from app.services.tenant_resolver import resolve_tenant_id
            _tid = resolve_tenant_id(task.project_id, db=db)
            local_url = await _download_video(video_url, task.provider_task_id, tenant_id=_tid, project_id=task.project_id)
            task.video_url = video_url
            task.local_path = local_url
            task.status = "succeeded"
            db.commit()
            _seed_video_to_canvas(task, db)
            return True

        elif status in ("failed", "FAILED", "ERROR", "expired", "not_found"):
            task.status = "failed"
            task.error_message = f"Vendor status: {status}"
            db.commit()
            return True

        # Still running — increment and continue
        task.poll_count += 1
        task.status = "polling"
        db.commit()
        return task.poll_count >= MAX_POLLS

    except Exception as e:
        task.poll_count += 1
        task.error_message = str(e)[:500]
        db.commit()
        return task.poll_count >= MAX_POLLS


async def video_polling_worker():
    """Main polling loop — runs as background task."""
    while True:
        db = SessionLocal()
        try:
            pending = db.query(VideoTask).filter(
                VideoTask.status.in_(["submitted", "polling"])
            ).all()

            for task in pending:
                try:
                    terminal = await poll_single_task(task, db)
                    if terminal and task.poll_count >= MAX_POLLS:
                        task.status = "failed"
                        task.error_message = task.error_message or "Max polls reached"
                        db.commit()
                except Exception:
                    db.rollback()

        except Exception:
            db.rollback()
        finally:
            db.close()

        await asyncio.sleep(POLL_INTERVAL)


def recover_unfinished_tasks():
    """Mark any in-progress tasks as submitted for re-polling on startup."""
    db = SessionLocal()
    try:
        stuck = db.query(VideoTask).filter(
            VideoTask.status.in_(["submitted", "polling"])
        ).all()
        for t in stuck:
            t.status = "submitted"
            t.poll_count = 0
        db.commit()
        return len(stuck)
    finally:
        db.close()
