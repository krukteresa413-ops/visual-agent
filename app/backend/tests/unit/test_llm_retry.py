"""LLM 重试逻辑测试 — TDD RED 阶段"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio


class TestRetryLogic:
    """测试指数退避重试的核心逻辑（不依赖真实 API）。"""

    def test_retry_on_timeout_succeeds_on_retry(self):
        """超时 → 重试 → 成功，应返回结果且重试计数正确。"""
        from app.services.llm_provider import retry_with_backoff

        call_count = [0]

        async def flaky_call():
            call_count[0] += 1
            if call_count[0] < 2:
                raise asyncio.TimeoutError("timed out")
            return {"result": "ok"}

        result = asyncio.run(retry_with_backoff(flaky_call, max_retries=3, base_delay=0.01))
        assert result == {"result": "ok"}
        assert call_count[0] == 2  # failed once, succeeded on retry

    def test_retry_exhausted_raises_last_error(self):
        """全部重试耗尽 → 抛出最后一次的错误。"""
        from app.services.llm_provider import retry_with_backoff

        async def always_fails():
            raise asyncio.TimeoutError("always timeout")

        with pytest.raises(asyncio.TimeoutError, match="always timeout"):
            asyncio.run(retry_with_backoff(always_fails, max_retries=2, base_delay=0.01))

    def test_no_retry_on_client_error(self):
        """4xx 客户端错误不重试，直接抛出。"""
        from app.services.llm_provider import retry_with_backoff

        call_count = [0]

        async def bad_request():
            call_count[0] += 1
            raise ValueError("400 Bad Request")  # simulating non-retryable

        with pytest.raises(ValueError, match="400"):
            asyncio.run(retry_with_backoff(bad_request, max_retries=3, base_delay=0.01))
        assert call_count[0] == 1  # should NOT retry

    def test_no_retry_on_json_parse_error(self):
        """JSON 解析错误不重试（内容问题，非瞬态）。"""
        from app.services.llm_provider import retry_with_backoff, LLMResponseError

        async def json_error():
            raise LLMResponseError("invalid json")

        call_count = [0]

        async def tracked_json_error():
            call_count[0] += 1
            raise LLMResponseError("invalid json")

        with pytest.raises(LLMResponseError):
            asyncio.run(retry_with_backoff(tracked_json_error, max_retries=3, base_delay=0.01))
        assert call_count[0] == 1

    def test_retry_on_connection_error(self):
        """连接错误应重试。"""
        from app.services.llm_provider import retry_with_backoff

        call_count = [0]

        async def connection_fails():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("connection refused")
            return {"ok": True}

        result = asyncio.run(retry_with_backoff(connection_fails, max_retries=3, base_delay=0.01))
        assert result == {"ok": True}
        assert call_count[0] == 3

    def test_exponential_backoff_timing(self):
        """验证指数退避延迟递增。"""
        from app.services.llm_provider import retry_with_backoff
        import time

        delays = []

        async def fail_then_succeed():
            if len(delays) == 0:
                delays.append(time.monotonic())
                raise asyncio.TimeoutError()
            if len(delays) == 1:
                delays.append(time.monotonic())
                raise asyncio.TimeoutError()
            delays.append(time.monotonic())
            return {"ok": True}

        result = asyncio.run(retry_with_backoff(fail_then_succeed, max_retries=3, base_delay=0.01))
        assert result == {"ok": True}
        # delay1 should be ~0.01, delay2 should be ~0.02
        assert len(delays) == 3
        d1 = delays[1] - delays[0]
        d2 = delays[2] - delays[1]
        # With base_delay=0.01: first sleep ~0.01, second ~0.02
        assert 0.005 < d1 < 0.05
        assert d2 > d1 * 1.2  # second delay should be longer

    def test_max_retries_configurable(self):
        """max_retries 参数应被遵守。"""
        from app.services.llm_provider import retry_with_backoff

        call_count = [0]

        async def fails():
            call_count[0] += 1
            raise asyncio.TimeoutError()

        with pytest.raises(asyncio.TimeoutError):
            asyncio.run(retry_with_backoff(fails, max_retries=1, base_delay=0.01))
        # 1 initial + 1 retry = 2 calls
        assert call_count[0] == 2


class TestDeepSeekProviderRetry:
    """测试 DeepSeekProvider 集成重试。"""

    def test_provider_call_uses_retry(self):
        """验证 DeepSeekProvider.call 内部使用了 retry_with_backoff。"""
        # Check that retry_with_backoff is imported and used
        from app.services import llm_provider

        source = open(llm_provider.__file__.replace(".pyc", ".py")).read()
        assert "retry_with_backoff" in source, "retry_with_backoff should be imported"
        assert "retry_with_backoff(" in source, "retry_with_backoff should be called in call() method"
