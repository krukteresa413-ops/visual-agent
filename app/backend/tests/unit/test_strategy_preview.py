"""
策略预览测试。
验证：/strategy/preview 端点在生成前单独返回策略。
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

SAMPLE_BRIEF = {
    "product_name": "Commercial Chest Freezer",
    "category": "Commercial Refrigeration",
    "specifications": ["300L", "stainless steel"],
    "selling_points": ["fast cooling", "energy saving"],
    "target_market": ["US", "EU"],
    "target_customer": ["supermarket buyer"],
    "usage_scenarios": ["supermarket"],
}

MOCK_STRATEGY = {
    "visual_positioning": "专业商用制冷方案",
    "visual_style": "工业专业风格",
    "selling_points_priority": [
        {"rank": 1, "point": "Fast Cooling", "rationale": "核心卖点"},
    ],
    "brand_tone": "Professional",
    "audience_type": "B2B",
    "key_differentiators": "fast cooling, energy saving",
}


class TestStrategyPreview:
    """策略预览端点"""

    def test_strategy_preview_returns_strategy(self):
        from app.api.unified_generation_routes import agent

        with patch.object(agent, 'generate_visual_strategy', new_callable=AsyncMock) as mock:
            mock.return_value = MOCK_STRATEGY

            from fastapi.testclient import TestClient
            from main import app
            client = TestClient(app)

            resp = client.post("/api/v1/strategy/preview", json={
                "brief": SAMPLE_BRIEF,
                "platform_id": None,
            })

            assert resp.status_code == 200
            data = resp.json()
            assert "visual_positioning" in data["strategy"]
            assert data["strategy"]["visual_positioning"] == "专业商用制冷方案"
            assert "display_context" in data

    def test_strategy_preview_with_platform(self):
        from app.api.unified_generation_routes import agent

        with patch.object(agent, 'generate_visual_strategy', new_callable=AsyncMock) as mock:
            mock.return_value = MOCK_STRATEGY

            from fastapi.testclient import TestClient
            from main import app
            client = TestClient(app)

            resp = client.post("/api/v1/strategy/preview", json={
                "brief": SAMPLE_BRIEF,
                "platform_id": "xiaohongshu",
            })

            assert resp.status_code == 200
            # 验证策略生成成功（platform_id 由后续管线处理）
            assert "strategy" in resp.json()

    def test_display_context_is_readable(self):
        from app.api.unified_generation_routes import agent

        with patch.object(agent, 'generate_visual_strategy', new_callable=AsyncMock) as mock:
            mock.return_value = MOCK_STRATEGY

            from fastapi.testclient import TestClient
            from main import app
            client = TestClient(app)

            resp = client.post("/api/v1/strategy/preview", json={
                "brief": SAMPLE_BRIEF,
            })

            data = resp.json()
            ctx = data["display_context"]
            assert "专业商用制冷方案" in ctx
            assert "B2B" in ctx
