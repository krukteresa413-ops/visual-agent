"""Agent 对话循环：用户消息 → 大脑决策 →（调工具 → 回灌）循环 → 最终回复。

无状态、无端点、无前端——纯后端核心，可独立脚本验证。
SSE 端点与前端接入是后续卡片。
"""
import json
from typing import Optional

from app.agents.conversation.brain import chat
from app.agents.conversation.tools import TOOL_SPECS, execute_tool

SYSTEM_PROMPT = (
    "你是电商视觉创作助手。用户用自然语言提需求时，"
    "判断是直接用文字回答，还是调用工具生成/修改图片。"
    "需要出图或改图时调用 generate_image。回答简洁、用中文。"
)

MAX_STEPS = 4


async def run_turn(user_message: str, reference_image_url: Optional[str] = None) -> dict:
    """跑一轮对话。返回 {reply, assets, tool_trace}。"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    content = user_message
    if reference_image_url:
        content += f"\n\n[当前选中图片] {reference_image_url}"
    messages.append({"role": "user", "content": content})

    assets: list[str] = []
    trace: list[dict] = []

    for _ in range(MAX_STEPS):
        msg = await chat(messages, tools=TOOL_SPECS, tool_choice="auto")
        tool_calls = msg.tool_calls or []

        if not tool_calls:
            return {"reply": msg.content or "", "assets": assets, "tool_trace": trace}

        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            }
        )

        for tc in tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            result = await execute_tool(tc.function.name, args)
            trace.append({"tool": tc.function.name, "args": args, "result": result})
            if isinstance(result, dict) and result.get("image_urls"):
                assets.extend(result["image_urls"])
                result = {"status": result.get("status"), "image_count": len(result.get("image_urls") or [])}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    return {"reply": "（已达最大步数上限）", "assets": assets, "tool_trace": trace}
