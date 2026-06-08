import pytest
from unittest.mock import AsyncMock, patch

class TestBriefParser:
    @pytest.mark.asyncio
    async def test_parse_returns_missing_fields(self):
        from app.services.brief_parser import parse_brief_text
        mock_llm = AsyncMock()
        mock_llm.call.return_value = {'product_name':'Test Freezer','category':None,'specifications':[],'selling_points':[]}
        result = await parse_brief_text('Test Freezer 300L', llm=mock_llm)
        assert result['product_name'] == 'Test Freezer'
        missing_names = [m['field'] for m in result['missing_fields']]
        assert 'category' in missing_names
        assert 'selling_points' in missing_names

    @pytest.mark.asyncio
    async def test_parse_complete_brief_no_required_missing(self):
        from app.services.brief_parser import parse_brief_text
        mock_llm = AsyncMock()
        mock_llm.call.return_value = {'product_name':'Freezer','category':'Refrigeration','specifications':['300L'],'selling_points':['fast cooling'],'target_market':['US'],'usage_scenarios':['supermarket']}
        result = await parse_brief_text('...', llm=mock_llm)
        required_missing = [m for m in result['missing_fields'] if m['level'] == 'required']
        assert len(required_missing) == 0
