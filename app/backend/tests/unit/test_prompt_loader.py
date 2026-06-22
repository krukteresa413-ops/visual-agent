"""
Prompt模板加载器测试。
验证：模板能正确渲染产品字段，缺失字段有默认值。
"""
import pytest


class TestPromptLoader:

    def test_load_and_render_main_image_template(self):
        from app.services.prompt_loader import PromptLoader

        loader = PromptLoader()
        rendered = loader.render("main_image", {
            "product_name": "Commercial Chest Freezer",
            "category": "Commercial Refrigeration",
            "specifications": ["300L", "stainless steel"],
            "selling_points": ["fast cooling", "energy saving"],
            "target_market": ["US", "EU"],
            "usage_scenarios": ["supermarket", "restaurant"],
            "brand_style": "professional, clean",
            "compliance_notes": ["no fake certification"],
        })

        assert "Commercial Chest Freezer" in rendered
        assert "fast cooling" in rendered
        assert "no fake certification" in rendered

    def test_missing_optional_fields_use_defaults(self):
        from app.services.prompt_loader import PromptLoader

        loader = PromptLoader()
        # compliance_notes 和 brand_style 省略
        rendered = loader.render("main_image", {
            "product_name": "Test Product",
            "category": "Test",
            "specifications": ["spec1"],
            "selling_points": ["point1"],
            "target_market": ["US"],
            "usage_scenarios": ["scenario1"],
        })

        assert "Test Product" in rendered
        # 不应该崩溃

    def test_nonexistent_template_raises_error(self):
        from app.services.prompt_loader import PromptLoader

        loader = PromptLoader()
        with pytest.raises(FileNotFoundError):
            loader.render("nonexistent_template", {})
