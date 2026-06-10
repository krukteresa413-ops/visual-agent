"""
LLM调用客户端（向后兼容包装）。

委托给 app.services.llm_provider.llm_service。
旧代码无需改动即可使用。
"""
from typing import Optional

from app.services.llm_provider import (
    LLMResponseError,
    llm_service,
)

__all__ = ["LLMClient", "LLMResponseError"]


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
