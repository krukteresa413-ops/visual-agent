"""
visual_asset_plans 模型和 Schema 测试。
"""
import pytest
import json
from pydantic import ValidationError


class TestVisualAssetPlanModel:
    """测试数据库模型（不含 DB 连接）"""

    def test_model_has_all_required_columns(self):
        """模型包含六类素材 + project_id + 时间戳"""
        from app.models.visual_asset_plan import VisualAssetPlan

        assert hasattr(VisualAssetPlan, '__tablename__')
        cols = [c.name for c in VisualAssetPlan.__table__.columns]
        assert 'id' in cols
        assert 'project_id' in cols
        assert 'main_image_json' in cols
        assert 'white_bg_json' in cols
        assert 'scene_images_json' in cols
        assert 'selling_points_json' in cols
        assert 'video_scripts_json' in cols
        assert 'ad_material_json' in cols
        assert 'created_at' in cols

    def test_model_table_name(self):
        from app.models.visual_asset_plan import VisualAssetPlan
        assert VisualAssetPlan.__tablename__ == 'visual_asset_plans'


class TestVisualAssetPlanSchema:
    """测试 Pydantic Schema"""

    def test_create_schema_accepts_valid_data(self):
        from app.schemas.visual_asset_plan import VisualAssetPlanCreate

        data = {
            "project_id": 1,
            "main_image_json": json.dumps({"asset_type": "main_image", "goal": "test"}),
            "white_bg_json": json.dumps({"asset_type": "white_bg", "goal": "test"}),
            "scene_images_json": json.dumps([{"scene_name": "test"}]),
            "selling_points_json": json.dumps([{"title": "test"}]),
            "video_scripts_json": json.dumps([{"video_goal": "test"}]),
            "ad_material_json": json.dumps({"ad_goal": "test"}),
        }
        schema = VisualAssetPlanCreate(**data)
        assert schema.project_id == 1
        parsed = json.loads(schema.main_image_json)
        assert parsed["asset_type"] == "main_image"

    def test_create_schema_requires_project_id(self):
        from app.schemas.visual_asset_plan import VisualAssetPlanCreate
        # project_id is required
        with pytest.raises(ValidationError):
            VisualAssetPlanCreate(
                main_image_json="{}",
                white_bg_json="{}",
                scene_images_json="[]",
                selling_points_json="[]",
                video_scripts_json="[]",
                ad_material_json="{}",
            )
