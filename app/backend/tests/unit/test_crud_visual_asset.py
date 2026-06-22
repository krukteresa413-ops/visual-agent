"""
visual_asset_plans CRUD 测试。
使用内存 SQLite 数据库。
"""
import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.visual_asset_plan import VisualAssetPlan
from app.models.project import Project


@pytest.fixture
def db_session():
    """创建内存 SQLite 数据库"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # Create a test project (FK required)
    project = Project(name="Test Project")
    session.add(project)
    session.commit()
    yield session
    session.close()


class TestVisualAssetPlanCRUD:

    def test_create_visual_asset_plan(self, db_session):
        from app.db.crud_visual_asset import create_visual_asset_plan
        from app.schemas.visual_asset_plan import VisualAssetPlanCreate

        data = VisualAssetPlanCreate(
            project_id=1,
            main_image_json=json.dumps({"asset_type": "main_image", "goal": "test"}),
            white_bg_json=json.dumps({"asset_type": "white_bg"}),
            scene_images_json=json.dumps([{"scene_name": "s1"}]),
            selling_points_json=json.dumps([{"title": "sp1"}]),
            video_scripts_json=json.dumps([{"video_goal": "v1"}]),
            ad_material_json=json.dumps({"ad_goal": "a1"}),
        )

        result = create_visual_asset_plan(db_session, data)
        assert result.id is not None
        assert result.project_id == 1
        parsed = json.loads(result.main_image_json)
        assert parsed["asset_type"] == "main_image"

    def test_get_visual_asset_plan_by_project(self, db_session):
        from app.db.crud_visual_asset import create_visual_asset_plan, get_visual_asset_plan_by_project
        from app.schemas.visual_asset_plan import VisualAssetPlanCreate

        data = VisualAssetPlanCreate(
            project_id=1,
            main_image_json="{}", white_bg_json="{}",
            scene_images_json="[]", selling_points_json="[]",
            video_scripts_json="[]", ad_material_json="{}",
        )
        create_visual_asset_plan(db_session, data)

        result = get_visual_asset_plan_by_project(db_session, project_id=1)
        assert result is not None
        assert result.project_id == 1

    def test_get_nonexistent_returns_none(self, db_session):
        from app.db.crud_visual_asset import get_visual_asset_plan_by_project
        result = get_visual_asset_plan_by_project(db_session, project_id=999)
        assert result is None
