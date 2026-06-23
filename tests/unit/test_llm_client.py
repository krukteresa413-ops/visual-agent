"""
LLM Client 单元测试。
用 mock 替代真实 API 调用，测试：
1. 正常返回 JSON 能被正确解析
2. API 错误能被捕获
3. 非 JSON 返回能被处理
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestLLMClient:

    @pytest.mark.asyncio
    async def test_call_returns_parsed_json(self):
        """正常调用返回有效JSON"""
        from app.services.llm_client import LLMClient

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"goal": "test goal", "composition": "centered"}'))
        ]

        client = LLMClient()
        with patch.object(client._client.chat.completions, "create", new_callable=AsyncMock, return_value=mock_response):
            result = await client.call(
                system_prompt="You are a helpful assistant.",
                user_prompt="Generate a main image plan.",
            )
        assert result["goal"] == "test goal"

    @pytest.mark.asyncio
    async def test_call_handles_invalid_json(self):
        """模型返回非JSON时抛出明确错误"""
        from app.services.llm_client import LLMClient, LLMResponseError

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="This is not JSON at all"))
        ]

        client = LLMClient()
        with patch.object(client._client.chat.completions, "create", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(LLMResponseError):
                await client.call(
                    system_prompt="You are a helpful assistant.",
                    user_prompt="Generate something.",
                )

    @pytest.mark.asyncio
    async def test_call_strips_markdown_fences(self):
        """模型返回被 ```json 包裹的内容时能正确解析"""
        from app.services.llm_client import LLMClient

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='```json\n{"goal": "stripped"}\n```'))
        ]

        client = LLMClient()
        with patch.object(client._client.chat.completions, "create", new_callable=AsyncMock, return_value=mock_response):
            result = await client.call(
                system_prompt="test",
                user_prompt="test",
            )
        assert result["goal"] == "stripped"
