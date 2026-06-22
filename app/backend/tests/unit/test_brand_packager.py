"""
测试 Brand Packager — 品牌资产包导出。
PRD Step 6: 保存品牌记忆，导出品牌资产包供后续复用。
"""

import pytest


SAMPLE_BRAND = {
    "name": "沐源甲科技",
    "logo_url": "/brand/logo.png",
    "colors": ["#1a1a2e", "#e94560"],
    "fonts": ["思源黑体", "PingFang SC"],
    "keywords": ["科技", "专业", "创新"],
    "forbidden_styles": ["可爱", "花哨"],
    "tone": "专业可靠",
}

SAMPLE_ASSETS = [
    {"id": "1", "type": "主图", "platform": "taobao", "url": "/img/a.jpg"},
    {"id": "2", "type": "封面图", "platform": "xiaohongshu", "url": "/img/c.jpg"},
]


class TestBrandPackager:
    """Test brand asset package export."""

    def test_generate_brand_package(self):
        """Should generate brand asset package manifest."""
        from app.services.brand_packager import BrandPackager

        packager = BrandPackager()
        manifest = packager.generate_manifest(
            brand=SAMPLE_BRAND,
            assets=SAMPLE_ASSETS,
            project_name="2026Q2新品",
        )

        assert manifest is not None
        assert "brand_name" in manifest
        assert manifest["brand_name"] == "沐源甲科技"
        assert "brand_assets" in manifest
        assert "project_assets" in manifest

    def test_package_includes_brand_guidelines(self):
        """Package should include brand visual guidelines."""
        from app.services.brand_packager import BrandPackager

        packager = BrandPackager()
        manifest = packager.generate_manifest(
            brand=SAMPLE_BRAND,
            assets=SAMPLE_ASSETS,
            project_name="测试",
        )

        guidelines = manifest.get("brand_guidelines", {})
        assert "colors" in guidelines
        assert "fonts" in guidelines
        assert guidelines["colors"] == SAMPLE_BRAND["colors"]

    def test_package_includes_forbidden_styles(self):
        """Package should include brand restrictions."""
        from app.services.brand_packager import BrandPackager

        packager = BrandPackager()
        manifest = packager.generate_manifest(
            brand=SAMPLE_BRAND,
            assets=SAMPLE_ASSETS,
            project_name="测试",
        )

        restrictions = manifest.get("restrictions", {})
        assert "forbidden_styles" in restrictions
        assert SAMPLE_BRAND["forbidden_styles"][0] in restrictions["forbidden_styles"]

    def test_partial_brand_info(self):
        """Should handle partial brand info gracefully."""
        from app.services.brand_packager import BrandPackager

        packager = BrandPackager()
        manifest = packager.generate_manifest(
            brand={"name": "简"},
            assets=[],
            project_name="测试",
        )

        assert manifest is not None
        assert manifest["brand_name"] == "简"
        assert manifest["brand_assets"] == []

    def test_manifest_is_serializable(self):
        """Manifest should be JSON-serializable."""
        import json
        from app.services.brand_packager import BrandPackager

        packager = BrandPackager()
        manifest = packager.generate_manifest(
            brand=SAMPLE_BRAND,
            assets=SAMPLE_ASSETS,
            project_name="测试",
        )

        encoded = json.dumps(manifest, ensure_ascii=False, indent=2)
        assert len(encoded) > 0
