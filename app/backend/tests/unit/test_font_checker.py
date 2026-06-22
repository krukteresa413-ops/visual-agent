"""
TDD (RED): Font license checker tests.
"""
import pytest


def test_check_font_license_returns_status():
    """检查字体应返回授权状态。"""
    from app.services.font_checker import FontLicenseChecker

    checker = FontLicenseChecker()
    result = checker.check("SimSun")
    assert "status" in result
    assert result["status"] in ("free", "licensed", "unknown", "restricted")


def test_common_chinese_fonts_are_known():
    """常见中文字体应有明确授权状态。"""
    from app.services.font_checker import FontLicenseChecker

    checker = FontLicenseChecker()
    # 思源黑体 — 开源免费
    r1 = checker.check("Source Han Sans")
    assert r1["status"] == "free"

    # 微软雅黑 — 商业需授权
    r2 = checker.check("Microsoft YaHei")
    assert r2["status"] == "restricted"


def test_check_unknown_font_returns_unknown():
    """未知字体返回 unknown 状态。"""
    from app.services.font_checker import FontLicenseChecker

    checker = FontLicenseChecker()
    result = checker.check("SomeRandomFont2026")
    assert result["status"] == "unknown"


def test_validate_asset_fonts_returns_warnings():
    """校验资产字体应返回警告列表。"""
    from app.services.font_checker import FontLicenseChecker

    checker = FontLicenseChecker()
    warnings = checker.validate_asset_fonts(
        fonts_used=["Microsoft YaHei", "Source Han Sans", "Arial"]
    )
    assert len(warnings) >= 1
    assert any("Microsoft YaHei" in w for w in warnings)
