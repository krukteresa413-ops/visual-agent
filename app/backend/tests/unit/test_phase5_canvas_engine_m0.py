"""Phase 5 M0 canvas engine model contract tests."""
import json
import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport


def make_state():
    state = MagicMock()
    state.id = 1
    state.project_id = 501
    state.elements_json = "[]"
    state.connections_json = "[]"
    state.viewport_json = '{"x":0,"y":0,"scale":1}'
    state.updated_at = None
    return state


@pytest.mark.asyncio
async def test_canvas_element_schema_has_phase5_engine_fields():
    from app.api.atelier_canvas_routes import CanvasElement

    fields = CanvasElement.model_fields
    assert "rotation" in fields
    assert "zIndex" in fields
    assert "hidden" in fields
    assert "locked" in fields
    assert "editableLayers" in fields


@pytest.mark.asyncio
async def test_canvas_state_preserves_phase5_engine_fields():
    import main
    app = main.app
    existing = make_state()
    payload = {
        "elements": [
            {
                "id": "el-phase5",
                "type": "image",
                "label": "Phase 5 element",
                "x": 10,
                "y": 20,
                "width": 320,
                "height": 180,
                "rotation": 15,
                "zIndex": 7,
                "hidden": False,
                "locked": True,
                "editableLayers": [
                    {"id": "title", "type": "text", "text": "MOYAG", "editable": True}
                ],
            }
        ],
        "connections": [],
        "viewport": {"x": 1, "y": 2, "scale": 1.25},
    }

    with patch("app.api.atelier_canvas_routes.SessionLocal") as session_local:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing
        session_local.return_value = db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put("/api/v1/projects/501/canvas-state", json=payload)

    assert response.status_code == 200
    saved = response.json()["elements"][0]
    assert saved["rotation"] == 15
    assert saved["zIndex"] == 7
    assert saved["hidden"] is False
    assert saved["locked"] is True
    assert saved["editableLayers"][0]["text"] == "MOYAG"

    persisted = json.loads(existing.elements_json)[0]
    assert persisted["rotation"] == 15
    assert persisted["zIndex"] == 7
    assert persisted["hidden"] is False
    assert persisted["locked"] is True
    assert persisted["editableLayers"][0]["id"] == "title"


def test_canvas_state_model_documents_phase5_engine_fields():
    from app.models.canvas_state import CanvasState

    comment = CanvasState.elements_json.comment or ""
    assert "rotation" in comment
    assert "zIndex" in comment
    assert "hidden" in comment
    assert "locked" in comment
    assert "editableLayers" in comment
