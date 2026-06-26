"""Agent 工具层：把现有生成服务包成可被大脑调用的工具。

设计：纯增量。只 import 现有服务，不修改它们。
新增工具时在 TOOL_SPECS + TOOL_EXECUTORS 各加一条即可。
"""
import os

from app.models.image_generation_model import ImageGenerationRequest
from app.services.image_generation_service import image_generation_service

# 给大脑看的工具说明书（JSON Schema）
TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "根据文字描述生成一张商业图片；可选传参考图 URL 实现以图生图（在原图基础上改图）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "图片内容的详细描述"},
                    "reference_image_url": {
                        "type": "string",
                        "description": "可选；参考图 URL，用于在其基础上改图",
                    },
                    "width": {"type": "integer", "description": "宽度像素，默认 1024"},
                    "height": {"type": "integer", "description": "高度像素，默认 1024"},
                },
                "required": ["prompt"],
            },
        },
    },
]


def _image_provider() -> str:
    # 生产默认 dataeyes；探针可设 AGENT_IMAGE_PROVIDER=local 零成本测回路
    return os.getenv("AGENT_IMAGE_PROVIDER", "dataeyes")


async def _generate_image(args: dict) -> dict:
    req = ImageGenerationRequest(
        provider=_image_provider(),
        prompt=args["prompt"],
        width=int(args.get("width") or 1024),
        height=int(args.get("height") or 1024),
        reference_image_url=args.get("reference_image_url"),
    )
    result = await image_generation_service.generate(req)
    return {
        "status": result.status,
        "image_urls": [img.url for img in result.images],
    }


TOOL_EXECUTORS = {
    "generate_image": _generate_image,
}


async def execute_tool(name: str, args: dict) -> dict:
    fn = TOOL_EXECUTORS.get(name)
    if fn is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return await fn(args)
    except Exception as exc:  # 工具失败 → 回灌错误给大脑，让它决定下一步
        return {"error": f"{type(exc).__name__}: {exc}"}
