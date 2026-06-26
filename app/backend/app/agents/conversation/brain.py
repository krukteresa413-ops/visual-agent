"""Agent 对话通道：chat.completions + tools。

与现有 app.services.llm_provider.LLMProvider.call() 完全独立——
那条是单次 JSON 生成器，本模块是带工具调用的对话通道，互不影响。
凭据复用现有 OPENAI_API_KEY + zydmx 中继（已验证支持 chat.completions + function calling）。
"""
import os

from openai import AsyncOpenAI


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        base_url=os.getenv("Zydmx_BASE_URL", "https://zydmx.com/v1"),
        timeout=float(os.getenv("LLM_TIMEOUT", "120")),
    )


def _model() -> str:
    return os.getenv("Zydmx_MODEL", "gpt-5.5")


async def chat(messages, tools=None, tool_choice="auto"):
    """单次 chat.completions 调用，返回原始 message 对象（含 content / tool_calls）。"""
    kwargs = {"model": _model(), "messages": messages, "max_tokens": 1024}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice
    resp = await _client().chat.completions.create(**kwargs)
    return resp.choices[0].message
