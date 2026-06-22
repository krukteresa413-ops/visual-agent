"""Tests for P3.2: Generation History Browser API.

TDD: RED phase.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


class TestHistoryAPI:
    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from app.api.history_routes import router
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_history_endpoint_returns_paginated(self, client):
        """GET /api/v1/history should return paginated results."""
        with patch("app.api.history_routes.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_record = MagicMock()
            mock_record.id = 1
            mock_record.project_name = "test"
            mock_record.model_used = "deepseek"
            mock_record.generation_seconds = 30
            mock_record.created_at = MagicMock()
            mock_record.created_at.isoformat.return_value = "2026-06-12T16:00:00"
            mock_record.asset_plan_json = '{"main_image": {"url": "/uploads/gen_01.png"}}'

            # Chain: db.query(...).join(...)[.filter(...)].order_by(...).offset(...).limit(...).all()
            # and .count() — without project_id, no .filter() in between
            base = mock_db.query.return_value.join.return_value
            base.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_record]
            base.count.return_value = 1

            response = client.get("/api/v1/history?page=1&page_size=10")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert data["total"] == 1

    def test_history_filter_by_project(self, client):
        """Should filter history by project_id."""
        with patch("app.api.history_routes.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            # Chain with filter: db.query(...).join(...).filter(...).order_by(...).offset(...).limit(...).all()
            # and .filter(...).count()
            base = mock_db.query.return_value.join.return_value
            filtered = base.filter.return_value
            filtered.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            filtered.count.return_value = 0

            response = client.get("/api/v1/history?project_id=2")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
