"""
LLM调用客户端（向后兼容包装）。

委托给 app.services.llm_provider.llm_service。
旧代码无需改动即可使用。

安全增强 (2026-06-16):
- SafeLLMClient: 在现有 LLMClient 外层增加注入检测 + 防御提醒
- 旧 LLMClient 接口不变，新代码使用 SafeLLMClient
"""
from typing import Optional

from app.services.llm_provider import (
    LLMResponseError,
    llm_service,
)
from app.services.safety import (
    detect_injection,
    append_safety_reminder,
    SafetyViolation,
)

__all__ = ["LLMClient", "SafeLLMClient", "LLMResponseError", "SafetyViolation"]


class LLMClient:
    """
    对 LLMService 的向后兼容包装。

    自动使用第一个注册的 provider（当前为 DeepSeek）。
    """

    def __init__(self):
        self._provider = llm_service.get_active()
        if self._provider is None:
            raise RuntimeError("No LLM provider available. Check configuration.")
        self._client = self._provider._client  # backward compat for tests

    @property
    def client(self):
        """Public accessor for backward-compatible test access."""
        return self._client

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model_override: Optional[str] = None,
    ) -> dict:
        return await self._provider.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model_override=model_override,
        )

    def get_usage_stats(self):
        return self._provider.get_usage_stats()

    def reset_usage_stats(self):
        self._provider.reset_usage_stats()


class SafeLLMClient:
    """安全 LLM 客户端 — 在 LLMClient 外层增加防护。

    防护层次：
    1. Pre-call: 对 user_prompt 做注入模式检测，拒绝可疑输入
    2. Mid-call: 在 user_prompt 末尾追加防御提醒（defense-in-depth）
    3. Post-call: 委托给底层 LLMClient 执行实际调用

    用法：
        client = SafeLLMClient()           # 安全模式
        client = SafeLLMClient(unsafe=True) # 跳过检查（调试用）
    """

    def __init__(self, unsafe: bool = False):
        self._inner = LLMClient()
        self._unsafe = unsafe

    @property
    def client(self):
        """Proxy to inner LLMClient's client for backward compat."""
        return self._inner.client

    @property
    def _model(self):
        """Proxy to inner provider's model for usage tracking."""
        return self._inner._provider._model

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model_override: Optional[str] = None,
    ) -> dict:
        """调用 LLM，带注入检测和防御提醒。

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数
            max_tokens: 最大 token 数
            model_override: 模型覆盖

        Returns:
            LLM 返回的 JSON dict

        Raises:
            SafetyViolation: 检测到注入尝试
        """
        if not self._unsafe:
            # Pre-call: check user_prompt for injection patterns
            injection = detect_injection(user_prompt, "llm_call user_prompt")
            if injection:
                raise SafetyViolation(injection)

            # Mid-call: append safety reminder (defense-in-depth)
            user_prompt = append_safety_reminder(user_prompt)

        # Post-call: delegate to inner client
        return await self._inner.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model_override=model_override,
        )

    def get_usage_stats(self):
        return self._inner.get_usage_stats()

    def reset_usage_stats(self):
        self._inner.reset_usage_stats()
