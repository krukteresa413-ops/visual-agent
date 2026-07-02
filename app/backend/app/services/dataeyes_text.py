"""DataEyes 文字-LLM 基座（唯一稳定可用的文字通道）。

第一性原理：MOYAG 后端 llm_provider 注册的 Zydmx / DeepSeek 当前均已失效
（余额不足 / 网关挂），因此 `LLMClient` 及基于它的旧链路一律返回空 → 静默降级。
唯一活着的文字 LLM 是 DataEyes（gpt-4o），走 vision_service 的 `/responses`
端点；`vision_service.analyze(images=[], prompt=...)` 在空图列表时即纯文字调用
（已在 /vision/brief-suggest-text 生产验证）。

本模块把该通道封成统一入口，供编排 Agent 与质量评审复用，让 LLM 推理真正落在
活着的通道上。所有失败都收敛为空返回（str "" / dict {}），调用方据此降级为模板。
"""
from __future__ import annotations

import asyncio
import json
import logging
import re

logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict:
    """从 LLM 文本里稳健抽取一个 JSON 对象。

    依次处理：```json 代码块围栏 → 直接 json.loads → 抓第一个平衡的 {...}。
    全部失败或非对象则返回 {}。
    """
    if not text:
        return {}
    t = text.strip()
    # 去掉 ```json ... ``` / ``` ... ``` 围栏
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z0-9]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t).strip()
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else {}
    except Exception:  # noqa: BLE001
        pass
    # 退路：抓第一个平衡的 {...}（容忍前后夹带解释文字）
    start = t.find("{")
    if start == -1:
        return {}
    depth = 0
    for i in range(start, len(t)):
        c = t[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(t[start:i + 1])
                    return obj if isinstance(obj, dict) else {}
                except Exception:  # noqa: BLE001
                    return {}
    return {}


async def dataeyes_text(
    prompt: str,
    *,
    max_tokens: int = 512,
    temperature: float = 0.7,
    per_try_timeout: float = 30.0,
) -> str:
    """走 DataEyes（唯一可用文字通道）返回纯文本；任何失败返回 ""。"""
    from app.services.vision_service import vision_service
    try:
        r = await asyncio.wait_for(
            vision_service.analyze(
                images=[],
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            ),
            timeout=per_try_timeout,
        )
    except Exception as e:  # noqa: BLE001 — 超时/网络/取消都视为不可用
        logger.warning("dataeyes_text unavailable: %s", e)
        return ""
    if not isinstance(r, dict) or not r.get("success"):
        return ""
    return r.get("content") or ""


async def dataeyes_json(
    system: str,
    user: str,
    *,
    max_tokens: int = 512,
    temperature: float = 0.7,
    per_try_timeout: float = 30.0,
) -> dict:
    """走 DataEyes 出 JSON dict；失败返回 {}（调用方据此降级为模板）。"""
    prompt = f"{system}\n\n{user}\n\n只输出 JSON，不要任何解释文字或代码块围栏。"
    text = await dataeyes_text(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        per_try_timeout=per_try_timeout,
    )
    return extract_json(text)
