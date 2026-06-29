"""对话 Agent 必须保证以图生图(需求二):有参考图时强制传给 generate_image,
不依赖大脑(LLM)自觉。"""
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.conversation import agent as ag


class _Fn:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _ToolCall:
    def __init__(self, id, name, arguments):
        self.id = id
        self.function = _Fn(name, arguments)


class _Msg:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


@pytest.mark.asyncio
async def test_reference_image_injected_when_llm_omits_it():
    captured = {}

    async def fake_execute(name, args):
        captured["name"] = name
        captured["args"] = dict(args)
        return {"status": "succeeded", "image_urls": ["/uploads/generated/out.png"]}

    # 第一轮:大脑调 generate_image 但漏传 reference_image_url;第二轮:收尾不再调工具
    msg1 = _Msg(tool_calls=[_ToolCall("c1", "generate_image", '{"prompt":"改成夜景氛围"}')])
    msg2 = _Msg(content="已按夜景调整完成", tool_calls=[])

    with patch.object(ag, "chat", new=AsyncMock(side_effect=[msg1, msg2])), \
         patch.object(ag, "execute_tool", new=fake_execute):
        result = await ag.run_turn("把这张图改成夜景", reference_image_url="/uploads/src.png")

    assert captured["name"] == "generate_image"
    # 关键:漏传的参考图被强制补上
    assert captured["args"]["reference_image_url"] == "/uploads/src.png"
    assert result["assets"] == ["/uploads/generated/out.png"]


@pytest.mark.asyncio
async def test_explicit_reference_from_llm_is_preserved():
    captured = {}

    async def fake_execute(name, args):
        captured["args"] = dict(args)
        return {"status": "succeeded", "image_urls": ["/uploads/generated/out.png"]}

    msg1 = _Msg(tool_calls=[_ToolCall(
        "c1", "generate_image",
        '{"prompt":"换背景","reference_image_url":"/uploads/explicit.png"}',
    )])
    msg2 = _Msg(content="完成", tool_calls=[])

    with patch.object(ag, "chat", new=AsyncMock(side_effect=[msg1, msg2])), \
         patch.object(ag, "execute_tool", new=fake_execute):
        await ag.run_turn("换个背景", reference_image_url="/uploads/canvas.png")

    # 大脑已显式指定的参考图不被覆盖
    assert captured["args"]["reference_image_url"] == "/uploads/explicit.png"
