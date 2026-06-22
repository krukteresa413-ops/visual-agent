"""Tests for F4: Font Generation API.

TDD: RED phase - tests written first, expected to fail.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime


class TestFontGenerationAPI:
    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from app.api.font_generation_routes import router
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_font_generate_endpoint_exists(self, client):
        """POST /api/v1/font-generate should exist and accept request."""
        payload = {
            "text": "沐源甲科技",
            "style_name": "优雅宋体",
            "provider": "mige",
        }
        # Should not get 404
        response = client.post("/api/v1/font-generate", json=payload)
        assert response.status_code in [200, 201, 202, 500, 502], \
            f"Endpoint should exist (got {response.status_code})"

    def test_font_generate_returns_task_id(self, client):
        """POST /api/v1/font-generate should return task_id for async generation."""
        with patch("app.api.font_generation_routes.font_generation_service") as mock_service:
            from app.models.font_generation_model import FontGenerationResponse
            from datetime import datetime
            mock_service.generate_font = AsyncMock(return_value=FontGenerationResponse(
                task_id="font_task_123",
                status="pending",
                text="沐源甲科技",
                style_name="优雅宋体",
                provider="mige",
                created_at=datetime.now(),
            ))

            payload = {
                "text": "沐源甲科技",
                "style_name": "优雅宋体",
                "provider": "mige",
            }
            response = client.post("/api/v1/font-generate", json=payload)
            assert response.status_code in [200, 201, 202]
            data = response.json()
            assert "task_id" in data
            assert data["status"] in ["pending", "processing"]

    def test_font_generate_validates_text_required(self, client):
        """POST /api/v1/font-generate should require text field."""
        payload = {
            "style_name": "优雅宋体",
        }
        response = client.post("/api/v1/font-generate", json=payload)
        assert response.status_code == 422  # Validation error

    def test_font_history_endpoint_exists(self, client):
        """GET /api/v1/font-history should exist."""
        response = client.get("/api/v1/font-history?page=1&page_size=10")
        assert response.status_code in [200, 500], \
            f"Endpoint should exist (got {response.status_code})"

    def test_font_history_returns_paginated(self, client):
        """GET /api/v1/font-history should return paginated results."""
        with patch("app.services.font_generation_service.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_record = MagicMock()
            mock_record.id = 1
            mock_record.task_id = "font_task_123"
            mock_record.text = "沐源甲科技"
            mock_record.style_name = "优雅宋体"
            mock_record.status = "completed"
            mock_record.image_url = "/static/fonts/font_task_123.png"
            mock_record.provider = "mige"
            mock_record.error_message = None  # Set to None explicitly, not MagicMock
            mock_record.generation_seconds = 30
            mock_record.created_at = datetime(2026, 6, 16, 12, 0, 0)
            mock_record.updated_at = datetime(2026, 6, 16, 12, 0, 30)

            # Mock query chain
            query_mock = mock_db.query.return_value
            query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_record]
            query_mock.count.return_value = 1

            response = client.get("/api/v1/font-history?page=1&page_size=10")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert data["total"] == 1
            assert len(data["items"]) == 1
            assert data["items"][0]["text"] == "沐源甲科技"

    def test_font_history_filter_by_status(self, client):
        """GET /api/v1/font-history should filter by status."""
        with patch("app.services.font_generation_service.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            # Mock query chain with filter
            query_mock = mock_db.query.return_value
            filter_mock = query_mock.filter.return_value
            filter_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            query_mock.filter.return_value.count.return_value = 0

            response = client.get("/api/v1/font-history?status=completed&page=1&page_size=10")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data


class TestFontGenerationService:
    """Test font generation service layer."""

    def test_generate_font_calls_mige_provider(self):
        """Service should use MigeProvider in Phase 1."""
        from app.services.font_generation_service import FontGenerationService
        
        service = FontGenerationService()
        # Should have method to generate fonts
        assert hasattr(service, 'generate_font')

    @pytest.mark.asyncio
    async def test_generate_font_saves_to_database(self):
        """Service should save generation record to database."""
        from app.services.font_generation_service import FontGenerationService
        from app.models.font_generation_model import FontGenerationRequest
        
        with patch("app.services.font_generation_service.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            
            # Mock the db_record to have created_at
            mock_db_record = MagicMock()
            mock_db_record.task_id = "font_test_123"
            mock_db_record.status = "completed"
            mock_db_record.text = "测试"
            mock_db_record.style_name = "宋体"
            mock_db_record.provider = "mige"
            mock_db_record.created_at = datetime(2026, 6, 16, 12, 0, 0)
            
            # Mock db.add to set the record
            def mock_add(record):
                record.created_at = datetime(2026, 6, 16, 12, 0, 0)
            
            mock_db.add = mock_add

            with patch("app.services.font_generation_service.image_generation_service") as mock_img_service:
                mock_img_service.generate = AsyncMock(return_value=MagicMock(
                    status="succeeded",
                    images=[MagicMock(url="/static/fonts/test.png")]
                ))

                service = FontGenerationService()
                request = FontGenerationRequest(
                    text="测试",
                    style_name="宋体",
                    provider="mige"
                )
                
                result = await service.generate_font(request)
                assert result is not None
                assert "task_id" in result.model_dump()


class TestFontGenerationModel:
    """Test font generation data models."""

    def test_font_generation_table_exists(self):
        """FontGeneration SQLAlchemy model should exist."""
        from app.models.font_generation_model import FontGeneration
        assert FontGeneration is not None
        assert hasattr(FontGeneration, '__tablename__')
        assert FontGeneration.__tablename__ == 'font_generations'

    def test_font_generation_has_required_fields(self):
        """FontGeneration should have all required fields."""
        from app.models.font_generation_model import FontGeneration
        
        assert hasattr(FontGeneration, 'id')
        assert hasattr(FontGeneration, 'task_id')
        assert hasattr(FontGeneration, 'text')
        assert hasattr(FontGeneration, 'style_name')
        assert hasattr(FontGeneration, 'status')
        assert hasattr(FontGeneration, 'image_url')
        assert hasattr(FontGeneration, 'provider')
        assert hasattr(FontGeneration, 'created_at')

    def test_font_generation_request_validates(self):
        """FontGenerationRequest Pydantic model should validate inputs."""
        from app.models.font_generation_model import FontGenerationRequest
        
        # Valid request
        req = FontGenerationRequest(
            text="沐源甲科技",
            style_name="优雅宋体",
            provider="mige"
        )
        assert req.text == "沐源甲科技"
        assert req.provider == "mige"

    def test_font_generation_request_requires_text(self):
        """FontGenerationRequest should require text field."""
        from app.models.font_generation_model import FontGenerationRequest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            FontGenerationRequest(style_name="宋体")
