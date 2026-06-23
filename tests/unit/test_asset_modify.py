"""
资产修改端点测试 — 画布中点选素材 → 自然语言修改 → 返回新版本
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

SAMPLE_BRIEF = {
    "product_name": "300L Chest Freezer",
    "category": "Commercial Refrigeration",
    "specifications": ["300L", "stainless steel"],
    "selling_points": ["fast cooling", "energy saving"],
}

ORIGINAL_MAIN_IMAGE = {
    "asset_type": "main_image",
    "goal": "展示产品专业品质",
    "composition": "产品居中，工业背景",
    "background": "灰色工业风",
    "prompt": "A commercial freezer in industrial setting",
    "status": "draft",
}

ORIGINAL_SCENE = {
    "scene_name": "supermarket",
    "target_user": "supermarket buyer",
    "scene_narrative": "超市冷藏区",
    "visual_elements": ["货架", "食品"],
    "product_position": "前景居中",
    "prompt": "Freezer in supermarket",
}

MODIFIED_MAIN_IMAGE = {
    "asset_type": "main_image",
    "goal": "展示产品在都市环境中的专业品质",
    "composition": "产品居中，城市夜景背景",
    "background": "城市夜景，冷色调",
    "prompt": "A commercial freezer with city night skyline background, cool tones",
    "status": "draft",
}


class TestAssetModify:
    """资产修改端点"""

    def test_modify_main_image(self):
        from app.api.unified_generation_routes import agent as va_agent

        with patch.object(va_agent._llm, 'call', new_callable=AsyncMock) as mock:
            mock.return_value = MODIFIED_MAIN_IMAGE

            from main import app
            client = TestClient(app)

            resp = client.post("/api/v1/asset/modify", json={
                "asset_type": "main_image",
                "original": ORIGINAL_MAIN_IMAGE,
                "instruction": "背景换成城市夜景，色调偏冷",
                "brief": SAMPLE_BRIEF,
            })

            assert resp.status_code == 200
            data = resp.json()
            assert data["modified"]["background"] == "城市夜景，冷色调"
            assert "night" in data["modified"]["prompt"].lower()

    def test_modify_scene_image(self):
        from app.api.unified_generation_routes import agent as va_agent

        with patch.object(va_agent._llm, 'call', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "scene_name": "city street",
                "target_user": "urban shopper",
                "scene_narrative": "城市便利店门口",
                "visual_elements": ["街道", "行人"],
                "product_position": "右侧",
                "prompt": "Freezer on city street at night",
            }

            from main import app
            client = TestClient(app)

            resp = client.post("/api/v1/asset/modify", json={
                "asset_type": "scene_image",
                "original": ORIGINAL_SCENE,
                "instruction": "场景改成城市街道夜景",
                "brief": SAMPLE_BRIEF,
            })

            assert resp.status_code == 200
            data = resp.json()
            assert "street" in data["modified"]["scene_name"]

    def test_modify_preserves_structure(self):
        """修改后保持与原结构一致"""
        from app.api.unified_generation_routes import agent as va_agent

        with patch.object(va_agent._llm, 'call', new_callable=AsyncMock) as mock:
            mock.return_value = MODIFIED_MAIN_IMAGE

            from main import app
            client = TestClient(app)

            resp = client.post("/api/v1/asset/modify", json={
                "asset_type": "main_image",
                "original": ORIGINAL_MAIN_IMAGE,
                "instruction": "换背景",
                "brief": SAMPLE_BRIEF,
            })

            data = resp.json()
            modified = data["modified"]
            # 保持 asset_type 不变
            assert modified["asset_type"] == "main_image"
            # 保持所有原始字段存在
            for key in ["goal", "composition", "background", "prompt"]:
                assert key in modified

    def test_modify_with_empty_instruction_returns_original(self):
        """空修改指令应快速返回且不做LLM调用"""
        from app.api.unified_generation_routes import agent as va_agent

        with patch.object(va_agent._llm, 'call', new_callable=AsyncMock) as mock:
            from main import app
            client = TestClient(app)

            resp = client.post("/api/v1/asset/modify", json={
                "asset_type": "main_image",
                "original": ORIGINAL_MAIN_IMAGE,
                "instruction": "",
                "brief": SAMPLE_BRIEF,
            })

            assert resp.status_code == 200
            # 空指令不调用 LLM
            mock.assert_not_called()
