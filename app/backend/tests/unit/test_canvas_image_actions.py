"""Canvas right-click image action contracts."""
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.project import Project  # noqa: F401 registers table
from app.models.canvas_state import CanvasState


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def seed_canvas(db_session, project_id=9301):
    original_url = "/uploads/generated/original-action.png"
    elements = [{
        "id": "image_9301_main_0",
        "type": "image",
        "label": "商品主图",
        "x": 10,
        "y": 20,
        "width": 280,
        "height": 280,
        "thumbnail_url": original_url,
        "asset_ref": {"type": "main_image", "url": original_url},
        "metadata": {"prompt": "一辆渐变色跑车", "url": original_url, "version": 1},
    }]
    db_session.add(CanvasState(
        project_id=project_id,
        elements_json=json.dumps(elements, ensure_ascii=False),
        connections_json="[]",
        viewport_json='{"x":0,"y":0,"scale":1}',
    ))
    db_session.commit()
    return elements[0]


def make_client(db_session):
    from main import app
    from app.api.atelier_canvas_routes import get_db

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    return app, TestClient(app)


def test_canvas_cutout_creates_new_version_without_text_to_image_generation(db_session):
    original = seed_canvas(db_session)
    app, client = make_client(db_session)
    try:
        with patch("app.api.canvas_image_action_routes.canvas_image_action_service.run", new_callable=AsyncMock) as run_mock, \
             patch("app.services.image_generation_service.image_generation_service.generate", new_callable=AsyncMock) as generate_mock:
            run_mock.return_value = {
                "url": "/uploads/generated/cutout-result.png",
                "width": 280,
                "height": 280,
                "provider": "rembg",
            }
            resp = client.post("/api/v1/canvas/image-action", json={
                "project_id": 9301,
                "asset_id": "image_9301_main_0",
                "action": "cutout",
                "image_url": original["thumbnail_url"],
                "instruction": "",
            })
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "cutout"
    assert data["canvas_element"]["thumbnail_url"] == "/uploads/generated/cutout-result.png"
    assert data["canvas_element"]["metadata"]["parent_asset_id"] == "image_9301_main_0"
    assert data["canvas_element"]["metadata"]["version"] == 2
    assert "抠图" in data["canvas_element"]["metadata"]["instruction"]
    assert data["canvas_element"]["metadata"]["provider"] == "rembg"
    generate_mock.assert_not_called()

    state = db_session.query(CanvasState).filter(CanvasState.project_id == 9301).first()
    saved = json.loads(state.elements_json)
    assert len(saved) == 2
    assert saved[0]["thumbnail_url"] == original["thumbnail_url"]


@pytest.mark.parametrize("action", ["ai_hd", "ai_edit", "layer_split"])
def test_canvas_image_action_rejects_removed_ai_actions(db_session, action):
    original = seed_canvas(db_session, project_id=9302)
    app, client = make_client(db_session)
    try:
        resp = client.post("/api/v1/canvas/image-action", json={
            "project_id": 9302,
            "asset_id": "image_9301_main_0",
            "action": action,
            "image_url": original["thumbnail_url"],
            "instruction": "任意指令",
        })
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
