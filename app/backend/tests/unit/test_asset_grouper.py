"""
测试 Asset Grouper — 多资产自动分组。
PRD Step 5: 画布协作 — 多资产自动分组，统一预览，按平台查看。
"""

import pytest


SAMPLE_ASSETS = [
    {"id": "1", "type": "主图", "platform": "taobao", "url": "/a.jpg", "size": "800x800"},
    {"id": "2", "type": "白底图", "platform": "taobao", "url": "/b.jpg", "size": "800x800"},
    {"id": "3", "type": "场景图", "platform": "xiaohongshu", "url": "/c.jpg", "size": "1080x1440"},
    {"id": "4", "type": "封面图", "platform": "xiaohongshu", "url": "/d.jpg", "size": "1080x1440"},
    {"id": "5", "type": "短视频", "platform": "douyin", "url": "/e.mp4", "size": "1080x1920"},
    {"id": "6", "type": "主图", "platform": "douyin", "url": "/f.jpg", "size": "1080x1920"},
    {"id": "7", "type": "主图", "platform": "taobao", "url": "/g.jpg", "size": "800x800"},
]


class TestAssetGrouper:
    """Test asset grouping for canvas display."""

    def test_group_by_platform(self):
        """Should group assets by platform."""
        from app.services.asset_grouper import AssetGrouper

        grouper = AssetGrouper()
        grouped = grouper.group_by_platform(SAMPLE_ASSETS)

        assert "taobao" in grouped
        assert "xiaohongshu" in grouped
        assert "douyin" in grouped
        assert len(grouped["taobao"]) == 3
        assert len(grouped["xiaohongshu"]) == 2
        assert len(grouped["douyin"]) == 2

    def test_group_by_type(self):
        """Should group assets by type."""
        from app.services.asset_grouper import AssetGrouper

        grouper = AssetGrouper()
        grouped = grouper.group_by_type(SAMPLE_ASSETS)

        assert "主图" in grouped
        assert "白底图" in grouped
        assert "场景图" in grouped
        assert "封面图" in grouped
        assert "短视频" in grouped
        assert len(grouped["主图"]) == 3

    def test_get_canvas_layout(self):
        """Should return canvas layout with sections."""
        from app.services.asset_grouper import AssetGrouper

        grouper = AssetGrouper()
        layout = grouper.get_canvas_layout(SAMPLE_ASSETS)

        assert "sections" in layout
        assert isinstance(layout["sections"], list)
        for section in layout["sections"]:
            assert "title" in section
            assert "platform" in section
            assert "assets" in section
            assert "size" in section

    def test_get_platform_sizes(self):
        """Should return list of platforms with their sizes."""
        from app.services.asset_grouper import AssetGrouper

        grouper = AssetGrouper()
        sizes = grouper.get_platform_sizes(SAMPLE_ASSETS)

        assert isinstance(sizes, dict)
        assert "taobao" in sizes
        # 淘宝应显示 800x800
        assert sizes["taobao"] == "800x800"

    def test_empty_assets(self):
        """Should handle empty asset list."""
        from app.services.asset_grouper import AssetGrouper

        grouper = AssetGrouper()
        grouped = grouper.group_by_platform([])
        assert grouped == {}

        layout = grouper.get_canvas_layout([])
        assert layout["sections"] == []

    def test_get_summary(self):
        """Should return summary stats."""
        from app.services.asset_grouper import AssetGrouper

        grouper = AssetGrouper()
        summary = grouper.get_summary(SAMPLE_ASSETS)

        assert summary["total_assets"] == 7
        assert summary["platform_count"] == 3
        assert summary["type_count"] == 5
