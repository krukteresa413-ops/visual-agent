"""
TDD (RED): Visual Direction Agent tests.
"""
import pytest


def test_extract_style_params_returns_palette():
    """从 brief 提取风格参数应包含配色方案。"""
    from app.services.visual_direction import VisualDirection

    vd = VisualDirection()
    params = vd.extract_style_params({
        "product_name": "有机红茶",
        "category": "茶饮",
        "brand_style": "自然/禅意/东方美学",
    })
    assert "primary_color" in params
    assert "style_keywords" in params
    assert len(params["style_keywords"]) >= 2


def test_generate_moodboard_context_includes_all_sections():
    """Moodboard 上下文应包含配色、字体、构图三部分。"""
    from app.services.visual_direction import VisualDirection

    vd = VisualDirection()
    mood = vd.build_moodboard_context(
        style_params={
            "primary_color": "#2d5a27",
            "secondary_color": "#e8d5b7",
            "style_keywords": ["自然", "禅意", "留白"],
            "typography": "serif",
            "composition": "centered",
        }
    )
    assert "配色" in mood
    assert "字体" in mood
    assert "构图" in mood
    assert "#2d5a27" in mood


def test_consistency_check_detects_mismatch():
    """一致性检查应检测色调偏离。"""
    from app.services.visual_direction import VisualDirection

    vd = VisualDirection()
    style = {
        "primary_color": "#2d5a27",
        "style_keywords": ["禅意", "留白", "极简"],
    }
    result = vd.check_consistency(
        style_params=style,
        asset_description="大红色背景，霓虹灯字体，赛博朋克风格",
    )
    assert result["consistent"] is False
    assert len(result["warnings"]) >= 1


def test_consistency_check_passes_matching_style():
    """风格匹配时应通过一致性检查。"""
    from app.services.visual_direction import VisualDirection

    vd = VisualDirection()
    style = {"primary_color": "#2d5a27", "style_keywords": ["自然", "留白"]}
    result = vd.check_consistency(
        style_params=style,
        asset_description="墨绿色背景，大面积留白，极简自然风格",
    )
    assert result["consistent"] is True
