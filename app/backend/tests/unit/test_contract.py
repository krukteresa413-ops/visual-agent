"""V2 recommended tests: async task contract + SSE fallback (Phase 5).

Tests the unified generation contract:
  1. POST generate-async → returns {task_id, status: processing}
  2. Poll /unified/generation/task/{task_id} → status progresses to complete
  3. SSE falls back to polling gracefully
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# ── Async Task Contract Tests ───────────────────────────────────────

class TestAsyncTaskContract:
    """Verify the submit→task_id→poll→result contract."""

    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from app.api.unified_generation_routes import router
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_generate_async_returns_task_id(self, client):
        """POST /unified/generate-async should return task_id immediately."""
        with patch(
            "app.api.unified_generation_routes._parse_brief_from_request",
            new_callable=AsyncMock,
        ) as mock_parse:
            mock_parse.return_value = {"product_name": "test", "category": "test"}
            with patch(
                "app.api.unified_generation_routes.BriefReviewer.generate_questions",
                return_value=[],
            ):
                response = client.post(
                    "/api/v1/generate-async",
                    data={"text": "test product", "project_id": 2, "skip_review": True},
                )
                assert response.status_code == 200
                data = response.json()
                assert "task_id" in data
                assert data["status"] == "processing"
                assert len(data["task_id"]) > 0

    def test_poll_returns_processing_then_complete(self, client):
        """Polling /unified/generation/task/{task_id} should reflect status progression."""
        from app.api.unified_generation_routes import _async_gen_tasks

        task_id = "test-task-contract-001"
        _async_gen_tasks[task_id] = {"status": "processing"}

        # Poll while processing
        response = client.get(f"/api/v1/generation/task/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "processing"

        # Mark complete
        _async_gen_tasks[task_id] = {
            "status": "complete",
            "parsed_brief": {"product_name": "test"},
            "generation": {"main_image": {"url": "/test.png"}},
            "elapsed_seconds": 30,
        }

        response = client.get(f"/api/v1/generation/task/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert data["generation"] is not None

    def test_poll_returns_error_status(self, client):
        """Failed tasks should return status=error with error message."""
        from app.api.unified_generation_routes import _async_gen_tasks

        task_id = "test-task-error-001"
        _async_gen_tasks[task_id] = {"status": "error", "error": "Generation timeout"}

        response = client.get(f"/api/v1/generation/task/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "error" in data

    def test_poll_unknown_task_returns_404(self, client):
        """Polling non-existent task should return 404."""
        response = client.get("/api/v1/generation/task/nonexistent-task-id")
        assert response.status_code == 404

    def test_async_task_store_persistence(self, client):
        """Tasks stored in _async_gen_tasks should persist across polls."""
        from app.api.unified_generation_routes import _async_gen_tasks

        task_id = "test-persist-001"
        _async_gen_tasks[task_id] = {"status": "processing", "progress": 50}

        # Multiple polls should return same task
        for _ in range(3):
            response = client.get(f"/api/v1/generation/task/{task_id}")
            assert response.status_code == 200
            assert response.json()["progress"] == 50


# ── SSE Fallback Tests ──────────────────────────────────────────────

class TestSSEFallback:
    """Verify SSE falls back to polling when SSE connection fails."""

    def test_polling_endpoint_serves_as_sse_fallback(self):
        """The polling endpoint should always be available as SSE fallback."""
        from app.api.unified_generation_routes import _async_gen_tasks

        task_id = "test-fallback-001"
        _async_gen_tasks[task_id] = {"status": "processing"}

        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from app.api.unified_generation_routes import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Poll should work even without SSE
        resp = client.get(f"/api/v1/generation/task/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "processing"

    def test_progress_sse_endpoint_accessible(self):
        """SSE endpoint should return event-stream content type."""
        from app.api.unified_generation_routes import _async_gen_tasks
        from app.models.visual_asset import VisualAsset

        task_id = "test-sse-001"
        _async_gen_tasks[task_id] = {"status": "processing"}

        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from app.api.progress_routes import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Mock GenerationTracker (new implementation, replaces SessionLocal)
        with patch("app.api.progress_routes.GenerationTracker") as mock_tracker_cls:
            mock_tracker = MagicMock()
            mock_tracker_cls.get.return_value = mock_tracker

            # get_task returns a valid task
            mock_tracker.get_task.return_value = {"task_id": "test-65", "status": "processing"}

            # subscribe yields a done event
            async def mock_subscribe(task_id):
                yield {"type": "progress", "status": "done", "step": "完成", "percent": 100}

            mock_tracker.subscribe.return_value = mock_subscribe("test-65")

            response = client.get("/api/v1/progress/65/stream")
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")


# ── Contract Compliance ─────────────────────────────────────────────

class TestContractCompliance:
    """Ensure all generation paths follow the unified contract."""

    def test_generate_all_fast_still_works(self):
        """Sync generate-all-fast should still work for lightweight use."""
        with patch(
            "app.api.visual_tasks.agent.generate_all",
            new_callable=AsyncMock,
        ) as mock_gen:
            mock_gen.return_value = MagicMock()
            mock_gen.return_value.model_dump.return_value = {"status": "ok"}

            from fastapi.testclient import TestClient
            from fastapi import FastAPI
            from app.api.visual_tasks import router

            app = FastAPI()
            app.include_router(router)
            tc = TestClient(app)

            response = tc.post("/api/v1/visual-tasks/generate-all-fast", json={
                "project_id": 2,
                "brief": {"product_name": "test", "category": "test"},
                "task_types": ["main_image"],
            })
            assert response.status_code == 200

    def test_async_and_sync_coexist(self):
        """Async and sync endpoints should coexist without interference."""
        from app.api.unified_generation_routes import _async_gen_tasks

        # Add a task to async store
        _async_gen_tasks["coexist-test"] = {"status": "processing"}

        # Verify async store works
        assert "coexist-test" in _async_gen_tasks

        # Verify polling works
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from app.api.unified_generation_routes import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get("/api/v1/generation/task/coexist-test")
        assert resp.status_code == 200

        # Cleanup
        del _async_gen_tasks["coexist-test"]
