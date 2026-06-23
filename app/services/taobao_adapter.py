"""Taobao export adapter — specs, structure, and readme generation."""
import io
import zipfile
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# ── Specs ───────────────────────────────────────────────────

PLATFORM_SPECS: Dict[str, dict] = {
    "taobao": {
        "main_image": {"width": 800, "height": 800, "format": "jpg", "max_size_mb": 3},
        "detail_page": {"width": 750, "format": "jpg"},
        "white_bg_required_for_first": True,
    },
}


def get_main_image_spec(platform: str = "taobao") -> dict:
    """Return main image dimension spec for a platform."""
    return dict(PLATFORM_SPECS.get(platform, PLATFORM_SPECS["taobao"])["main_image"])


def get_detail_page_spec(platform: str = "taobao") -> dict:
    """Return detail page dimension spec for a platform."""
    return dict(PLATFORM_SPECS.get(platform, PLATFORM_SPECS["taobao"])["detail_page"])


# ── Directory Structure ─────────────────────────────────────

def get_export_structure(
    project_name: str,
    main_images: List[str],
    detail_pages: List[str],
    platform: str = "taobao",
) -> dict:
    """Build the export ZIP directory structure."""
    if platform == "taobao":
        root = f"{project_name}_淘宝"
    entries = []

    for i, img in enumerate(main_images, 1):
        entries.append({"path": f"{root}/主图/主图_{i}.jpg", "source": img})

    for i, page in enumerate(detail_pages, 1):
        entries.append({"path": f"{root}/详情页/详情页_{i}.jpg", "source": page})

    entries.append({"path": f"{root}/上传说明.txt", "source": "__README__"})

    return {"root_dir": root, "entries": entries}


# ── Upload Readme ───────────────────────────────────────────

def generate_upload_readme(
    platform: str = "taobao",
    main_count: int = 5,
    detail_count: int = 1,
) -> str:
    """Generate a platform-specific upload instruction file."""
    if platform == "taobao":
        return f"""淘宝商品上传说明
==================

主图要求（{main_count}张）：
  - 尺寸：800 × 800 像素
  - 格式：JPG
  - 大小：每张不超过 3MB
  - 第1张建议为纯白底图
  - 第5张建议为白底图（天猫要求）

详情页要求（{detail_count}张）：
  - 宽度：750 像素
  - 格式：JPG
  - 高度不限（建议不超过 25000 像素）

上传步骤：
  1. 登录千牛卖家中心
  2. 进入"商品管理" → "发布商品"
  3. 在"商品图片"区域上传主图
  4. 在"商品描述"区域上传详情页

注意事项：
  - 主图不要出现"淘宝同款""最低价"等极限词
  - 主图不要出现其他平台水印
  - 图片背景简洁，突出商品主体
"""
    return f"{platform} 平台上传说明\n尺寸和格式请参考平台最新规范。"


# ── ZIP Packaging ───────────────────────────────────────────

def create_export_zip(
    project_name: str,
    main_images: List[bytes],
    detail_pages: List[bytes],
    platform: str = "taobao",
) -> bytes:
    """Package images into a platform-compliant ZIP file.

    Args:
        project_name: Name for the root directory and filenames.
        main_images: List of raw image bytes for main images.
        detail_pages: List of raw image bytes for detail pages.
        platform: Target platform name.

    Returns:
        Raw ZIP file bytes.
    """
    structure = get_export_structure(
        project_name=project_name,
        main_images=[f"main_{i}" for i in range(len(main_images))],
        detail_pages=[f"detail_{i}" for i in range(len(detail_pages))],
        platform=platform,
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry, img_bytes in zip(structure["entries"], main_images + detail_pages + [None]):
            if entry["source"] == "__README__":
                readme = generate_upload_readme(
                    platform, len(main_images), len(detail_pages)
                )
                zf.writestr(entry["path"], readme.encode("utf-8"))
            elif img_bytes is not None:
                zf.writestr(entry["path"], img_bytes)

    buf.seek(0)
    return buf.read()
