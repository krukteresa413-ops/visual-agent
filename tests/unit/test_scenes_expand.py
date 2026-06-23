"""
TDD (RED): Scene template expansion — 10→20 templates.
"""
import pytest


def test_template_count_is_20_or_more():
    """场景模板应至少有20个。"""
    from app.services.platform_specs import INDUSTRY_SCENES
    assert len(INDUSTRY_SCENES) >= 20


def test_new_templates_have_required_fields():
    """每个模板应有 id, name, desc, platforms。"""
    from app.services.platform_specs import INDUSTRY_SCENES
    for scene in INDUSTRY_SCENES:
        assert "id" in scene
        assert "name" in scene
        assert "desc" in scene
        assert "platforms" in scene


@pytest.mark.parametrize("scene_id", [
    "food_beverage", "real_estate", "education",
    "automotive", "health_wellness", "pet_supplies",
    "sports_outdoor", "baby_maternal", "jewelry_accessories",
    "home_appliances",
])
def test_new_scenes_exist(scene_id):
    """新增场景应存在。"""
    from app.services.platform_specs import INDUSTRY_SCENES
    ids = {s["id"] for s in INDUSTRY_SCENES}
    assert scene_id in ids, f"Missing scene: {scene_id}"
