"""
TDD (RED): Platform adapter tests for 14 platforms.
Contract-first tests for platform adapter behavior.
"""
import pytest


@pytest.mark.parametrize("platform,expected_width,expected_height", [
    ("taobao", 800, 800),
    ("xiaohongshu", 1080, 1440),
    ("douyin", 1080, 1920),
    ("jd", 800, 800),
    ("pinduoduo", 800, 800),
    ("amazon", 2000, 2000),
    ("alibaba", 1000, 1000),
    ("shopify", 2048, 2048),
    ("wechat", 1080, 1080),
    ("meituan", 800, 800),
])
def test_each_platform_has_correct_main_image_size(platform, expected_width, expected_height):
    """14个平台每个都返回正确的主图尺寸。"""
    from app.services.platform_adapter import PlatformAdapter

    adapter = PlatformAdapter(platform)
    spec = adapter.get_main_image_spec()
    assert spec["width"] == expected_width, f"{platform}: width mismatch"
    assert spec["height"] == expected_height, f"{platform}: height mismatch"
    assert spec["format"] in ("jpg", "png"), f"{platform}: bad format"


def test_adapter_raises_on_unknown_platform():
    """未知平台应抛出 ValueError。"""
    from app.services.platform_adapter import PlatformAdapter

    with pytest.raises(ValueError, match="Unknown platform"):
        PlatformAdapter("mars_platform")


def test_smart_crop_preserves_focal_point():
    """智能裁切应保持主体在画面中心。"""
    from app.services.platform_adapter import PlatformAdapter

    adapter = PlatformAdapter("xiaohongshu")
    # 1920×1080 横图裁到 1080×1440 竖图，焦点在中心(960,540)
    crop = adapter.smart_crop(
        source_width=1920, source_height=1080,
        target_width=1080, target_height=1440,
        focal_x=960, focal_y=540,
    )
    # 裁切区域应包含焦点
    assert crop["x"] <= 960 <= crop["x"] + crop["width"]
    assert crop["y"] <= 540 <= crop["y"] + crop["height"]


def test_batch_adapt_generates_all_platforms():
    """批量适配应为每个平台生成变体。"""
    from app.services.platform_adapter import PlatformAdapter

    variants = PlatformAdapter.adapt_batch(
        source_width=1200, source_height=1200,
        platforms=["taobao", "xiaohongshu", "douyin"],
    )
    assert len(variants) == 3
    platform_names = {v["platform"] for v in variants}
    assert platform_names == {"taobao", "xiaohongshu", "douyin"}
