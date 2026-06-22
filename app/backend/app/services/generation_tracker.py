"""
Generation Progress Tracker — real-time progress for SSE streaming.

Replaces the old fake-step simulation with actual progress events
emitted from the generation loop itself.

Architecture:
  generate_all()                        SSE endpoint
       │                                     │
       ├─ tracker.start(6 steps)             │
       ├─ tracker.step("分析需求")            ├─ GET /progress/{id}/stream
       ├─ tracker.step("生成主图")            │    │
       ├─ tracker.step("生成白底图")          │    ├─ tracker.subscribe(task_id)
       │    ...                               │    └─ async for event in queue
       └─ tracker.done(result)                │
                                             ▼
                                       SSE → 浏览器
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ProgressEvent:
    """A single progress event emitted during generation."""
    step: str           # e.g., "分析需求", "生成主图", "质量评估"
    percent: int        # 0-100
    status: str         # "thinking" | "generating" | "evaluating" | "done" | "error"
    message: str        # Human-readable message
    detail: Optional[dict] = None  # Optional extra data


class GenerationProgress:
    """Tracks progress for a single generation task.

    The generation loop calls step() at each milestone.
    SSE subscribers consume events via the async queue.
    """

    def __init__(self, task_id: str, total_steps: int = 6):
        self.task_id = task_id
        self.total_steps = total_steps
        self.current_step = 0
        self.events: asyncio.Queue = asyncio.Queue(maxsize=50)
        self._finished = False
        self._started_at = time.time()
        self._result: Optional[dict] = None
        self._error: Optional[str] = None

    async def step(self, label: str, status: str = "generating", message: str = "", detail: dict = None):
        """Report a progress step. Called by the generation loop."""
        self.current_step += 1
        percent = int(self.current_step / self.total_steps * 100) if self.total_steps > 0 else 0

        event = ProgressEvent(
            step=label,
            percent=min(percent, 99),  # Cap at 99% until done()
            status=status,
            message=message or f"正在{label}...",
            detail=detail,
        )

        await self.events.put(event.to_dict())
        logger.info(f"[{self.task_id}] Progress {percent}%: {label}")

    async def done(self, result: dict = None):
        """Mark generation as complete."""
        self._finished = True
        self._result = result
        event = ProgressEvent(
            step="完成",
            percent=100,
            status="done",
            message="生成完成",
            detail={"elapsed_seconds": int(time.time() - self._started_at)},
        )
        await self.events.put(event.to_dict())

    async def error(self, message: str):
        """Mark generation as failed."""
        self._finished = True
        self._error = message
        event = ProgressEvent(
            step="出错",
            percent=self.current_step / self.total_steps * 100 if self.total_steps > 0 else 0,
            status="error",
            message=message,
        )
        await self.events.put(event.to_dict())

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "finished": self._finished,
            "elapsed_seconds": int(time.time() - self._started_at),
            "error": self._error,
        }


class GenerationTracker:
    """Global registry of in-progress generations.

    Singleton pattern — shared across routes and services.
    """

    _instance: Optional["GenerationTracker"] = None

    def __init__(self):
        self._tasks: dict[str, GenerationProgress] = {}

    @classmethod
    def get(cls) -> "GenerationTracker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create(self, task_id: str, total_steps: int = 6) -> GenerationProgress:
        """Create a new progress tracker for a generation task."""
        progress = GenerationProgress(task_id, total_steps)
        self._tasks[task_id] = progress
        return progress

    def get_task(self, task_id: str) -> Optional[GenerationProgress]:
        """Get an existing progress tracker."""
        return self._tasks.get(task_id)

    def remove(self, task_id: str):
        """Remove a completed tracker."""
        self._tasks.pop(task_id, None)

    async def subscribe(self, task_id: str):
        """Async generator that yields progress events for SSE streaming.

        Usage in FastAPI SSE endpoint:
            tracker = GenerationTracker.get()
            async for event in tracker.subscribe(task_id):
                yield f"event: progress\\ndata: {json.dumps(event)}\\n\\n"
        """
        progress = self.get_task(task_id)

        if progress is None:
            # Task might have already completed. Wait briefly and check.
            await asyncio.sleep(0.5)
            progress = self.get_task(task_id)
            if progress is None:
                yield {"type": "error", "message": "任务不存在或已过期"}
                return

        # Stream events until done
        while True:
            try:
                event = await asyncio.wait_for(progress.events.get(), timeout=30.0)
                yield event
                if event.get("status") in ("done", "error"):
                    break
            except asyncio.TimeoutError:
                # Heartbeat to keep connection alive
                yield {
                    "type": "heartbeat",
                    "step": progress.events._queue[-1]["step"] if progress.events.qsize() > 0 else "处理中",
                    "percent": progress.current_step / progress.total_steps * 100 if progress.total_steps > 0 else 0,
                    "status": "generating",
                    "message": "仍在处理中...",
                }


# Helper for ProgressEvent serialization
def _event_to_dict(self: ProgressEvent) -> dict:
    d = {
        "type": "progress",
        "step": self.step,
        "percent": self.percent,
        "status": self.status,
        "message": self.message,
    }
    if self.detail:
        d["detail"] = self.detail
    return d


ProgressEvent.to_dict = _event_to_dict




# Module-level singleton
tracker = GenerationTracker.get()
