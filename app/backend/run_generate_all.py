"""
Phase 2.1: Run generate_all with real DeepSeek API.
Uses the Commercial Chest Freezer from PRD Section 14.
"""
import asyncio
import json
import time
from app.services.visual_agent import VisualAgent

FREEZER_BRIEF = {
    "product_name": "Commercial Chest Freezer",
    "category": "Commercial Refrigeration",
    "specifications": ["300L", "stainless steel", "low noise", "R290 refrigerant"],
    "materials": ["stainless steel"],
    "selling_points": ["fast cooling", "energy saving", "OEM customization", "digital thermostat"],
    "target_market": ["US", "EU", "Middle East"],
    "target_customer": ["supermarket buyer", "restaurant owner", "distributor"],
    "usage_scenarios": ["supermarket", "restaurant", "convenience store", "cold storage"],
    "brand_style": "clean, professional, industrial",
    "compliance_notes": ["CE certified", "avoid unverifiable certification claims"],
}


async def main():
    agent = VisualAgent()
    start = time.time()

    print("Generating all 6 asset types...\n")
    result = await agent.generate_all(project_id=1, brief=FREEZER_BRIEF)

    elapsed = time.time() - start

    # Print each asset type
    assets = {
        "main_image": result.main_image,
        "white_bg": result.white_bg,
        "scene_images": result.scene_images,
        "selling_points": result.selling_points,
        "video_scripts": result.video_scripts,
        "ad_material": result.ad_material,
    }

    for name, asset in assets.items():
        print(f"\n{'='*60}")
        print(f"  {name}")
        print(f"{'='*60}")
        if isinstance(asset, list):
            for i, item in enumerate(asset):
                print(f"\n  [{i+1}]")
                d = item.model_dump()
                for k, v in d.items():
                    val = str(v)[:120]
                    print(f"    {k}: {val}")
        else:
            d = asset.model_dump()
            for k, v in d.items():
                val = str(v)[:120]
                print(f"    {k}: {val}")

    print(f"\n{'='*60}")
    print(f"  Generated {len(result.scene_images)} scenes, {len(result.selling_points)} selling points, {len(result.video_scripts)} scripts")
    print(f"  Time: {elapsed:.1f}s")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())
