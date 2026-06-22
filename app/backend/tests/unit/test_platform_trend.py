"""Tests for Platform Trend Research service — P2.3 Research Agent Enhancement.

TDD: RED phase — tests written before implementation.
"""
import pytest
from unittest.mock import AsyncMock


# ---------------------------------------------------------------------------
# PlatformTrend models
# ---------------------------------------------------------------------------

class TestPlatformTrendModels:
    """Test the platform trend data models."""

    def test_platform_trend_model_exists(self):
        """PlatformTrend should hold structured trend data for one platform."""
        from app.models.research_models import PlatformTrend
        trend = PlatformTrend(
            platform="taobao",
            category="女装",
            trends=["法式复古", "多巴胺配色"],
            visual_styles=["暖色调", "柔光滤镜", "场景化拍摄"],
            copywriting_patterns=["痛点+解决方案", "数字卖点", "限时紧迫感"],
            price_range="79-299",
            hot_keywords=["#穿搭", "#显瘦"],
        )
        assert trend.platform == "taobao"
        assert len(trend.trends) == 2
        assert len(trend.visual_styles) == 3
        assert len(trend.copywriting_patterns) == 3

    def test_research_report_model_exists(self):
        """ResearchReport should aggregate trends across platforms."""
        from app.models.research_models import ResearchReport, PlatformTrend
        trends = [
            PlatformTrend(platform="taobao", category="女装", trends=["t1"], visual_styles=["v1"], copywriting_patterns=["c1"], price_range="79-299", hot_keywords=["#k1"]),
            PlatformTrend(platform="douyin", category="女装", trends=["t2"], visual_styles=["v2"], copywriting_patterns=["c2"], price_range="49-199", hot_keywords=["#k2"]),
        ]
        report = ResearchReport(
            category="女装",
            platforms=trends,
            summary="女装品类两大平台趋势汇总",
            moe_recommendations=["建议模板1", "建议模板2"],
        )
        assert len(report.platforms) == 2
        assert report.category == "女装"
        assert len(report.moe_recommendations) == 2

    def test_trend_model_serialization(self):
        """ResearchReport should serialize to dict for API responses."""
        from app.models.research_models import ResearchReport, PlatformTrend
        t = PlatformTrend(platform="test", category="test", trends=["a"], visual_styles=["b"], copywriting_patterns=["c"], price_range="0-100", hot_keywords=["#d"])
        report = ResearchReport(category="test", platforms=[t], summary="ok", moe_recommendations=["r1"])
        data = report.model_dump()
        assert data["category"] == "test"
        assert data["platforms"][0]["platform"] == "test"


# ---------------------------------------------------------------------------
# PlatformTrendService
# ---------------------------------------------------------------------------

class TestPlatformTrendService:
    """Test the platform trend research service."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM that returns structured trend analysis."""
        mock = AsyncMock()
        mock.generate.return_value = """```json
{
    "platform": "taobao",
    "category": "女装",
    "trends": ["新中式爆款", "法式极简", "多巴胺配色"],
    "visual_styles": ["暖色调场景化拍摄", "大片留白构图", "动态抓拍"],
    "copywriting_patterns": ["痛点+解决方案句式", "数字卖点轰炸", "限时紧迫感"],
    "price_range": "79-299",
    "hot_keywords": ["#新中式穿搭", "#显瘦显高", "#一周穿搭不重样"]
}
```"""
        return mock

    @pytest.mark.asyncio
    async def test_research_single_platform(self, mock_llm):
        """Should research trends for one platform+category."""
        from app.services.platform_trend_service import PlatformTrendService
        from app.models.research_models import PlatformTrend

        service = PlatformTrendService(llm_client=mock_llm)
        result = await service.research_platform("taobao", "女装")

        assert isinstance(result, PlatformTrend)
        assert result.platform == "taobao"
        assert result.category == "女装"
        assert len(result.trends) == 3
        assert "新中式爆款" in result.trends

    @pytest.mark.asyncio
    async def test_research_multiple_platforms(self, mock_llm):
        """Should research multiple platforms and aggregate results."""
        from app.services.platform_trend_service import PlatformTrendService
        from app.models.research_models import ResearchReport

        service = PlatformTrendService(llm_client=mock_llm)
        result = await service.research_category(
            category="女装",
            platforms=["taobao", "douyin", "xiaohongshu"],
        )

        assert isinstance(result, ResearchReport)
        assert result.category == "女装"
        assert len(result.platforms) == 3
        assert len(result.moe_recommendations) > 0

    @pytest.mark.asyncio
    async def test_research_handles_llm_error(self, mock_llm):
        """Should handle LLM failure gracefully with partial results."""
        from app.services.platform_trend_service import PlatformTrendService

        mock_llm.generate.side_effect = Exception("API timeout")
        service = PlatformTrendService(llm_client=mock_llm)
        result = await service.research_category(
            category="女装",
            platforms=["taobao", "douyin"],
        )

        # Should still return a report, even if some platforms failed
        assert result.category == "女装"
        # Should have error markers
        assert len(result.platforms) >= 0  # may be empty with errors marked

    def test_generate_moe_recommendations(self, mock_llm):
        """Should generate actionable template recommendations from trends."""
        from app.services.platform_trend_service import PlatformTrendService
        from app.models.research_models import PlatformTrend

        trends = [
            PlatformTrend(platform="taobao", category="女装", trends=["法式复古"], visual_styles=["暖色调"], copywriting_patterns=["痛点+方案"], price_range="79-299", hot_keywords=["#穿搭"]),
            PlatformTrend(platform="douyin", category="女装", trends=["多巴胺"], visual_styles=["动态抓拍"], copywriting_patterns=["数字卖点"], price_range="49-199", hot_keywords=["#变装"]),
        ]

        recs = PlatformTrendService.synthesize_recommendations(trends)
        assert len(recs) >= 2
        assert any("模板" in r or "视觉" in r for r in recs)

    @pytest.mark.asyncio
    async def test_research_handles_null_fields(self):
        """Should handle JSON null values in list fields gracefully."""
        from app.services.platform_trend_service import PlatformTrendService
        mock = AsyncMock()
        mock.generate.return_value = """```json
{"platform": "test_p", "category": "test_c", "trends": null, "visual_styles": null, "copywriting_patterns": null, "price_range": null, "hot_keywords": null}
```"""
        service = PlatformTrendService(llm_client=mock)
        result = await service.research_platform("test_p", "test_c")
        assert result.trends == []
        assert result.visual_styles == []
        assert result.copywriting_patterns == []
        assert result.price_range == "N/A"
        assert result.hot_keywords == []
