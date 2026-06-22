"""
测试 Markdown 导出。
PRD：输出内容可复制、修改、下载。
"""
import pytest


class TestMarkdownExport:

    def test_export_asset_plan_to_markdown(self):
        from app.services.exporter import to_markdown

        plan = {
            "project_id": 1,
            "main_image": {
                "asset_type": "main_image",
                "goal": "突出产品主体",
                "composition": "居中45度角",
                "background": "浅灰背景",
                "prompt": "A commercial freezer, centered, 4K",
            },
            "scene_images": [
                {"scene_name": "supermarket", "prompt": "freezer in supermarket..."}
            ],
            "selling_points": [
                {"title": "Fast Cooling", "description": "Quick temperature drop"}
            ],
            "video_scripts": [
                {"duration_seconds": 15, "cta": "Learn More", "storyboard": []}
            ],
            "ad_material": {"ad_goal": "引流", "hook": "Tired of breakdowns?", "cta": "Get Quote"},
            "white_bg": {"goal": "平台上架", "instructions": "纯白背景"},
        }

        md = to_markdown(plan)

        assert "# 视觉素材方案" in md
        assert "## 主图方案" in md
        assert "Fast Cooling" in md
        assert "A commercial freezer" in md
        assert len(md) > 200

    def test_markdown_has_all_six_sections(self):
        from app.services.exporter import to_markdown

        plan = {
            "project_id": 1,
            "main_image": {"goal": "t", "prompt": "t"},
            "white_bg": {"goal": "t", "instructions": "t"},
            "scene_images": [],
            "selling_points": [],
            "video_scripts": [],
            "ad_material": {"ad_goal": "t", "hook": "t", "cta": "t"},
        }

        md = to_markdown(plan)
        sections = ["主图方案", "白底图方案", "场景图方案", "卖点图模块", "短视频脚本", "广告素材方案"]
        for section in sections:
            assert section in md, f"缺少章节: {section}"
