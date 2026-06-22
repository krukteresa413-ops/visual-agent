from fastapi import HTTPException


def test_video_edit_safe_filename_rejects_path_traversal_values():
    from app.api.video_edit_routes import _safe_video_edit_filename

    for filename in ["../main.py", "..", "nested/file.mp4", r"nested\file.mp4", "bad$name.mp4", ""]:
        try:
            _safe_video_edit_filename(filename)
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "invalid filename"
        else:
            raise AssertionError(f"expected invalid filename: {filename}")


def test_video_edit_safe_filename_allows_simple_media_names():
    from app.api.video_edit_routes import _safe_video_edit_filename

    assert _safe_video_edit_filename("shoe_video-01.mp4") == "shoe_video-01.mp4"
