"""
策略预览测试 — 适配重构后端点（不再依赖 generate_visual_strategy）。

Endpoint now derives strategy directly from brief fields (2026-06-16).
"""
import pytest
from fastapi.testclient import TestClient

SAMPLE_BRIEF = {
    "product_name": "Commercial Chest Freezer",
    "category": "Commercial Refrigeration",
    "specifications": ["300L", "stainless steel"],
    "selling_points": ["fast cooling", "energy saving"],
    "target_market": ["US", "EU"],
    "target_customer": ["supermarket buyer"],
    "usage_scenarios": ["supermarket"],
    "brand_style": "工业专业风格",
}


class TestStrategyPreview:
    """策略预览端点 - 轻量级返回，不调用 LLM"""

    def test_strategy_preview_returns_strategy(self):
        from main import app
        client = TestClient(app)

        resp = client.post("/api/v1/strategy/preview", json={
            "brief": SAMPLE_BRIEF,
            "platform_id": None,
        })

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "visual_positioning" in data["strategy"]
        assert "Industrial" in data["strategy"]["visual_positioning"] or "Freezer" in data["strategy"]["visual_positioning"] or "Commercial" in data["strategy"]["visual_positioning"]
        assert "display_context" in data

    def test_strategy_preview_with_platform(self):
        from main import app
        client = TestClient(app)

        resp = client.post("/api/v1/strategy/preview", json={
            "brief": SAMPLE_BRIEF,
            "platform_id": "xiaohongshu",
        })

        assert resp.status_code == 200
        assert "strategy" in resp.json()

    def test_display_context_is_readable(self):
        from main import app
        client = TestClient(app)

        resp = client.post("/api/v1/strategy/preview", json={
            "brief": SAMPLE_BRIEF,
        })

        data = resp.json()
        ctx = data["display_context"]
        assert "Freezer" in ctx
        assert "B2C" in ctx  # ctx: "产品: Commercial Chest Freezer | 风格: 工业专业风格 | 受众: B2C"
