import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_canvas_action_starts_existing_progress_task_and_returns_task_id(monkeypatch):
    import main
    import app.api.canvas_action_routes as canvas_action_routes
    from app.services.generation_tracker import GenerationTracker

    monkeypatch.setattr(canvas_action_routes, "generate_canvas_variant_asset", AsyncMock(return_value=("/uploads/generated/test.png", "asset-real-1")))

    payload = {
        "project_id": 19,
        "instruction": "make it warmer",
        "selection": [
            {"nodeId": "s5-main", "assetId": "asset-s5-main", "label": "S5 Main", "type": "key_visual"}
        ],
    }

    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/canvas-actions", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processing"
    assert body["task_id"]
    assert GenerationTracker.get().get_task(body["task_id"]) is not None


@pytest.mark.asyncio
async def test_canvas_action_task_poll_returns_variant_node_and_relation_edge(monkeypatch):
    import asyncio
    import main
    import app.api.canvas_action_routes as canvas_action_routes

    monkeypatch.setattr(canvas_action_routes, "generate_canvas_variant_asset", AsyncMock(return_value=("/uploads/generated/test.png", "asset-real-2")))

    payload = {
        "project_id": 19,
        "instruction": "make it warmer",
        "selection": [
            {"nodeId": "s5-main", "assetId": "asset-s5-main", "label": "S5 Main", "type": "key_visual"}
        ],
    }

    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        started = await client.post("/api/v1/canvas-actions", json=payload)
        task_id = started.json()["task_id"]
        for _ in range(20):
            polled = await client.get(f"/api/v1/canvas-actions/{task_id}")
            body = polled.json()
            if body.get("status") == "complete":
                break
            await asyncio.sleep(0.05)

    assert body["status"] == "complete"
    result = body["result"]
    assert result["node"]["id"].startswith("variant-s5-main-")
    assert result["node"]["metadata"]["provenance"]["parentNodeId"] == "s5-main"
    assert result["node"]["metadata"]["provenance"]["assetId"]
    assert result["edge"]["source_id"] == "s5-main"
    assert result["edge"]["target_id"] == result["node"]["id"]
    assert result["edge"]["relation_type"] == "variant_of"
    assert result["edge"]["metadata"]["relation_type"] == "variant_of"



def test_canvas_action_result_uses_generated_asset_url_and_instruction_labeled_edge():
    from app.api.canvas_action_routes import CanvasActionRequest, CanvasSelectionItem, build_canvas_action_result

    req = CanvasActionRequest(
        project_id=19,
        instruction="调成白色",
        selection=[],
    )
    source = CanvasSelectionItem(
        nodeId="s5-main",
        assetId="asset-s5-main",
        label="S5 Main",
        type="key_visual",
        imageUrl="http://example.test/source.png",
    )

    result = build_canvas_action_result(
        req,
        source,
        task_id="task-real",
        generated_image_url="/uploads/generated/edited.png",
        generated_asset_id="123",
    )

    assert result["node"]["thumbnail_url"] == "/uploads/generated/edited.png"
    assert result["node"]["asset_ref"]["asset_id"] == "123"
    assert result["node"]["asset_ref"]["url"] == "/uploads/generated/edited.png"
    assert result["edge"]["label"] == "调成白色"
    assert result["edge"]["relation_type"] == "variant_of"

