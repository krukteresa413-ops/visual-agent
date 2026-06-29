"""以图生图路由 — DataEyes provider 必须真正读取源图。

核心契约(本次需求二):
- 凡是带 reference_image_url 的请求,即便调用方用的是 gpt-image-2(/images/generations
  不接收图片输入),provider 也要自动切到能吃图的 gemini/NanoBanana 模型,
  并把源图作为多模态内容喂进 chat/completions。
- 不带源图时维持原行为(gpt-image-2 → /images/generations),不得回归。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.image_generation_model import ImageGenerationRequest
from app.services.image_generation_service import DataEyesAIImageProvider

# 1x1 透明 PNG (与现有 test_dataeyes_format_adapters 同款)
_TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def _provider():
    p = DataEyesAIImageProvider(api_key="test-key", base_url="https://cloud.dataeyes.ai/v1")
    p._api_key = "test-key"
    return p


def _nb_response():
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "id": "chatcmpl-img2img",
        "choices": [{"message": {"content": f"![image](data:image/png;base64,{_TINY_PNG_B64})"}}],
    }
    return resp


class TestReferenceImageRoutesToImg2Img:
    @pytest.mark.asyncio
    async def test_reference_image_url_forces_gemini_chat_completions(self):
        """有 reference_image_url 时,即便 model 是 gpt-image-2,也要走 chat/completions
        且把源图作为 image_url 内容喂进去,模型自动切到 gemini 系。"""
        provider = _provider()
        with patch.object(provider, "_get_client") as mock_client:
            mock_client.return_value.post = AsyncMock(return_value=_nb_response())
            req = ImageGenerationRequest(
                provider="dataeyes",
                prompt="把背景换成沙滩,保留产品主体",
                model="gpt-image-2",  # 调用方用的是不吃图的模型
                reference_image_url="http://example.test/product.png",
            )
            result = await provider.generate(req)

        assert result.status == "succeeded"
        call = mock_client.return_value.post.call_args
        # 必须打到 chat/completions(吃图端点),而不是 /images/generations
        assert "/chat/completions" in str(call)
        payload = call.kwargs["json"]
        # 模型被自动切到能吃图的 gemini 系
        assert payload["model"].startswith("gemini"), payload["model"]
        # 源图作为多模态内容被喂进去
        content = payload["messages"][0]["content"]
        urls = [c["image_url"]["url"] for c in content if c.get("type") == "image_url"]
        assert "http://example.test/product.png" in urls
        # 用户的修改指令(prompt)同时在场
        texts = [c["text"] for c in content if c.get("type") == "text"]
        assert any("沙滩" in t for t in texts)

    @pytest.mark.asyncio
    async def test_options_image_urls_also_route_img2img(self):
        """老入口 options.image_urls 同样触发以图生图路由。"""
        provider = _provider()
        with patch.object(provider, "_get_client") as mock_client:
            mock_client.return_value.post = AsyncMock(return_value=_nb_response())
            req = ImageGenerationRequest(
                provider="dataeyes",
                prompt="改成冬季氛围",
                model="gpt-image-2",
                options={"image_urls": ["http://example.test/a.png"]},
            )
            result = await provider.generate(req)
        assert result.status == "succeeded"
        payload = mock_client.return_value.post.call_args.kwargs["json"]
        assert "/chat/completions" in str(mock_client.return_value.post.call_args)
        content = payload["messages"][0]["content"]
        urls = [c["image_url"]["url"] for c in content if c.get("type") == "image_url"]
        assert "http://example.test/a.png" in urls

    def test_coerce_image_ref_passes_through_http_and_data(self):
        from app.services.image_generation_service import _coerce_image_ref
        assert _coerce_image_ref("http://x/y.png") == "http://x/y.png"
        assert _coerce_image_ref("https://x/y.png") == "https://x/y.png"
        assert _coerce_image_ref("data:image/png;base64,AAAA") == "data:image/png;base64,AAAA"

    def test_coerce_image_ref_blocks_path_traversal(self):
        from app.services.image_generation_service import _coerce_image_ref
        # uploads 目录之外的路径不读盘,原样返回(交由上游报错可见)
        assert _coerce_image_ref("/etc/passwd") == "/etc/passwd"

    @pytest.mark.asyncio
    async def test_no_reference_keeps_openai_generations(self):
        """回归:无源图时仍走 gpt-image-2 的 /images/generations,不受影响。"""
        provider = _provider()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"data": [{"b64_json": _TINY_PNG_B64}]}
        with patch.object(provider, "_get_client") as mock_client:
            mock_client.return_value.post = AsyncMock(return_value=resp)
            req = ImageGenerationRequest(
                provider="dataeyes",
                prompt="一个红苹果",
                model="gpt-image-2",
            )
            result = await provider.generate(req)
        assert result.status == "succeeded"
        assert "/images/generations" in str(mock_client.return_value.post.call_args)
