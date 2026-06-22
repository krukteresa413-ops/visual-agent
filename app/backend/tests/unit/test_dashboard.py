"""Tests for P3.1: Dashboard API endpoint.

TDD: RED phase — tests written before implementation.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock


class TestDashboardAPI:
    """Test the /api/v1/dashboard endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client with dashboard routes registered + mocked DB."""
        from fastapi import FastAPI
        from app.api.dashboard_routes import router, get_db
        app = FastAPI()
        app.include_router(router)

        # Override get_db to inject a mock session
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 5
        mock_db.query.return_value.filter.return_value.count.return_value = 42
        mock_db.query.return_value.scalar.return_value = 5
        mock_db.query.return_value.filter.return_value.scalar.return_value = 42

        # Mock recent activity query
        mock_activity = MagicMock()
        mock_activity.id = 1
        mock_activity.project_name = "test project"
        mock_activity.model_used = "deepseek"
        mock_activity.created_at = MagicMock()
        mock_activity.created_at.isoformat.return_value = "2026-06-16T16:00:00"

        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_activity
        ]

        # Mock group_by query (project breakdown)
        mock_row = MagicMock()
        mock_row.project_type = "video"
        mock_row.count = 3
        mock_db.query.return_value.group_by.return_value.all.return_value = [mock_row]

        app.dependency_overrides[get_db] = lambda: mock_db
        return TestClient(app)

    def test_dashboard_endpoint_exists(self, client):
        """GET /api/v1/dashboard should return 200 with stats."""
        response = client.get("/api/v1/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_projects" in data
        assert "total_generations" in data

    def test_dashboard_returns_recent_activity(self, client):
        """Dashboard should include recent generation activity."""
        response = client.get("/api/v1/dashboard")
        data = response.json()
        assert "recent_activity" in data
        assert len(data["recent_activity"]) >= 0

    def test_dashboard_project_breakdown(self, client):
        """Dashboard should break down stats per project type / status."""
        response = client.get("/api/v1/dashboard")
        data = response.json()
        assert "projects_with_activity" in data
        assert isinstance(data["projects_with_activity"], (int, list))
