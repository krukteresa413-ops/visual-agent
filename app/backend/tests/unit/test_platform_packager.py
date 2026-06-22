"""
测试 Platform Packager — 多平台尺寸包生成。
PRD Step 6: 导出 — 多平台尺寸包，按平台重组素材。
"""

import pytest


SAMPLE_ASSETS = [
    {"id": "1", "type": "主图", "platform": "taobao", "url": "/img/a.jpg", "size": "800x800"},
    {"id": "2", "type": "白底图", "platform": "taobao", "url": "/img/b.jpg", "size": "800x800"},
    {"id": "3", "type": "封面图", "platform": "xiaohongshu", "url": "/img/c.jpg", "size": "1080x1440"},
    {"id": "4", "type": "短视频", "platform": "douyin", "url": "/vid/e.mp4", "size": "1080x1920"},
]


class TestPlatformPackager:
    """Test multi-platform size package generation."""

    def test_generate_package(self):
        """Should generate platform package manifest."""
        from app.services.platform_packager import PlatformPackager

        packager = PlatformPackager()
        manifest = packager.generate_manifest(
            assets=SAMPLE_ASSETS,
            project_name="测试项目",
        )

        assert manifest is not None
        assert "project_name" in manifest
        assert manifest["project_name"] == "测试项目"
        assert "packages" in manifest
        assert isinstance(manifest["packages"], list)

    def test_each_platform_has_package(self):
        """Each target platform should have its own package."""
        from app.services.platform_packager import PlatformPackager

        packager = PlatformPackager()
        manifest = packager.generate_manifest(
            assets=SAMPLE_ASSETS,
            project_name="测试",
        )

        platforms = [p["platform"] for p in manifest["packages"]]
        assert "taobao" in platforms
        assert "xiaohongshu" in platforms
        assert "douyin" in platforms

    def test_package_includes_size_info(self):
        """Each package should include size specifications."""
        from app.services.platform_packager import PlatformPackager

        packager = PlatformPackager()
        manifest = packager.generate_manifest(
            assets=SAMPLE_ASSETS,
            project_name="测试",
        )

        for pkg in manifest["packages"]:
            assert "platform" in pkg
            assert "size" in pkg
            assert "assets" in pkg
            assert "count" in pkg

    def test_empty_assets(self):
        """Should handle empty asset list."""
        from app.services.platform_packager import PlatformPackager

        packager = PlatformPackager()
        manifest = packager.generate_manifest(assets=[], project_name="空")

        assert manifest["packages"] == []

    def test_manifest_is_serializable(self):
        """Manifest should be JSON-serializable."""
        import json
        from app.services.platform_packager import PlatformPackager

        packager = PlatformPackager()
        manifest = packager.generate_manifest(
            assets=SAMPLE_ASSETS,
            project_name="测试",
        )

        encoded = json.dumps(manifest, ensure_ascii=False, indent=2)
        assert len(encoded) > 0
