"""
TDD Step 1 (RED): Atelier Flow Infinite Canvas API tests.
Tests for CanvasState CRUD, Timeline, and Asset Library search.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport


# ── Fixtures ──────────────────────────────────────────────────

def make_mock_canvas_state():
    elements = [
        {"id": "kv01", "type": "key_visual", "label": "KV_01_Main",
         "x": 100, "y": 200, "width": 400, "height": 500,
         "thumbnail_url": "/api/v1/files/kv01.png",
         "asset_ref": {"visual_asset_id": 1},
         "metadata": {"direction": "Organic", "status": "complete"}},
        {"id": "kv02", "type": "key_visual", "label": "KV_02_Alternative",
         "x": 600, "y": 200, "width": 400, "height": 500,
         "thumbnail_url": "/api/v1/files/kv02.png",
         "asset_ref": {"visual_asset_id": 1},
         "metadata": {"direction": "Natural-forward", "status": "in_progress"}},
        {"id": "video01", "type": "video", "label": "Video_01_Mountain",
         "x": 100, "y": 800, "width": 320, "height": 240,
         "thumbnail_url": "/api/v1/files/video01_thumb.png",
         "asset_ref": {"visual_asset_id": 2},
         "metadata": {"duration": 12, "status": "complete"}},
    ]
    connections = [
        {"id": "conn1", "source_id": "kv01", "target_id": "kv02", "label": "variant"},
        {"id": "conn2", "source_id": "kv01", "target_id": "video01", "label": "衍生"},
    ]
    viewport = {"x": 0, "y": 0, "scale": 1}
    mock = MagicMock()
    mock.id = 1; mock.project_id = 1
    mock.elements_json = json.dumps(elements, ensure_ascii=False)
    mock.connections_json = json.dumps(connections, ensure_ascii=False)
    mock.viewport_json = json.dumps(viewport)
    mock.updated_at = None  # prevent MagicMock isoformat() crash
    return mock


def make_mock_visual_asset():
    import datetime
    plan = {
        "main_image": {"prompt": "A nature-forward campaign aesthetic: mountains, wildflowers",
                       "url": "/files/gen1_main.png", "goal": "展示春日户外"},
        "scene_images": [{"scene_name": "山景", "prompt": "Mountain", "url": "/files/scene1.png"}],
        "white_bg": None, "selling_points": [], "video_scripts": [],
        "ad_material": None, "layout_plan": None,
    }
    mock = MagicMock()
    mock.id = 1; mock.project_id = 1
    mock.asset_plan = plan; mock.model_used = "deepseek-v4-pro"
    mock.generation_seconds = 45
    mock.created_at = datetime.datetime(2025, 6, 15, 8, 30, 0)
    return mock


# ── Canvas State Tests ────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_canvas_state_returns_elements_and_connections():
    import main; app = main.app
    mock_state = make_mock_canvas_state()
    with patch("app.api.atelier_canvas_routes.SessionLocal") as ms:
        mdb = MagicMock()
        mdb.query.return_value.filter.return_value.first.return_value = mock_state
        ms.return_value = mdb
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/projects/1/canvas-state")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["elements"]) == 3
    assert data["elements"][0]["id"] == "kv01"
    assert len(data["connections"]) == 2
    assert data["viewport"]["scale"] == 1


@pytest.mark.asyncio
async def test_get_canvas_state_empty_for_new_project():
    import main; app = main.app
    with patch("app.api.atelier_canvas_routes.SessionLocal") as ms:
        mdb = MagicMock()
        mdb.query.return_value.filter.return_value.first.return_value = None
        ms.return_value = mdb
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/projects/1/canvas-state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["elements"] == []
    assert data["connections"] == []


@pytest.mark.asyncio
async def test_put_canvas_state_saves_and_returns():
    import main; app = main.app
    payload = {
        "elements": [{"id": "new_kv", "type": "key_visual", "label": "New KV",
                      "x": 50, "y": 50, "width": 300, "height": 400}],
        "connections": [], "viewport": {"x": 10, "y": 20, "scale": 0.8},
    }
    with patch("app.api.atelier_canvas_routes.SessionLocal") as ms:
        mdb = MagicMock()
        mdb.query.return_value.filter.return_value.first.return_value = None
        ms.return_value = mdb
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.put("/api/v1/projects/1/canvas-state", json=payload)
    assert resp.status_code == 200
    assert resp.json()["elements"] == payload["elements"]
    mdb.add.assert_called_once()
    mdb.commit.assert_called_once()



@pytest.mark.asyncio
async def test_put_canvas_state_preserves_connection_relation_type():
    import json
    import main; app = main.app
    payload = {
        "elements": [{"id": "source", "type": "key_visual", "x": 0, "y": 0}],
        "connections": [{
            "id": "edge-variant",
            "source_id": "source",
            "target_id": "variant",
            "label": "variant_of",
            "relation_type": "variant_of",
        }],
        "viewport": {"x": 0, "y": 0, "scale": 1},
    }
    with patch("app.api.atelier_canvas_routes.SessionLocal") as ms:
        mdb = MagicMock()
        mdb.query.return_value.filter.return_value.first.return_value = None
        ms.return_value = mdb
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.put("/api/v1/projects/1/canvas-state", json=payload)

    assert resp.status_code == 200
    assert resp.json()["connections"][0]["relation_type"] == "variant_of"
    saved = json.loads(mdb.add.call_args.args[0].connections_json)
    assert saved[0]["relation_type"] == "variant_of"


@pytest.mark.asyncio
async def test_put_canvas_state_preserves_connection_metadata():
    import json
    import main; app = main.app
    payload = {
        "elements": [{"id": "source", "type": "key_visual", "x": 0, "y": 0}],
        "connections": [{
            "id": "edge-instruction",
            "source_id": "source",
            "target_id": "variant",
            "label": "换蓝色背景",
            "relation_type": "variant_of",
            "metadata": {"instruction": "换蓝色背景"},
        }],
        "viewport": {"x": 0, "y": 0, "scale": 1},
    }
    with patch("app.api.atelier_canvas_routes.SessionLocal") as ms:
        mdb = MagicMock()
        mdb.query.return_value.filter.return_value.first.return_value = None
        ms.return_value = mdb
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.put("/api/v1/projects/1/canvas-state", json=payload)

    assert resp.status_code == 200
    assert resp.json()["connections"][0]["relation_type"] == "variant_of"
    assert resp.json()["connections"][0]["metadata"]["instruction"] == "换蓝色背景"
    saved = json.loads(mdb.add.call_args.args[0].connections_json)
    assert saved[0]["relation_type"] == "variant_of"
    assert saved[0]["metadata"]["instruction"] == "换蓝色背景"


@pytest.mark.asyncio
async def test_put_canvas_state_updates_existing():
    import main; app = main.app
    existing = make_mock_canvas_state()
    payload = {
        "elements": [{"id": "updated", "type": "text", "x": 0, "y": 0}],
        "connections": [], "viewport": {"x": 0, "y": 0, "scale": 1},
    }
    with patch("app.api.atelier_canvas_routes.SessionLocal") as ms:
        mdb = MagicMock()
        mdb.query.return_value.filter.return_value.first.return_value = existing
        ms.return_value = mdb
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.put("/api/v1/projects/1/canvas-state", json=payload)
    assert resp.status_code == 200
    mdb.add.assert_not_called()
    mdb.commit.assert_called_once()


# ── Timeline Tests ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_timeline_returns_generation_history():
    import main; app = main.app
    mock_asset = make_mock_visual_asset()
    with patch("app.api.atelier_canvas_routes.SessionLocal") as ms:
        mdb = MagicMock()
        mdb.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_asset]
        ms.return_value = mdb
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/projects/1/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["entries"]) > 0
    entry = data["entries"][0]
    assert "prompt" in entry
    assert "timestamp" in entry


@pytest.mark.asyncio
async def test_get_timeline_empty_project():
    import main; app = main.app
    with patch("app.api.atelier_canvas_routes.SessionLocal") as ms:
        mdb = MagicMock()
        mdb.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        ms.return_value = mdb
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/projects/1/timeline")
    assert resp.status_code == 200
    assert resp.json()["entries"] == []


# ── Asset Library Search Tests ────────────────────────────────

@pytest.mark.asyncio
async def test_canvas_assets_returns_filtered_by_type():
    import main; app = main.app
    mock_asset = make_mock_visual_asset()
    with patch("app.api.atelier_canvas_routes.SessionLocal") as ms:
        mdb = MagicMock()
        mdb.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_asset]
        ms.return_value = mdb
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/projects/1/canvas-assets?type=images")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_canvas_assets_search_by_keyword():
    import main; app = main.app
    mock_asset = make_mock_visual_asset()
    with patch("app.api.atelier_canvas_routes.SessionLocal") as ms:
        mdb = MagicMock()
        mdb.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_asset]
        ms.return_value = mdb
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/projects/1/canvas-assets?search=mountain")
    assert resp.status_code == 200
    assert resp.json()["total"] > 0
