"""TDD: Taobao adapter tests (RED)."""
import pytest


def test_main_image_spec_is_800x800_jpg():
    """淘宝主图必须 800×800 JPG。"""
    from app.services.taobao_adapter import get_main_image_spec
    spec = get_main_image_spec()
    assert spec["width"] == 800
    assert spec["height"] == 800
    assert spec["format"] == "jpg"


def test_detail_page_width_is_750():
    """淘宝详情页宽度 750px。"""
    from app.services.taobao_adapter import get_detail_page_spec
    spec = get_detail_page_spec()
    assert spec["width"] == 750
    assert spec["format"] == "jpg"


def test_export_directory_structure():
    """导出目录结构包含主图/详情页/说明文件。"""
    from app.services.taobao_adapter import get_export_structure

    structure = get_export_structure(
        project_name="测试项目",
        main_images=["img1.jpg", "img2.jpg"],
        detail_pages=["detail.jpg"],
    )

    assert "测试项目_淘宝" in structure["root_dir"]
    entries = [e["path"] for e in structure["entries"]]
    assert "测试项目_淘宝/主图/主图_1.jpg" in entries
    assert "测试项目_淘宝/详情页/详情页_1.jpg" in entries
    assert "测试项目_淘宝/上传说明.txt" in entries


def test_upload_readme_contains_taobao_rules():
    """上传说明包含淘宝规格要求。"""
    from app.services.taobao_adapter import generate_upload_readme

    readme = generate_upload_readme("taobao", main_count=5, detail_count=1)
    assert "800 × 800" in readme
    assert "JPG" in readme
    assert "主图" in readme
