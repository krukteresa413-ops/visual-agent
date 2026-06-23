"""
TDD (RED): Unified exporter tests.
"""
import io, zipfile, pytest


def test_export_single_platform_creates_zip():
    """单平台导出应生成合法的 ZIP 文件。"""
    from app.services.unified_exporter import UnifiedExporter

    exporter = UnifiedExporter()
    zip_bytes = exporter.export(
        project_name="测试项目",
        assets={"main_image": [b"fake_jpg_data"] * 3},
        platforms=["taobao"],
    )
    assert len(zip_bytes) > 0
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    names = zf.namelist()
    assert any("主图" in n for n in names)
    assert any("上传说明" in n for n in names)


def test_export_multi_platform_includes_all():
    """多平台导出应包含所有平台的目录。"""
    from app.services.unified_exporter import UnifiedExporter

    exporter = UnifiedExporter()
    zip_bytes = exporter.export(
        project_name="测试",
        assets={"main_image": [b"x"]},
        platforms=["taobao", "xiaohongshu"],
    )
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    names = zf.namelist()
    assert any("淘宝" in n for n in names)
    assert any("小红书" in n for n in names)


def test_export_empty_assets_returns_valid_zip():
    """空资产导出应返回合法 ZIP（至少包含 README）。"""
    from app.services.unified_exporter import UnifiedExporter

    exporter = UnifiedExporter()
    zip_bytes = exporter.export(
        project_name="空项目",
        assets={},
        platforms=["taobao"],
    )
    assert len(zip_bytes) > 0
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    assert len(zf.namelist()) > 0
