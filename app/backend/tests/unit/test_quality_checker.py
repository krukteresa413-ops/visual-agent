"""
TDD Step 1 (RED): Quality Checker tests.
OCR text verification + brand color deviation + full quality report.
"""
import json
import pytest
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tempfile
import os


# ── Test image generators ─────────────────────────────────────

def make_text_image(text: str, size=(400, 100), bg_color=(255, 255, 255)) -> str:
    """Create a simple image with text rendered on it, return file path."""
    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)
    # Use default font (may not support Chinese, but OCR should still detect shapes)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except (OSError, IOError):
        font = ImageFont.load_default()
    draw.text((10, 30), text, fill=(0, 0, 0), font=font)
    path = os.path.join(tempfile.gettempdir(), "test_ocr.png")
    img.save(path)
    return path


def make_color_image(hex_colors: list, size=(200, 200)) -> str:
    """Create an image with specified colors as blocks, return file path."""
    img = Image.new("RGB", size, hex_colors[0] if hex_colors else "#FFFFFF")
    if len(hex_colors) > 1:
        draw = ImageDraw.Draw(img)
        block_h = size[1] // len(hex_colors)
        for i, color in enumerate(hex_colors):
            draw.rectangle([0, i * block_h, size[0], (i + 1) * block_h], fill=color)
    path = os.path.join(tempfile.gettempdir(), "test_color.png")
    img.save(path)
    return path


# ── OCR Tests ─────────────────────────────────────────────────

def test_ocr_extracts_english_text():
    """OCR 能从纯色背景图片中提取英文文字。"""
    from app.services.quality_checker import QualityChecker

    checker = QualityChecker()
    img_path = make_text_image("Hello World Test")
    result = checker.check_text_accuracy(img_path, ["Hello World Test"])

    assert result["passed"] is True
    assert result["ocr_text"] != ""
    assert result["match_count"] > 0
    os.unlink(img_path)


def test_ocr_detects_mismatch():
    """OCR 能检测到图片文字与预期文案不匹配。"""
    from app.services.quality_checker import QualityChecker

    checker = QualityChecker()
    img_path = make_text_image("Wrong Text Here")
    result = checker.check_text_accuracy(img_path, ["Expected Different Text"])

    # Should report mismatch
    assert result["match_count"] < len(result["expected_texts"])
    os.unlink(img_path)


def test_ocr_handles_empty_expected():
    """无预期文案时返回通过。"""
    from app.services.quality_checker import QualityChecker

    checker = QualityChecker()
    img_path = make_text_image("Anything")
    result = checker.check_text_accuracy(img_path, [])

    assert result["passed"] is True
    assert result["match_count"] == 0
    os.unlink(img_path)


# ── Brand Color Tests ─────────────────────────────────────────

def test_brand_color_within_tolerance_passes():
    """品牌色 ΔE 在容差范围内时通过。"""
    from app.services.quality_checker import QualityChecker

    checker = QualityChecker()
    # Create image with brand red
    img_path = make_color_image(["#E63946"])
    brand_colors = {"primary": "#E63946"}

    result = checker.check_brand_colors(img_path, brand_colors, tolerance=5.0)

    assert result["passed"] is True
    assert len(result["deviations"]) == 0
    os.unlink(img_path)


def test_brand_color_exceeds_tolerance_fails():
    """品牌色 ΔE 超出容差时报告偏差。"""
    from app.services.quality_checker import QualityChecker

    checker = QualityChecker()
    # Create image with wrong green instead of brand red
    img_path = make_color_image(["#2ECC71"])  # green — far from red
    brand_colors = {"primary": "#E63946"}      # brand red

    result = checker.check_brand_colors(img_path, brand_colors, tolerance=5.0)

    assert result["passed"] is False
    assert len(result["deviations"]) > 0
    os.unlink(img_path)


def test_brand_color_handles_empty_palette():
    """无品牌色板时跳过检测。"""
    from app.services.quality_checker import QualityChecker

    checker = QualityChecker()
    img_path = make_color_image(["#E63946"])
    result = checker.check_brand_colors(img_path, {})

    assert result["passed"] is True
    assert result.get("skipped") is True
    os.unlink(img_path)


# ── Full Quality Report Tests ─────────────────────────────────

def test_full_check_returns_comprehensive_report():
    """全检返回完整报告结构。"""
    from app.services.quality_checker import QualityChecker

    checker = QualityChecker()
    img_path = make_text_image("Hello World Test")

    expected_texts = ["Hello World Test"]
    brand_colors = {"primary": "#FFFFFF"}

    report = checker.run_full_check(img_path, expected_texts, brand_colors)

    assert "text_check" in report
    assert "color_check" in report
    assert "overall_passed" in report
    assert "summary" in report
    assert isinstance(report["overall_passed"], bool)
    os.unlink(img_path)
