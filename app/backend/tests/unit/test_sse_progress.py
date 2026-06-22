"""
Tests for SSE progress streaming with GenerationTracker (updated).
"""
import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock


class TestSSEProgress:
    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from app.api.progress_routes import router
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_sse_endpoint_rejects_unknown_task(self, client):
        """GET /api/v1/progress/{task_id}/stream should 404 for unknown tasks."""
        response = client.get("/api/v1/progress/nonexistent123/stream")
        assert response.status_code == 404
        assert "不存在" in response.text or "not found" in response.text.lower()

    def test_sse_endpoint_streams_with_tracker(self, client):
        """SSE should stream events from a real GenerationProgress."""
        from app.services.generation_tracker import GenerationTracker

        gt = GenerationTracker.get()
        task_id = "test_stream_001"
        progress = gt.create(task_id, total_steps=3)

        # Pre-populate some progress
        async def add_events():
            await progress.step("分析需求", "thinking", "分析中...")
            await progress.step("生成主图", "generating", "生成中...")
            await progress.done({"result": "ok"})

        # Run add_events in background so SSE can consume them
        import asyncio as _asyncio
        loop = _asyncio.new_event_loop()
        loop.run_until_complete(add_events())
        loop.close()

        response = client.get(f"/api/v1/progress/{task_id}/stream")
        # Since events were already added before connecting,
        # SSE will receive them immediately
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type

    def test_progress_status_endpoint(self, client):
        """GET /api/v1/progress/{task_id}/status should return progress info."""
        from app.services.generation_tracker import GenerationTracker

        gt = GenerationTracker.get()
        task_id = "test_status_001"
        gt.create(task_id, total_steps=5)

        response = client.get(f"/api/v1/progress/{task_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["total_steps"] == 5
        assert data["finished"] is False

    def test_progress_status_404(self, client):
        """GET /api/v1/progress/{task_id}/status should 404 for unknown tasks."""
        response = client.get("/api/v1/progress/nonexistent456/status")
        assert response.status_code == 404


class TestGenerationTracker:
    """Unit tests for the tracker itself (no HTTP)."""

    def test_create_and_step(self):
        from app.services.generation_tracker import GenerationTracker
        gt = GenerationTracker.get()
        task_id = "unit_test_001"

        progress = gt.create(task_id, total_steps=4)
        assert progress.task_id == task_id
        assert progress.total_steps == 4
        assert progress.current_step == 0

        assert gt.get_task(task_id) is not None
        gt.remove(task_id)
        assert gt.get_task(task_id) is None

    def test_step_and_done(self):
        from app.services.generation_tracker import GenerationTracker
        import asyncio

        gt = GenerationTracker.get()
        task_id = "unit_test_002"
        progress = gt.create(task_id, total_steps=2)

        async def run():
            await progress.step("分析需求", "thinking", "分析中")
            await progress.step("生成", "generating", "生成中")
            await progress.done({"ok": True})

        loop = asyncio.new_event_loop()
        loop.run_until_complete(run())

        # Drain events
        events = []
        while not progress.events.empty():
            events.append(loop.run_until_complete(progress.events.get()))

        loop.close()

        assert len(events) >= 3  # 2 steps + 1 done
        assert events[-1]["status"] == "done"
        assert events[-1]["percent"] == 100

        gt.remove(task_id)
