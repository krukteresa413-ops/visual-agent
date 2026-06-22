"""Canvas API — asset grouping and modification endpoints."""
from typing import Dict, List


_ASSET_TYPE_LABELS: Dict[str, str] = {
    "main_image": "主图",
    "white_bg": "白底图",
    "scene_images": "场景图",
    "selling_points": "卖点",
    "video_scripts": "视频脚本",
    "ad_material": "广告素材",
    "layout_plan": "排版方案",
}


def group_assets_by_type(plan: dict) -> List[dict]:
    """Group assets from a VisualAsset plan by type for canvas display.

    Returns list of {name, assets} dicts, skipping None/empty groups.
    """
    if not plan:
        return []

    groups = []
    for key, label in _ASSET_TYPE_LABELS.items():
        value = plan.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            if len(value) == 0:
                continue
            assets = value
        else:
            assets = [value]

        groups.append({"name": label, "assets": assets, "type_key": key})

    return groups
