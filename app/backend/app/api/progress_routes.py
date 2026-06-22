"""
Progress SSE streaming — real-time generation progress via GenerationTracker.

Replaces the old fake-step simulation with actual progress events
emitted from the generation loop itself.
"""
import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.generation_tracker import GenerationTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])


@router.get("/{task_id}/stream")
async def stream_progress(task_id: str):
    """SSE endpoint: streams real-time generation progress events.

    Events:
        event: progress — {step, percent, status, message}
        event: heartbeat — {message} (every 30s to keep connection alive)
        event: done — {step: "完成", percent: 100}
        event: error — {message}

    The client connects to this endpoint after receiving a task_id
    from POST /api/v1/generate-async. Progress events are emitted
    in real-time as the generation loop executes.
    """
    tracker = GenerationTracker.get()

    # Verify task exists (or wait briefly for it to be created)
    progress = tracker.get_task(task_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")

    async def event_generator():
        try:
            async for event in tracker.subscribe(task_id):
                event_type = event.get("type", "progress")
                event_data = json.dumps(event, ensure_ascii=False)

                if event_type == "error":
                    yield f"event: error\ndata: {event_data}\n\n"
                    break
                elif event_type == "heartbeat":
                    yield f"event: heartbeat\ndata: {event_data}\n\n"
                elif event.get("status") == "done":
                    yield f"event: done\ndata: {event_data}\n\n"
                    break
                else:
                    yield f"event: progress\ndata: {event_data}\n\n"
        except Exception as e:
            logger.error(f"SSE stream error for task {task_id}: {e}")
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # Cleanup after streaming completes
            tracker.remove(task_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/{task_id}/status")
async def get_progress_status(task_id: str):
    """Quick status check without SSE streaming."""
    tracker = GenerationTracker.get()
    progress = tracker.get_task(task_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return progress.to_dict()
