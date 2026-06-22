"""
TDD Step 1 (RED): Aesthetic Ranker tests.
Technical quality (MUSIQ) + pairwise comparison + ranking.
"""
import pytest
from PIL import Image
import tempfile
import os


# ── Helpers ────────────────────────────────────────────────────

def make_test_image(color="#4488CC", size=(256, 256)) -> str:
    """Create a simple test image with unique filename."""
    import uuid
    img = Image.new("RGB", size, color)
    path = os.path.join(tempfile.gettempdir(), f"test_rank_{uuid.uuid4().hex[:8]}.png")
    img.save(path)
    return path


SAMPLE_BRIEF = {
    "product_name": "女性轻量跑鞋",
    "brand_style": "清新、温柔、女性化",
    "target_audience": "25-35岁女性",
    "selling_points": ["极致轻量", "柔软回弹", "透气网面"],
}


# ── Technical Quality Tests ────────────────────────────────────

def test_technical_quality_returns_score():
    """MUSIQ 技术质量评分返回 0-100 分数。"""
    from app.services.aesthetic_ranker import AestheticRanker

    ranker = AestheticRanker()
    img_path = make_test_image()
    result = ranker.technical_quality(img_path)

    assert "score" in result
    assert 0 <= result["score"] <= 100
    assert result["metric"] == "MUSIQ"
    os.unlink(img_path)


def test_technical_quality_handles_invalid_image():
    """无效图片返回错误但不崩。"""
    from app.services.aesthetic_ranker import AestheticRanker

    ranker = AestheticRanker()
    result = ranker.technical_quality("/nonexistent/path.png")

    assert "score" in result
    assert "error" in result


# ── Comparison Tests ───────────────────────────────────────────

def test_compare_pair_returns_winner():
    """两两比较返回 winner 和 reasoning。"""
    from app.services.aesthetic_ranker import AestheticRanker

    ranker = AestheticRanker()
    img_a = make_test_image("#FF69B4")  # pink - matches brief
    img_b = make_test_image("#333333")  # dark - doesn't match

    result = ranker.compare_pair(img_a, img_b, SAMPLE_BRIEF)

    assert "winner" in result
    assert result["winner"] in ("A", "B", "tie")
    assert "reasoning" in result
    assert "scores" in result
    os.unlink(img_a)
    os.unlink(img_b)


def test_compare_pair_without_brief():
    """无 brief 时用纯技术质量比较。"""
    from app.services.aesthetic_ranker import AestheticRanker

    ranker = AestheticRanker()
    img_a = make_test_image("#E63946")
    img_b = make_test_image("#457B9D")

    result = ranker.compare_pair(img_a, img_b, {})

    assert "winner" in result
    assert "reasoning" in result
    os.unlink(img_a)
    os.unlink(img_b)


# ── Ranking Tests ──────────────────────────────────────────────

def test_rank_images_orders_by_score():
    """多图排序按分数降序。"""
    from app.services.aesthetic_ranker import AestheticRanker

    ranker = AestheticRanker()
    paths = [make_test_image(c) for c in ["#FF69B4", "#FFB6C1", "#C71585"]]

    result = ranker.rank_images(paths, SAMPLE_BRIEF)

    assert "rankings" in result
    assert len(result["rankings"]) == 3
    # First should have highest score
    scores = [r["score"] for r in result["rankings"]]
    assert scores == sorted(scores, reverse=True)
    for p in paths:
        os.unlink(p)


def test_rank_images_single_image():
    """单张图片也能排序。"""
    from app.services.aesthetic_ranker import AestheticRanker

    ranker = AestheticRanker()
    img_path = make_test_image()

    result = ranker.rank_images([img_path], SAMPLE_BRIEF)

    assert len(result["rankings"]) == 1
    assert result["rankings"][0]["rank"] == 1
    os.unlink(img_path)
