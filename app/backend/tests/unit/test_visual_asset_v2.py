"""
测试视觉素材生成结果的持久化。
PRD：保存输入资料、Prompt、脚本、生成结果。
"""
import pytest
from unittest.mock import patch, MagicMock


class TestVisualAssetCRUD:

    def test_save_asset_plan(self):
        """保存一次完整的六类素材生成结果"""
        from app.db.crud_visual_asset_v2 import save_asset_plan

        mock_db = MagicMock()

        result = save_asset_plan(
            db=mock_db,
            project_id=1,
            brief_id=1,
            asset_plan={
                "main_image": {"asset_type": "main_image", "goal": "test", "prompt": "test"},
                "white_bg": {"asset_type": "white_bg", "goal": "test", "instructions": "test"},
                "scene_images": [],
                "selling_points": [],
                "video_scripts": [],
                "ad_material": {"ad_goal": "test", "cta": "test"},
            },
            model_used="deepseek-chat",
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    def test_get_latest_asset_plan_by_project(self):
        """获取某项目最新一次生成结果"""
        from app.db.crud_visual_asset_v2 import get_latest_by_project

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = get_latest_by_project(db=mock_db, project_id=999)
        assert result is None
