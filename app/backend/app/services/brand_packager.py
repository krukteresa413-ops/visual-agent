"""Brand Packager — exports brand asset package for reuse."""
from typing import List, Dict


class BrandPackager:
    """Package brand assets for long-term reuse."""

    def generate_manifest(
        self, brand: Dict, assets: List[Dict], project_name: str
    ) -> Dict:
        """Generate brand package manifest."""
        # Only include non-empty brand assets
        brand_assets = []
        logo = brand.get("logo_url", "")
        if logo:
            brand_assets.append({"type": "logo", "url": logo})
        colors = brand.get("colors", [])
        if colors:
            brand_assets.append({"type": "colors", "values": colors})
        fonts = brand.get("fonts", [])
        if fonts:
            brand_assets.append({"type": "fonts", "values": fonts})

        return {
            "brand_name": brand.get("name", ""),
            "project_name": project_name,
            "brand_assets": brand_assets,
            "brand_guidelines": {
                "colors": brand.get("colors", []),
                "fonts": brand.get("fonts", []),
                "keywords": brand.get("keywords", []),
                "tone": brand.get("tone", ""),
            },
            "restrictions": {
                "forbidden_styles": brand.get("forbidden_styles", []),
            },
            "project_assets": assets,
        }
