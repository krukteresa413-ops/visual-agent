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


async def _download_video(url: str, task_id: str) -> str | None:
    """Download video to local storage. Returns local path or None."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    import uuid
    filename = f"video_{uuid.uuid4().hex[:12]}.mp4"
    filepath = os.path.join(UPLOAD_DIR, filename)
    try:
        async with httpx.AsyncClient(timeout=300, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                local_url = f"/uploads/generated/{filename}"
                return local_url
    except Exception:
        pass
    return None


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

            # Download video
            local_url = await _download_video(video_url, task.provider_task_id)
            task.video_url = video_url
            task.local_path = local_url
            task.status = "succeeded"
            db.commit()
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
