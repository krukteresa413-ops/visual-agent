"""
LLM Provider abstraction — registry pattern, swappable backends.

Replaces the monolithic LLMClient with a provider registry, enabling:
- Multiple LLM backends (DeepSeek, OpenAI-compatible providers, local models)
- Runtime provider switching
- Provider-level usage tracking
- Future: load balancing, fallback chains, A/B testing
"""
import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LLMResponseError(Exception):
    """模型返回的内容无法解析为有效JSON"""

# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------

import asyncio
import time

RETRYABLE_ERRORS = (
    asyncio.TimeoutError,
    ConnectionError,
    TimeoutError,
    OSError,
)


def _is_retryable(error: Exception) -> bool:
    """Determine if an error is transient and worth retrying."""
    status = getattr(error, "status_code", None)
    if status is not None:
        return status == 429 or status >= 500

    if isinstance(error, LLMResponseError):
        return False

    if isinstance(error, RETRYABLE_ERRORS):
        return True

    cause = error.__cause__
    while cause is not None:
        if isinstance(cause, RETRYABLE_ERRORS):
            return True
        cause = cause.__cause__

    return False


async def retry_with_backoff(
    fn,
    max_retries: int = 3,
    base_delay: float = 2.0,
):
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except Exception as e:
            last_error = e
            if attempt == max_retries or not _is_retryable(e):
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)

    raise last_error  # pragma: no cover


# ---------------------------------------------------------------------------
# Provider descriptor
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LLMProviderDescriptor:
    name: str
    display_name: str
    base_url: str
    default_model: str
    context_length: int = 128000


# ---------------------------------------------------------------------------
# Abstract provider
# ---------------------------------------------------------------------------


