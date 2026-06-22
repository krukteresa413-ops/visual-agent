import pytest

from app.services.vision_service import VisionService


class FakeResponse:
    status_code = 200
    text = "ok"

    def json(self):
        return {
            "output_text": "识别结果",
            "model": "gpt-4o",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
            },
        }


class FakeAsyncClient:
    requests = []

    def __init__(self, timeout):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, headers, json):
        self.requests.append({"url": url, "headers": headers, "json": json})
        return FakeResponse()


@pytest.mark.asyncio
async def test_analyze_uses_openai_responses_multimodal_payload(monkeypatch):
    import httpx

    FakeAsyncClient.requests.clear()
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    service = VisionService()
    service._api_key = "test-key"
    service._base_url = "https://api.openai.com/v1"

    result = await service.analyze(["https://example.com/image.png"], "描述图片")

    assert result["success"] is True
    assert result["content"] == "识别结果"

    request = FakeAsyncClient.requests[0]
    assert request["url"] == "https://api.openai.com/v1/responses"
    assert request["json"] == {
        "model": "gpt-4o",
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "描述图片"},
                    {"type": "input_image", "image_url": "https://example.com/image.png", "detail": "auto"},
                ],
            }
        ],
        "max_output_tokens": 1024,
        "temperature": 0.3,
    }
    assert "messages" not in request["json"]


def test_vision_rejects_upload_path_traversal():
    service = VisionService()

    for value in ["/uploads/../app/backend/main.py", "uploads/../app/backend/main.py"]:
        try:
            service._image_to_base64(value)
        except ValueError as exc:
            assert "outside uploads" in str(exc) or "invalid image path" in str(exc)
        else:
            raise AssertionError(f"expected path rejection: {value}")
