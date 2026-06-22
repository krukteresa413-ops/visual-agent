"""ChatCanvas selected-asset image modification contract."""
import json
import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.project import Project  # noqa: F401 registers projects table
from app.models.canvas_state import CanvasState
from app.models.image_generation_model import GeneratedImage, ImageGenerationResult


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


def test_modify_selected_canvas_image_creates_version_and_preserves_other_elements(db_session):
    from main import app
    from app.api.atelier_canvas_routes import get_db

    project_id = 9202
    original_url = "/uploads/generated/original.png"
    other_url = "/uploads/generated/other.png"
    modified_url = "/uploads/generated/modified.png"
    elements = [
        {
            "id": "image_9202_main_0",
            "type": "image",
            "label": "商品主图",
            "x": 0,
            "y": 0,
            "width": 280,
            "height": 280,
            "thumbnail_url": original_url,
            "asset_ref": {"type": "main_image", "url": original_url},
            "metadata": {"prompt": "白底运动鞋", "url": original_url, "version": 1},
        },
        {
            "id": "image_9202_scene_1",
            "type": "image",
            "label": "场景图",
            "x": 320,
            "y": 0,
            "width": 280,
            "height": 280,
            "thumbnail_url": other_url,
            "asset_ref": {"type": "scene_image", "url": other_url},
            "metadata": {"prompt": "其它图", "url": other_url, "version": 1},
        },
    ]
    db_session.add(CanvasState(
        project_id=project_id,
        elements_json=json.dumps(elements, ensure_ascii=False),
        connections_json="[]",
        viewport_json='{"x":0,"y":0,"scale":1}',
    ))
    db_session.commit()

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    try:
        with patch("app.api.asset_routes.image_generation_service.generate", new_callable=AsyncMock) as generate_mock:
            generate_mock.return_value = ImageGenerationResult(
                provider="local",
                status="succeeded",
                images=[GeneratedImage(url=modified_url, width=1024, height=1024)],
            )
            client = TestClient(app)
            resp = client.post("/api/v1/asset/modify", json={
                "asset_type": "image",
                "asset_id": "image_9202_main_0",
                "project_id": project_id,
                "original": elements[0]["metadata"],
                "instruction": "背景换成城市通勤场景，商品主体保持不变",
                "brief": {"project_id": project_id, "product_name": "运动鞋"},
            })
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["modified"]["url"] == modified_url
    assert data["modified"]["parent_asset_id"] == "image_9202_main_0"
    assert data["modified"]["version"] == 2
    assert data["canvas_element"]["id"] != "image_9202_main_0"
    assert data["canvas_element"]["thumbnail_url"] == modified_url

    state = db_session.query(CanvasState).filter(CanvasState.project_id == project_id).first()
    saved = json.loads(state.elements_json)
    assert len(saved) == 3
    assert saved[0]["thumbnail_url"] == original_url
    assert saved[1]["thumbnail_url"] == other_url
    new_el = saved[2]
    assert new_el["asset_ref"]["parent_asset_id"] == "image_9202_main_0"
    assert new_el["metadata"]["version"] == 2
    assert new_el["metadata"]["instruction"] == "背景换成城市通勤场景，商品主体保持不变"
