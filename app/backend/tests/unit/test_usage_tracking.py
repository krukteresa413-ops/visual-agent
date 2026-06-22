"""Unit tests for LLM usage tracking."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.llm_provider import DeepSeekProvider, LLMProvider


class FakeProvider(LLMProvider):
    """Isolated fake provider for testing — no singleton sharing."""
    descriptor = DeepSeekProvider.descriptor

    def __init__(self):
        super().__init__()

    async def call(self, system_prompt, user_prompt, temperature=0.7, max_tokens=4096, model_override=None):
        response = await self._client.chat.completions.create(
            model=model_override or "test-model",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = response.choices[0].message.content.strip()
        self._record_usage(response)
        return self._parse_json(raw)


class TestLLMUsageTracking:

    @pytest.mark.asyncio
    async def test_tracks_call_count_and_tokens(self):
        """统计调用次数和 token 消耗"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"goal": "test"}'))
        ]
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 50

        provider = FakeProvider()
        provider._client = MagicMock()
        with patch.object(provider._client.chat.completions, "create", new_callable=AsyncMock, return_value=mock_response):
            await provider.call(system_prompt="s", user_prompt="u")
            await provider.call(system_prompt="s", user_prompt="u")

        stats = provider.get_usage_stats()
        assert stats["total_calls"] == 2
        assert stats["total_prompt_tokens"] == 300
        assert stats["total_completion_tokens"] == 100
        assert stats["estimated_cost_usd"] > 0

    @pytest.mark.asyncio
    async def test_reset_stats(self):
        """重置统计"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"goal": "test"}'))
        ]
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        provider = FakeProvider()
        provider._client = MagicMock()
        with patch.object(provider._client.chat.completions, "create", new_callable=AsyncMock, return_value=mock_response):
            await provider.call(system_prompt="s", user_prompt="u")

        provider.reset_usage_stats()
        stats = provider.get_usage_stats()
        assert stats["total_calls"] == 0
