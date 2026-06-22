"""
Tests for async full-generation endpoint.
Pattern: submit → get task_id → poll until complete.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


class TestAsyncGeneration:
    """RED tests — async generate + poll endpoints."""

    def test_submit_async_returns_task_id_immediately(self, client):
        """POST /generate-async should return task_id within 1 second."""
        mock_plan = AsyncMock()
        mock_plan.main_image = None
        mock_plan.white_bg = None
        mock_plan.scene_images = []
        mock_plan.selling_points = []
        mock_plan.video_scripts = []
        mock_plan.ad_material = None

        with patch("app.services.visual_agent.VisualAgent.generate_all",
                   new_callable=AsyncMock, return_value=mock_plan):
            resp = client.post("/api/v1/generate-async", data={
                "text": "小米智能手表S3，心率血氧GPS",
                "skip_review": "true",
                "project_id": "2",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["status"] == "processing"

    def test_poll_processing_returns_status(self, client):
        """Polling an in-progress task should return status=processing."""
        mock_plan = AsyncMock()
        mock_plan.main_image = None
        mock_plan.white_bg = None
        mock_plan.scene_images = []
        mock_plan.selling_points = []
        mock_plan.video_scripts = []
        mock_plan.ad_material = None

        with patch("app.services.visual_agent.VisualAgent.generate_all",
                   new_callable=AsyncMock, return_value=mock_plan):
            resp = client.post("/api/v1/generate-async", data={
                "text": "测试产品",
                "skip_review": "true",
                "project_id": "2",
            })
            task_id = resp.json()["task_id"]

        resp2 = client.get(f"/api/v1/generation/task/{task_id}")
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["status"] in ("processing", "complete")

    def test_poll_unknown_task_returns_404(self, client):
        """Polling a non-existent task should return 404."""
        resp = client.get("/api/v1/generation/task/nonexistent-id")
        assert resp.status_code == 404

    def test_submit_async_handles_review_needed(self, client):
        """When brief is incomplete, async endpoint should return needs_review immediately."""
        resp = client.post("/api/v1/generate-async", data={
            "text": "产品",  # too short → needs review
            "project_id": "2",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("needs_review") is True
        assert "questions" in data
        assert "task_id" not in data  # no async task needed for review
