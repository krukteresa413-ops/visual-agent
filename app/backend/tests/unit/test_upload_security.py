from fastapi import HTTPException
from fastapi.testclient import TestClient


def test_safe_upload_path_rejects_path_traversal_values():
    from app.api.upload_routes import _safe_upload_path

    for filename in ["../main.py", "..", "nested/file.png", r"nested\\file.png", "bad$name.png"]:
        try:
            _safe_upload_path(filename)
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "invalid filename"
        else:
            raise AssertionError(f"expected invalid filename: {filename}")


def test_delete_image_keeps_safe_missing_filename_as_not_found():
    from main import app

    client = TestClient(app)
    resp = client.delete("/api/v1/upload/image/not-existing-safe-file.png")

    assert resp.status_code == 404
