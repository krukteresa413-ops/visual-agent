"""
测试 Project Exporter — 可编辑项目文件导出。
PRD Step 6: 导出可编辑项目文件。
"""

import pytest


class TestProjectExporter:
    """Test editable project file export."""

    def test_export_project_json(self):
        """Should export project as structured JSON."""
        from app.services.project_exporter import ProjectExporter

        exporter = ProjectExporter()
        project_data = {
            "name": "2026Q2新品",
            "brief": {"product_name": "测试", "category": "食品"},
            "strategy": {"creative_angle": "健康"},
            "assets": [{"id": "1", "type": "主图", "url": "/a.jpg"}],
            "brand": {"name": "测试品牌", "colors": ["#fff"]},
        }

        exported = exporter.export(project_data, format="json")

        assert exported is not None
        assert "project" in exported
        assert exported["project"]["name"] == "2026Q2新品"
        assert "exported_at" in exported
        assert "version" in exported

    def test_export_includes_all_sections(self):
        """Export should include brief, strategy, assets, brand."""
        from app.services.project_exporter import ProjectExporter

        exporter = ProjectExporter()
        project_data = {
            "name": "测试",
            "brief": {"product_name": "X"},
            "strategy": {},
            "assets": [],
            "brand": {},
        }

        exported = exporter.export(project_data)

        assert "brief" in exported
        assert "strategy" in exported
        assert "assets" in exported
        assert "brand" in exported

    def test_export_minimal_project(self):
        """Should handle minimal project data."""
        from app.services.project_exporter import ProjectExporter

        exporter = ProjectExporter()
        exported = exporter.export({"name": "最小项目"})

        assert exported is not None
        assert exported["project"]["name"] == "最小项目"
        assert exported["brief"] == {}
        assert exported["assets"] == []

    def test_export_is_serializable(self):
        """Exported data should be JSON-serializable."""
        import json
        from app.services.project_exporter import ProjectExporter

        exporter = ProjectExporter()
        exported = exporter.export({
            "name": "测试",
            "brief": {"product_name": "X", "category": "食品"},
            "strategy": {"creative_angle": "健康"},
            "assets": [{"id": "1", "type": "主图"}],
            "brand": {"name": "品牌A", "colors": ["#fff"]},
        })

        encoded = json.dumps(exported, ensure_ascii=False, indent=2)
        assert len(encoded) > 0
        # Should be valid JSON
        json.loads(encoded)
