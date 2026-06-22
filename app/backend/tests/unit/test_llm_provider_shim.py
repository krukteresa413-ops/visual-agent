"""Module 1 契约测试：providers.llm 必须 re-export 现有 llm_provider，且行为不变。
此测试在 app/providers/ 尚未建立时应失败（import error）= TDD 红。"""
import inspect

from app.providers import llm as plm
from app.services import llm_provider as svc


def test_reexport_is_same_object():
    # providers.llm 导出的类必须与 services.llm_provider 是同一对象（同一性，不是副本）
    for name in [
        "LLMProvider", "LLMProviderDescriptor", "LLMResponseError",
        "DeepSeekProvider", "ZydmxProvider", "OpenAIProvider",
        "LLMService", "retry_with_backoff",
    ]:
        assert getattr(plm, name) is getattr(svc, name), f"{name} 不是同一对象"


def test_descriptor_metadata_unchanged():
    assert svc.DeepSeekProvider.descriptor.name == "deepseek"
    assert svc.DeepSeekProvider.descriptor.base_url == "https://api.deepseek.com"
    assert svc.DeepSeekProvider.descriptor.default_model == "deepseek-v4-pro"
    assert svc.DeepSeekProvider.descriptor.context_length == 1_000_000

    assert svc.ZydmxProvider.descriptor.name == "zydmx"
    assert svc.ZydmxProvider.descriptor.base_url == "https://zydmx.com/v1"
    assert svc.ZydmxProvider.descriptor.default_model == "gpt-5.5"
    assert svc.ZydmxProvider.descriptor.context_length == 200000

    assert svc.OpenAIProvider.descriptor.name == "openai"
    assert svc.OpenAIProvider.descriptor.base_url == "https://api.openai.com/v1"
    assert svc.OpenAIProvider.descriptor.default_model == "gpt-4o"
    assert svc.OpenAIProvider.descriptor.context_length == 128000


def test_call_signature_unchanged():
    sig = inspect.signature(svc.LLMProvider.call)
    params = list(sig.parameters)
    assert params == ["self", "system_prompt", "user_prompt", "temperature", "max_tokens", "model_override"]


def test_llm_service_registry_behavior():
    s = svc.LLMService()
    p = svc.DeepSeekProvider(api_key="dummy")
    s.register(p)
    listed = s.list_providers()
    assert any(d.get("name") == "deepseek" for d in listed)
    assert s.get_provider("deepseek") is p


def test_existing_import_surface_untouched():
    # 现有调用方仍从 services.llm_provider import，第一刀不动这条
    import app.services.llm_client as client_mod
    src = inspect.getsource(client_mod)
    assert "from app.services.llm_provider import" in src
