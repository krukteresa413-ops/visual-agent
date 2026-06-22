"""Markdown 导出测试"""
import pytest, json
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.models.project import Project
from app.models.visual_asset_plan import VisualAssetPlan

@pytest.fixture
def db_session():
    e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=e)
    s = sessionmaker(bind=e)()
    s.add(Project(name="Test"))
    s.commit()
    plan = VisualAssetPlan(project_id=1,
        main_image_json=json.dumps({"asset_type":"main_image","goal":"Test Goal","composition":"centered","background":"white","prompt":"A photo of freezer","platform":"Alibaba.com","status":"draft"}),
        white_bg_json=json.dumps({"asset_type":"white_bg","goal":"White bg goal","instructions":"Take photo","status":"draft","quality_checklist":["Q1","Q2"]}),
        scene_images_json=json.dumps([{"scene_name":"Supermarket","target_user":"buyer","scene_narrative":"In store","visual_elements":["shelf","product"],"product_position":"center","prompt":"Scene prompt"}]),
        selling_points_json=json.dumps([{"title":"Fast","description":"Fast cooling","visual_representation":"chart","icon_suggestion":"snowflake","layout_suggestion":"left-right"}]),
        video_scripts_json=json.dumps([{"video_goal":"traffic","duration_seconds":15,"storyboard":[{"shot_number":1,"duration":"0-3s","visual":"wide","subtitle":"Buy Now","voiceover":"Get it"}],"cta":"Shop","material_requirements":["photo"],"pacing":"fast"}]),
        ad_material_json=json.dumps({"ad_goal":"traffic","target_audience":"B2B","ad_angle":"quality","material_list":["photo"],"shot_sequence":["hook","cta"],"hook":"Buy!","key_selling_points":["fast"],"cta":"Buy","platform_suggestion":"Meta"}))
    s.add(plan)
    s.commit()
    yield s
    s.close()

class TestMarkdownExport:
    def test_export_contains_all_sections(self, db_session):
        """导出 Markdown 包含六类素材标题"""
        from app.services.markdown_exporter import export_to_markdown
        md = export_to_markdown(db_session, project_id=1)
        assert md is not None
        assert "## 主图方案" in md
        assert "## 白底图方案" in md
        assert "## 场景图方案" in md
        assert "## 卖点图模块" in md
        assert "## 短视频脚本" in md
        assert "## 广告素材方案" in md

    def test_export_contains_product_info(self, db_session):
        """导出包含具体产品数据"""
        from app.services.markdown_exporter import export_to_markdown
        md = export_to_markdown(db_session, project_id=1)
        assert "Test Goal" in md
        assert "Supermarket" in md
        assert "Fast" in md

    def test_export_nonexistent_returns_empty(self, db_session):
        """不存在的项目返回 None"""
        from app.services.markdown_exporter import export_to_markdown
        md = export_to_markdown(db_session, project_id=999)
        assert md is None