class LLMProvider(ABC):
    descriptor: LLMProviderDescriptor

    def __init__(self):
        self._usage = {"total_calls": 0, "total_prompt_tokens": 0, "total_completion_tokens": 0}

    @abstractmethod
    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model_override: Optional[str] = None,
    ) -> dict:
        raise NotImplementedError

    def get_usage_stats(self) -> dict:
        prompt_cost = self._usage["total_prompt_tokens"] / 1_000_000 * 1.0
        completion_cost = self._usage["total_completion_tokens"] / 1_000_000 * 2.0
        return {
            **self._usage,
            "estimated_cost_usd": round(prompt_cost + completion_cost, 6),
        }

    def reset_usage_stats(self) -> None:
        self._usage = {"total_calls": 0, "total_prompt_tokens": 0, "total_completion_tokens": 0}

    def _record_usage(self, response) -> None:
        self._usage["total_calls"] += 1
        try:
            usage = response.usage
            prompt_tokens = getattr(usage, "prompt_tokens", None)
            completion_tokens = getattr(usage, "completion_tokens", None)
            if prompt_tokens is None:
                prompt_tokens = getattr(usage, "input_tokens", 0)
            if completion_tokens is None:
                completion_tokens = getattr(usage, "output_tokens", 0)
            self._usage["total_prompt_tokens"] += prompt_tokens or 0
            self._usage["total_completion_tokens"] += completion_tokens or 0
        except Exception:
            pass

    @staticmethod
    def _extract_response_text(response) -> str:
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        output = getattr(response, "output", None)
        if output is None and isinstance(response, dict):
            output = response.get("output")
        for item in output or []:
            content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
            for part in content or []:
                part_type = part.get("type") if isinstance(part, dict) else getattr(part, "type", None)
                text = part.get("text") if isinstance(part, dict) else getattr(part, "text", None)
                if part_type in {"output_text", "text"} and isinstance(text, str) and text.strip():
                    return text.strip()

        if hasattr(response, "model_dump"):
            try:
                return LLMProvider._extract_response_text(response.model_dump())
            except Exception:
                pass
        return ""

    def _responses_kwargs(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> dict:
        kwargs = {
            "model": model,
            "instructions": system_prompt,
            "input": [{"role": "user", "content": user_prompt}],
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "store": False,
        }
        cache_key = os.getenv("LLM_PROMPT_CACHE_KEY", "visual-agent-main").strip()
        if cache_key:
            kwargs["prompt_cache_key"] = cache_key
        cache_retention = os.getenv("LLM_PROMPT_CACHE_RETENTION", "").strip()
        if cache_retention:
            kwargs["prompt_cache_retention"] = cache_retention
        return kwargs

    @staticmethod
    def _parse_json(raw: str) -> dict:
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise LLMResponseError(
                f"模型返回内容无法解析为JSON。\n原始内容前200字符: {raw[:200]}\n错误: {e}"
            )


# ---------------------------------------------------------------------------
# DeepSeek provider
# ---------------------------------------------------------------------------


class DeepSeekProvider(LLMProvider):
    descriptor = LLMProviderDescriptor(
        name="deepseek",
        display_name="DeepSeek",
        base_url="https://api.deepseek.com",
        default_model="deepseek-v4-pro",
        context_length=1_000_000,
    )

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        super().__init__()
        self._model = model or os.getenv("DEEPSEEK_MODEL", self.descriptor.default_model)
        self._max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
        self._timeout = float(os.getenv("LLM_TIMEOUT", "120"))

        self._client = AsyncOpenAI(
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=base_url or os.getenv("DEEPSEEK_BASE_URL", self.descriptor.base_url),
            max_retries=self._max_retries,
            timeout=self._timeout,
        )

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model_override: Optional[str] = None,
    ) -> dict:
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        base_delay = float(os.getenv("LLM_RETRY_BASE_DELAY", "2.0"))

        async def _do_call():
            response = await self._client.chat.completions.create(
                model=model_override or self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            raw = response.choices[0].message.content.strip()
            self._record_usage(response)
            return self._parse_json(raw)

        return await retry_with_backoff(_do_call, max_retries=max_retries, base_delay=base_delay)


# ---------------------------------------------------------------------------
# Zydmx (GPT Pro) provider
# ---------------------------------------------------------------------------


class ZydmxProvider(LLMProvider):
    descriptor = LLMProviderDescriptor(
        name="zydmx",
        display_name="GPT Pro",
        base_url="https://zydmx.com/v1",
        default_model="gpt-5.5",
        context_length=200000,
    )

    def __init__(self, api_key=None, base_url=None, model=None):
        super().__init__()
        import os as _os
        self._model = model or _os.getenv("Zydmx_MODEL", self.descriptor.default_model)
        self._max_retries = int(_os.getenv("LLM_MAX_RETRIES", "2"))
        self._timeout = float(_os.getenv("LLM_TIMEOUT", "120"))

        self._client = AsyncOpenAI(
            api_key=api_key or _os.getenv("OPENAI_API_KEY", ""),
            base_url=base_url or _os.getenv("Zydmx_BASE_URL", self.descriptor.base_url),
            max_retries=self._max_retries,
            timeout=self._timeout,
        )

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model_override=None,
    ) -> dict:
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        base_delay = float(os.getenv("LLM_RETRY_BASE_DELAY", "2.0"))

        async def _do_call():
            response = await self._client.responses.create(
                **self._responses_kwargs(
                    model=model_override or self._model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )
            raw = self._extract_response_text(response)
            self._record_usage(response)
            return self._parse_json(raw)

        return await retry_with_backoff(_do_call, max_retries=max_retries, base_delay=base_delay)


# ---------------------------------------------------------------------------
# OpenAI provider (Responses API, same interface)
# ---------------------------------------------------------------------------


class OpenAIProvider(LLMProvider):
    descriptor = LLMProviderDescriptor(
        name="openai",
        display_name="OpenAI",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o",
        context_length=128000,
    )

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self._model = os.getenv("OPENAI_MODEL", self.descriptor.default_model)
        self._client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("OPENAI_BASE_URL", self.descriptor.base_url),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
            timeout=float(os.getenv("LLM_TIMEOUT", "60")),
        )

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model_override: Optional[str] = None,
    ) -> dict:
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        base_delay = float(os.getenv("LLM_RETRY_BASE_DELAY", "2.0"))

        async def _do_call():
            response = await self._client.responses.create(
                **self._responses_kwargs(
                    model=model_override or self._model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )
            raw = self._extract_response_text(response)
            self._record_usage(response)
            return self._parse_json(raw)

        return await retry_with_backoff(_do_call, max_retries=max_retries, base_delay=base_delay)


# ---------------------------------------------------------------------------
# LLM Service — registry + delegation
# ---------------------------------------------------------------------------



class LLMService:
    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}

    def register(self, provider: LLMProvider) -> None:
        self._providers[provider.descriptor.name] = provider

    def list_providers(self) -> list[dict[str, str]]:
        return [
            {
                "name": p.descriptor.name,
                "display_name": p.descriptor.display_name,
                "default_model": p.descriptor.default_model,
                "context_length": p.descriptor.context_length,
            }
            for p in self._providers.values()
        ]

    def get_provider(self, name: str) -> LLMProvider:
        provider = self._providers.get(name)
        if provider is None:
            raise ValueError(
                f"Unknown LLM provider: {name}. Available: {list(self._providers.keys())}"
            )
        return provider

    def get_active(self) -> LLMProvider:
        """Return the configured primary provider; defaults to zydmx / GPT 5.5."""
        if not self._providers:
            raise RuntimeError("No LLM providers registered")
        provider_name = os.getenv("LLM_PROVIDER", "zydmx").strip().lower() or "zydmx"
        if provider_name in self._providers:
            return self._providers[provider_name]
        return self._providers.get("zydmx") or next(iter(self._providers.values()))


# Global singleton — Zydmx (GPT Pro) first = active, DeepSeek = fallback
llm_service = LLMService()
llm_service.register(ZydmxProvider())
llm_service.register(DeepSeekProvider())
