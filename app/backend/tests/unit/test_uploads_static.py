from pathlib import Path
from fastapi.testclient import TestClient


def test_generated_uploads_are_served_by_api():
    from main import app

    generated = Path("/opt/visual-agent/uploads/generated")
    generated.mkdir(parents=True, exist_ok=True)
    sample = generated / "static-smoke.txt"
    sample.write_text("ok", encoding="utf-8")

    resp = TestClient(app).get("/uploads/generated/static-smoke.txt")

    assert resp.status_code == 200
    assert resp.text == "ok"
