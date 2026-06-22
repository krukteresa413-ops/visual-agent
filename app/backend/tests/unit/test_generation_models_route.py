from fastapi.testclient import TestClient

from main import app


def test_models_endpoint_returns_inventory_shape():
    response = TestClient(app).get("/api/v1/generation/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert data["models"]
    first = data["models"][0]
    for key in ["modelKey", "provider", "modality", "source", "productionUsable", "available"]:
        assert key in first


def test_modality_filter_image():
    response = TestClient(app).get("/api/v1/generation/models?modality=image")
    assert response.status_code == 200
    assert response.json()["models"]
    assert all(model["modality"] == "image" for model in response.json()["models"])


def test_modality_filter_video():
    response = TestClient(app).get("/api/v1/generation/models?modality=video")
    assert response.status_code == 200
    assert response.json()["models"]
    assert all(model["modality"] == "video" for model in response.json()["models"])


def test_benchmark_present_but_flagged():
    response = TestClient(app).get("/api/v1/generation/models")
    assert response.status_code == 200
    lovart = [model for model in response.json()["models"] if model["provider"].startswith("lovart")]
    assert lovart
    assert all(model["source"] == "benchmark" for model in lovart)
    assert all(model["productionUsable"] is False for model in lovart)
