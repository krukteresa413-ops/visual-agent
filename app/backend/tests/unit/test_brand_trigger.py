"""TDD: Auto-trigger brand learning on asset modify (RED)."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_modify_text_triggers_brand_learning():
    """文本修改后应自动触发 BrandMemoryLearner.learn_from_edit。"""
    from app.api.asset_routes import modify_asset, ModifyRequest

    mock_llm = AsyncMock(return_value={
        "asset_type": "main_image", "prompt": "modified",
    })
    mock_learner = AsyncMock(return_value={"tone_updated": True})

    req = ModifyRequest(
        asset_type="main_image",
        original={"prompt": "old"},
        instruction="改文案",
        brief={"product_name": "test"},
        operation="text",
    )

    with patch("app.api.unified_generation_routes.agent._llm.call", mock_llm), \
         patch("app.api.asset_routes.brand_learner.learn_from_edit", mock_learner):
        result = await modify_asset(req)

    assert "modified" in result
    mock_learner.assert_called_once()
