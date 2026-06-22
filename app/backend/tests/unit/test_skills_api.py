"""RED test for skills API endpoint (P2-12)."""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.skills_routes import router as skills_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(skills_router)
    return TestClient(app)


class TestSkillsAPI:
    def test_get_skills_returns_list(self, client):
        resp = client.get("/api/v1/skills")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_skills_have_required_fields(self, client):
        resp = client.get("/api/v1/skills")
        data = resp.json()
        for skill in data:
            assert "id" in skill
            assert "title" in skill
            assert "description" in skill
            assert "category" in skill
            assert "prompt" in skill
            assert "enabled" in skill

    def test_only_enabled_skills_returned(self, client):
        resp = client.get("/api/v1/skills")
        data = resp.json()
        for skill in data:
            assert skill["enabled"] is True, f"Skill {skill['id']} should be enabled"

    def test_skills_can_be_filtered_by_category(self, client):
        resp = client.get("/api/v1/skills?category=Video")
        assert resp.status_code == 200
        data = resp.json()
        for skill in data:
            assert skill["category"] == "Video"

    def test_categories_list_available(self, client):
        resp = client.get("/api/v1/skills/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert "Video" in data

    def test_get_single_skill(self, client):
        resp = client.get("/api/v1/skills")
        skills = resp.json()
        if skills:
            skill_id = skills[0]["id"]
            resp2 = client.get(f"/api/v1/skills/{skill_id}")
            assert resp2.status_code == 200
            assert resp2.json()["id"] == skill_id

    def test_disabled_skill_not_in_list(self, client):
        resp = client.get("/api/v1/skills")
        data = resp.json()
        ids = [s["id"] for s in data]
        # "create" skill is disabled in config
        assert "create" not in ids

    def test_disabled_skill_returns_404_individually(self, client):
        # "create" skill exists but is disabled
        resp = client.get("/api/v1/skills/create")
        assert resp.status_code == 404
