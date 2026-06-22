import pytest, json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.models.project import Project
from app.models.visual_asset_plan import VisualAssetPlan

SAMPLE_BRIEF = {"product_name":"Test","category":"Test","specifications":["x"],"selling_points":["x"],"target_market":["x"],"usage_scenarios":["x"]}
MOCKS = [
    {"asset_type":"main_image","goal":"m","composition":"c","background":"b","prompt":"p"},
    {"asset_type":"white_bg","goal":"m","instructions":"i"},
    [{"scene_name":"s","target_user":"u","scene_narrative":"n","visual_elements":[],"product_position":"p","prompt":"p"}],
    [{"title":"t","description":"d","visual_representation":"v","icon_suggestion":"i","layout_suggestion":"l"}],
    [{"video_goal":"v","duration_seconds":15,"storyboard":[],"cta":"c","material_requirements":[],"pacing":"p"}],
    {"ad_goal":"a","target_audience":"a","ad_angle":"a","material_list":[],"shot_sequence":[],"hook":"h","key_selling_points":[],"cta":"c","platform_suggestion":"p"},
]

@pytest.fixture
def db_session():
    e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=e)
    s = sessionmaker(bind=e)()
    s.add(Project(name="Test"))
    s.commit()
    yield s
    s.close()

class TestSaveGeneration:
    @pytest.mark.asyncio
    async def test_generate_and_save(self, db_session):
        from app.services.visual_agent import VisualAgent
        from app.db.crud_visual_asset import get_visual_asset_plan_by_project
        agent = VisualAgent()
        agent._llm.call = AsyncMock(side_effect=MOCKS)
        agent.generate_images_from_plan = AsyncMock(return_value={
            "main_image": None,
            "white_bg": None,
            "scene_images": [None],
        })
        with patch("app.services.layout_agent.LayoutAgent.generate_layout", new=AsyncMock(side_effect=RuntimeError("skip layout in persistence unit test"))):
            result = await agent.generate_all(project_id=1, brief=SAMPLE_BRIEF)
        d = result.model_dump()
        p = VisualAssetPlan(project_id=d["project_id"],
            main_image_json=json.dumps(d["main_image"]),
            white_bg_json=json.dumps(d["white_bg"]),
            scene_images_json=json.dumps(d["scene_images"]),
            selling_points_json=json.dumps(d["selling_points"]),
            video_scripts_json=json.dumps(d["video_scripts"]),
            ad_material_json=json.dumps(d["ad_material"]))
        db_session.add(p)
        db_session.commit()
        saved = get_visual_asset_plan_by_project(db_session, project_id=1)
        assert saved is not None
        assert json.loads(saved.main_image_json)["asset_type"] == "main_image"
