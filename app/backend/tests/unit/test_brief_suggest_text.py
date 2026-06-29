"""文字 Brief 抽取端点(需求一):从一句话需求抽取问卷字段,用于自动判断是否追问。

只 import vision_routes(无 DB);LLM 被替身,不发真请求。
"""
import pytest
from unittest.mock import patch

from app.api import vision_routes as vr


def test_filter_brief_fields_drops_empty_and_unknown():
    raw = {"product_name": "防晒衣", "category": "", "junk": "y", "selling_points": []}
    out = vr._filter_brief_fields(raw, vr._BRIEF_TEXT_ALLOWED)
    assert out == {"product_name": "防晒衣"}


def test_filter_brief_fields_non_dict():
    assert vr._filter_brief_fields("not-a-dict", vr._BRIEF_TEXT_ALLOWED) == {}


@pytest.mark.asyncio
async def test_brief_suggest_text_extracts_and_filters():
    async def fake_analyze(images, prompt, **kw):
        assert images == []  # 文字抽取走纯文字(无图)
        return {
            "success": True,
            "content": '{"product_name":"防晒衣","category":"服饰鞋包",'
                       '"selling_points":["UPF50+","透气"],"target_audience":"","usage_scenarios":[]}',
        }

    with patch.object(vr.vision_service, "analyze", side_effect=fake_analyze):
        res = await vr.brief_suggest_text(vr.BriefSuggestTextRequest(text="夏天户外防晒衣 UPF50 透气"))

    assert res["success"] is True
    f = res["fields"]
    assert f["product_name"] == "防晒衣"
    assert f["category"] == "服饰鞋包"
    assert f["selling_points"] == ["UPF50+", "透气"]
    assert "target_audience" not in f      # 空 -> 被过滤
    assert "usage_scenarios" not in f


@pytest.mark.asyncio
async def test_brief_suggest_text_empty_input_returns_false():
    res = await vr.brief_suggest_text(vr.BriefSuggestTextRequest(text="   "))
    assert res == {"success": False, "fields": {}}


@pytest.mark.asyncio
async def test_brief_suggest_text_llm_failure_is_nonblocking():
    async def fail_analyze(images, prompt, **kw):
        return {"success": False, "error": "vision unavailable"}

    with patch.object(vr.vision_service, "analyze", side_effect=fail_analyze):
        res = await vr.brief_suggest_text(vr.BriefSuggestTextRequest(text="一款智能手表"))
    assert res == {"success": False, "fields": {}}
