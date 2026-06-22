"""
Platform adapter implementation for multi-platform image specifications.
"""

PLATFORM_SPECS = {
    "taobao": {"width": 800, "height": 800, "format": "jpg"},
    "xiaohongshu": {"width": 1080, "height": 1440, "format": "jpg"},
    "douyin": {"width": 1080, "height": 1920, "format": "jpg"},
    "jd": {"width": 800, "height": 800, "format": "jpg"},
    "pinduoduo": {"width": 800, "height": 800, "format": "jpg"},
    "amazon": {"width": 2000, "height": 2000, "format": "png"},
    "alibaba": {"width": 1000, "height": 1000, "format": "jpg"},
    "shopify": {"width": 2048, "height": 2048, "format": "png"},
    "wechat": {"width": 1080, "height": 1080, "format": "jpg"},
    "meituan": {"width": 800, "height": 800, "format": "jpg"},
}


class PlatformAdapter:
    def __init__(self, platform):
        if platform not in PLATFORM_SPECS:
            raise ValueError(f"Unknown platform: {platform}")
        self.platform = platform

    def get_main_image_spec(self):
        return PLATFORM_SPECS[self.platform]

    def smart_crop(self, source_width, source_height, target_width, target_height, focal_x, focal_y):
        source_ratio = source_width / source_height
        target_ratio = target_width / target_height

        if source_ratio > target_ratio:
            crop_height = source_height
            crop_width = int(crop_height * target_ratio)
        else:
            crop_width = source_width
            crop_height = int(crop_width / target_ratio)

        x = max(0, min(focal_x - crop_width // 2, source_width - crop_width))
        y = max(0, min(focal_y - crop_height // 2, source_height - crop_height))

        return {"x": x, "y": y, "width": crop_width, "height": crop_height}

    @staticmethod
    def adapt_batch(source_width, source_height, platforms):
        return [{"platform": p} for p in platforms]
