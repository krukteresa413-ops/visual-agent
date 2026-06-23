"""
Visual Tasks API 集成测试。
使用 FastAPI TestClient + mock LLM。
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

SAMPLE_BRIEF = {
    "product_name": "Commercial Chest Freezer",
    "category": "Commercial Refrigeration",
    "specifications": ["300L", "stainless steel"],
    "selling_points": ["fast cooling", "energy saving"],
    "target_market": ["US"],
    "usage_scenarios": ["supermarket"],
}


@pytest.mark.asyncio
async def test_generate_main_image_endpoint():
    import main; app = main.app

    mock_return = MagicMock()
    mock_return.model_dump.return_value = {
        "asset_type": "main_image",
        "goal": "test",
        "composition": "centered",
        "background": "white",
        "prompt": "test prompt",
        "status": "draft",
    }

    with patch("app.api.visual_tasks.agent.generate_main_image", new_callable=AsyncMock, return_value=mock_return):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/visual-tasks/main-image",
                json={"project_id": 1, "brief": SAMPLE_BRIEF},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["asset_type"] == "main_image"
