"""
Unified exporter for multi-platform asset packaging.
"""
import io
import zipfile
from typing import Dict, List


class UnifiedExporter:
    """Exports project assets to a multi-platform ZIP structure."""

    PLATFORM_NAMES = {
        "taobao": "淘宝",
        "xiaohongshu": "小红书",
    }

    ASSET_TYPE_NAMES = {
        "main_image": "主图",
        "detail_page": "详情页",
    }

    def export(
        self,
        project_name: str,
        assets: Dict[str, List[bytes]],
        platforms: List[str],
    ) -> bytes:
        """
        Export assets to a ZIP file with platform-specific structure.

        Args:
            project_name: Project name for the ZIP root folder
            assets: Dict mapping asset types to lists of image bytes
            platforms: List of platform identifiers

        Returns:
            ZIP file as bytes
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for platform in platforms:
                platform_name = self.PLATFORM_NAMES.get(platform, platform)
                platform_dir = f"{project_name}/{platform_name}/"

                # Write assets
                for asset_type, images in assets.items():
                    asset_name = self.ASSET_TYPE_NAMES.get(asset_type, asset_type)
                    for idx, img_bytes in enumerate(images, 1):
                        filename = f"{platform_dir}{asset_name}/{asset_name}{idx}.jpg"
                        zf.writestr(filename, img_bytes)

                # Write upload instructions
                readme_path = f"{platform_dir}上传说明.txt"
                zf.writestr(readme_path, f"{platform_name}平台上传说明\n")

        return zip_buffer.getvalue()
