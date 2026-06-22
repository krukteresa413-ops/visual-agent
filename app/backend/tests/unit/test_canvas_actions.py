import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_canvas_action_starts_existing_progress_task_and_returns_task_id():
    import main
    from app.services.generation_tracker import GenerationTracker

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
async def test_canvas_action_task_poll_returns_variant_node_and_relation_edge():
    import asyncio
    import main

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
