"""TDD: Canvas API route test (RED — endpoint doesn't exist yet)."""
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_get_canvas_returns_groups():
    """验证 GET /api/v1/projects/{id}/canvas 返回分组资产。"""
    import main
    app = main.app

    mock_plan = {
        "main_image": {"asset_type": "main_image", "prompt": "test"},
        "scene_images": [{"asset_type": "scene_image", "scene": "厨房"}],
        "white_bg": None,
        "selling_points": [],
        "video_scripts": [],
        "ad_material": None,
        "layout_plan": None,
    }

    mock_asset = type("Asset", (), {"asset_plan": mock_plan})()

    with patch(
        "app.api.canvas_routes.get_latest_asset_for_project",
        return_value=mock_asset,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/projects/1/canvas")

    assert resp.status_code == 200
    data = resp.json()
    assert "groups" in data
    assert len(data["groups"]) == 2  # main_image + scene_images
