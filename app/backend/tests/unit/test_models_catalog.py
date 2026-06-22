from fastapi.testclient import TestClient

from main import app


def test_models_catalog_returns_curated_image_and_video_models():
    response = TestClient(app).get("/api/v1/models/catalog")
    assert response.status_code == 200
    data = response.json()
    assert "image" in data
    assert "video" in data
    assert any(model["id"] == "gpt-image-2" for model in data["image"])
    video_ids = [model["id"] for model in data["video"]]
    assert "doubao-seedance-1-5-pro-251215" in video_ids
    assert "kling-v2-6" in video_ids
    assert "kling-v3" in video_ids
    assert "kling-v2-5-turbo" in video_ids
    assert "viduq3-pro" in video_ids
    assert "MiniMax-Hailuo-2.3" not in video_ids
    first_image = data["image"][0]
    assert {"id", "name", "category", "format", "params", "tags", "enabled"} <= set(first_image)


def test_models_catalog_only_exposes_enabled_models():
    data = TestClient(app).get("/api/v1/models/catalog").json()
    assert all(model["enabled"] is True for model in data["image"])
    assert all(model["enabled"] is True for model in data["video"])
