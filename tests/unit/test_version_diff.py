"""
TDD (RED): Canvas version diff tests.
"""
import pytest


def test_diff_detects_text_change():
    """应检测文案字段的变更。"""
    from app.services.version_diff import VersionDiff

    diff = VersionDiff()
    changes = diff.compare(
        version_a={"title": "旧标题", "prompt": "unchanged", "color": "#333"},
        version_b={"title": "新标题", "prompt": "unchanged", "color": "#333"},
    )
    assert len(changes) == 1
    assert changes[0]["field"] == "title"
    assert changes[0]["type"] == "text"
    assert changes[0]["before"] == "旧标题"
    assert changes[0]["after"] == "新标题"


def test_diff_detects_color_change():
    """应检测颜色字段的变更。"""
    from app.services.version_diff import VersionDiff

    diff = VersionDiff()
    changes = diff.compare(
        version_a={"background_color": "#ffffff"},
        version_b={"background_color": "#000000"},
    )
    assert len(changes) == 1
    assert changes[0]["type"] == "color"


def test_diff_no_changes_returns_empty():
    """相同版本应返回空列表。"""
    from app.services.version_diff import VersionDiff

    diff = VersionDiff()
    changes = diff.compare(
        version_a={"a": 1, "b": "same"},
        version_b={"a": 1, "b": "same"},
    )
    assert changes == []


def test_diff_detects_new_and_removed_fields():
    """应检测新增和删除的字段。"""
    from app.services.version_diff import VersionDiff

    diff = VersionDiff()
    changes = diff.compare(
        version_a={"title": "x", "old_field": "removed"},
        version_b={"title": "x", "new_field": "added"},
    )
    field_names = {c["field"] for c in changes}
    assert "old_field" in field_names
    assert "new_field" in field_names


def test_diff_format_for_canvas():
    """format_for_canvas 返回前端可用的格式。"""
    from app.services.version_diff import VersionDiff

    diff = VersionDiff()
    changes = diff.compare(
        {"title": "旧", "color": "#fff"},
        {"title": "新", "color": "#fff"},
    )
    canvas_output = diff.format_for_canvas(changes)
    assert "version_a" in canvas_output
    assert "version_b" in canvas_output
    assert len(canvas_output["changes"]) == 1
