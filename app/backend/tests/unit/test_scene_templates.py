"""
测试 Scene Template Service — 场景模板选择。
PRD Step 1: 用户选择场景模板（电商上新、小红书种草、餐饮活动、品牌视觉系统等）。
"""

import pytest


class TestSceneTemplateService:
    """Test scene template listing and selection."""

    def test_list_templates(self):
        """Should list all available scene templates."""
        from app.services.scene_templates import SceneTemplateService

        service = SceneTemplateService()
        templates = service.list_templates()

        assert templates is not None
        assert isinstance(templates, list)
        assert len(templates) >= 4  # at least 4 templates
        for t in templates:
            assert "id" in t
            assert "name" in t
            assert "description" in t
            assert "platforms" in t
            assert "default_assets" in t

    def test_get_template(self):
        """Should get a specific template by ID."""
        from app.services.scene_templates import SceneTemplateService

        service = SceneTemplateService()
        template = service.get_template("ecommerce_launch")

        assert template is not None
        assert template["name"] == "电商上新"
        assert "taobao" in template["platforms"]

    def test_get_template_unknown(self):
        """Should return None for unknown template ID."""
        from app.services.scene_templates import SceneTemplateService

        service = SceneTemplateService()
        template = service.get_template("nonexistent")

        assert template is None

    def test_template_provides_default_brief(self):
        """Each template should provide a default brief structure."""
        from app.services.scene_templates import SceneTemplateService

        service = SceneTemplateService()
        template = service.get_template("social_种草")

        assert template is not None
        assert "default_brief" in template
        brief = template["default_brief"]
        assert "category" in brief
        assert "platform" in brief

    def test_apply_template(self):
        """Should merge template defaults with user input."""
        from app.services.scene_templates import SceneTemplateService

        service = SceneTemplateService()
        user_input = {"product_name": "测试产品"}
        merged = service.apply_template("ecommerce_launch", user_input)

        assert merged is not None
        assert merged["product_name"] == "测试产品"
        # Template should fill in missing fields
        assert "platform" in merged
        assert "category" in merged
