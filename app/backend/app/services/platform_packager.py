"""Platform Packager — generates multi-platform size packages."""
from typing import List, Dict


PLATFORM_SPECS = {
    "taobao": {"size": "800x800", "formats": ["jpg", "png"]},
    "xiaohongshu": {"size": "1080x1440", "formats": ["jpg", "png"]},
    "douyin": {"size": "1080x1920", "formats": ["mp4", "jpg"]},
    "wechat": {"size": "800x800", "formats": ["jpg"]},
    "amazon": {"size": "2000x2000", "formats": ["jpg", "png"]},
}


class PlatformPackager:
    """Generate platform-specific asset packages."""

    def generate_manifest(
        self, assets: List[Dict], project_name: str
    ) -> Dict:
        """Generate package manifest with per-platform bundles."""
        # Group by platform
        groups = {}
        for asset in assets:
            platform = asset.get("platform", "other")
            if platform not in groups:
                groups[platform] = []
            groups[platform].append(asset)

        packages = []
        for platform, platform_assets in sorted(groups.items()):
            spec = PLATFORM_SPECS.get(platform, {"size": "auto", "formats": ["jpg"]})
            packages.append({
                "platform": platform,
                "size": spec["size"],
                "formats": spec["formats"],
                "assets": platform_assets,
                "count": len(platform_assets),
            })

        return {
            "project_name": project_name,
            "packages": packages,
        }
