"""
TDD Step 1 (RED): Canvas grouping tests.
Tests for function that groups VisualAsset plan data by type.
"""
import json
import pytest


# Import will fail until module exists
from app.api.canvas import group_assets_by_type


def make_asset_plan(**overrides):
    """Helper: create a VisualAsset-like dict with default test data."""
    plan = {
        "main_image": {"asset_type": "main_image", "prompt": "test", "goal": "展示产品"},
        "white_bg": {"asset_type": "white_bg", "prompt": "white bg"},
        "scene_images": [
            {"asset_type": "scene_image", "scene": "厨房", "prompt": "厨房场景"},
            {"asset_type": "scene_image", "scene": "客厅", "prompt": "客厅场景"},
        ],
        "selling_points": [
            {"asset_type": "selling_point", "title": "快速制冷"},
            {"asset_type": "selling_point", "title": "节能省电"},
        ],
        "video_scripts": [],
        "ad_material": None,
        "layout_plan": {"canvas_width": 800, "canvas_height": 800},
    }
    plan.update(overrides)
    return plan


def test_group_assets_classifies_by_type():
    """验证资产按类型正确分组。"""
    plan = make_asset_plan()

    groups = group_assets_by_type(plan)

    # 应该有 main_image, white_bg, scene_images, selling_points, layout_plan
    group_names = {g["name"] for g in groups}
    assert "主图" in group_names
    assert "白底图" in group_names
    assert "场景图" in group_names
    assert "卖点" in group_names
    assert "排版方案" in group_names


def test_group_assets_single_item_gets_correct_count():
    """验证每个分组内资产数量正确。"""
    plan = make_asset_plan()

    groups = group_assets_by_type(plan)

    by_name = {g["name"]: g["assets"] for g in groups}
    assert len(by_name["主图"]) == 1
    assert len(by_name["白底图"]) == 1
    assert len(by_name["场景图"]) == 2
    assert len(by_name["卖点"]) == 2


def test_group_assets_empty_plan_returns_no_error():
    """验证空 plan 返回空列表不报错。"""
    groups = group_assets_by_type({})
    assert groups == []


def test_group_assets_none_fields_skipped():
    """验证 None 值字段被跳过。"""
    plan = make_asset_plan(main_image=None, white_bg=None, ad_material=None)

    groups = group_assets_by_type(plan)

    group_names = {g["name"] for g in groups}
    assert "主图" not in group_names
    assert "白底图" not in group_names
    assert "场景图" in group_names  # still present
