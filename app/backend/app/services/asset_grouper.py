"""Asset Grouper — groups assets by platform/type for canvas display."""
from typing import List, Dict


PLATFORM_SIZES = {
    "taobao": "800x800",
    "xiaohongshu": "1080x1440",
    "douyin": "1080x1920",
    "wechat": "800x800",
    "amazon": "2000x2000",
}


class AssetGrouper:
    """Group assets for canvas layout."""

    def group_by_platform(self, assets: List[Dict]) -> Dict[str, List[Dict]]:
        """Group assets by platform."""
        groups = {}
        for asset in assets:
            platform = asset.get("platform", "other")
            if platform not in groups:
                groups[platform] = []
            groups[platform].append(asset)
        return groups

    def group_by_type(self, assets: List[Dict]) -> Dict[str, List[Dict]]:
        """Group assets by type."""
        groups = {}
        for asset in assets:
            asset_type = asset.get("type", "other")
            if asset_type not in groups:
                groups[asset_type] = []
            groups[asset_type].append(asset)
        return groups

    def get_canvas_layout(self, assets: List[Dict]) -> Dict:
        """Get canvas layout with sections grouped by platform."""
        grouped = self.group_by_platform(assets)
        sections = []
        for platform, platform_assets in grouped.items():
            size = platform_assets[0].get("size", "") if platform_assets else ""
            sections.append({
                "title": f"{platform} 素材",
                "platform": platform,
                "size": size or PLATFORM_SIZES.get(platform, ""),
                "assets": platform_assets,
            })
        return {"sections": sections}

    def get_platform_sizes(self, assets: List[Dict]) -> Dict[str, str]:
        """Get platform size mapping from assets."""
        sizes = {}
        for asset in assets:
            platform = asset.get("platform", "")
            size = asset.get("size", "")
            if platform and size and platform not in sizes:
                sizes[platform] = size
        # Fill missing from defaults
        for platform, default_size in PLATFORM_SIZES.items():
            if platform not in sizes:
                # Only add if platform has assets
                pass
        return sizes

    def get_summary(self, assets: List[Dict]) -> Dict:
        """Get summary stats."""
        if not assets:
            return {"total_assets": 0, "platform_count": 0, "type_count": 0}
        platforms = set(a.get("platform", "") for a in assets if a.get("platform"))
        types = set(a.get("type", "") for a in assets if a.get("type"))
        return {
            "total_assets": len(assets),
            "platform_count": len(platforms),
            "type_count": len(types),
        }
