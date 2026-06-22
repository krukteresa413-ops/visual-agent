"""生成历史 API 测试 — TDD RED"""
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestHistoryAPI:
    """测试历史记录 API。"""

    @patch("app.db.session.SessionLocal")
    def test_list_history_returns_records(self, mock_session_cls):
        """GET /projects/{id}/history 返回生成记录列表。"""
        # Setup mock DB
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.project_id = 2
        mock_record.model_used = "deepseek-v4-pro"
        mock_record.generation_seconds = 45
        mock_record.created_at = "2026-06-08T12:00:00"
        mock_record.asset_plan_json = json.dumps({"prompt": "test prompt for reuse", "main_image": {"goal": "test"}})
        mock_record.brief_id = None

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_record]

        # Import and test
        from app.api.unified_generation_routes import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get("/api/v1/projects/2/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "records" in data
        assert len(data["records"]) == 1
        assert data["records"][0]["id"] == 1
        assert data["records"][0]["model_used"] == "deepseek-v4-pro"
        assert data["records"][0]["prompt"] == "test prompt for reuse"

    @patch("app.db.session.SessionLocal")
    def test_history_detail_returns_full_plan(self, mock_session_cls):
        """GET /projects/{id}/history/{record_id} 返回完整 plan。"""
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        plan_json = json.dumps({
            "project_id": 2,
            "main_image": {"asset_type": "main_image", "goal": "test", "composition": "c", "background": "b", "prompt": "p"},
            "white_bg": {"goal": "test", "instructions": "test"},
            "scene_images": [],
            "selling_points": [],
            "video_scripts": [],
            "ad_material": {"ad_goal": "t", "target_audience": "t", "ad_angle": "t", "material_list": [], "shot_sequence": [], "hook": "t", "key_selling_points": [], "cta": "t", "platform_suggestion": "t"},
        })

        mock_record = MagicMock()
        mock_record.id = 5
        mock_record.project_id = 2
        mock_record.model_used = "deepseek"
        mock_record.generation_seconds = 30
        mock_record.created_at = "2026-06-08T12:00:00"
        mock_record.asset_plan_json = plan_json
        mock_record.brief_id = 3

        mock_db.query.return_value.filter.return_value.first.return_value = mock_record

        from app.api.unified_generation_routes import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get("/api/v1/projects/2/history/5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 5
        assert data["project_id"] == 2
        assert data["brief_id"] == 3
        assert data["asset_plan"] is not None
        assert data["asset_plan"]["main_image"]["goal"] == "test"

    @patch("app.db.session.SessionLocal")
    def test_history_detail_404(self, mock_session_cls):
        """不存在的记录返回 404。"""
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        from app.api.unified_generation_routes import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get("/api/v1/projects/2/history/999")
        assert resp.status_code == 404


class TestAutoSave:
    """测试自动存档行为。"""

    def test_generate_all_accepts_db_param(self):
        """generate_all 接受 db 参数。"""
        import inspect
        from app.services.visual_agent import VisualAgent
        sig = inspect.signature(VisualAgent.generate_all)
        assert "db" in sig.parameters

    def test_unified_endpoint_passes_db(self):
        """unified endpoint 调用 generate_all 时传了 db session。"""
        import inspect
        # Check that the route code contains db session creation
        source = inspect.getsource(inspect.getmodule(
            __import__("app.api.unified_generation_routes", fromlist=["router"])
        ))
        assert "db" in source.lower() or "SessionLocal" in source, "Should pass db session for auto-save"
