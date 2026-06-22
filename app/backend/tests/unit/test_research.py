"""TDD: Research template matcher tests (RED — module missing)."""
import pytest


def test_match_template_returns_competitors():
    """匹配品类+平台应返回竞品和趋势数据。"""
    from app.services.research_templates import match_template

    result = match_template(category="女装", platform="taobao")
    assert len(result["competitors"]) >= 2
    assert len(result["trends"]) >= 2


def test_match_template_fallback_for_unknown_category():
    """未知品类应返回通用模板。"""
    from app.services.research_templates import match_template

    result = match_template(category="航天器", platform="taobao")
    assert "通用" in result["category"] or len(result["competitors"]) > 0


def test_match_template_fallback_for_unknown_platform():
    """未知平台应返回通用模板。"""
    from app.services.research_templates import match_template

    result = match_template(category="女装", platform="火星")
    assert len(result["competitors"]) > 0
