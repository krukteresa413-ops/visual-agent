import pytest
from unittest.mock import AsyncMock

class TestDetailPage:
    @pytest.mark.asyncio
    async def test_generate_detail_page_returns_modules(self):
        from app.services.visual_agent import VisualAgent
        agent = VisualAgent()
        agent._llm.call = AsyncMock(return_value={"page_goal":"t","target_platform":"a","target_audience":"B2B","total_modules":7,"estimated_scroll_depth":"4","modules":[{"order":1,"module_type":"hero_banner","title":"H","content_description":"d","visual_suggestion":"v"}]})
        result = await agent.generate_detail_page(brief={"product_name":"T","category":"T","specifications":["a"],"selling_points":["a"],"target_market":["a"],"usage_scenarios":["a"],"target_customer":["a"],"brand_style":"a","compliance_notes":["a"]})
        assert result.total_modules == 7

    @pytest.mark.asyncio
    async def test_agent_has_new_methods(self):
        from app.services.visual_agent import VisualAgent
        agent = VisualAgent()
        assert hasattr(agent, "generate_detail_page")
        assert hasattr(agent, "generate_visual_strategy")
