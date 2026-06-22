def test_image_first_history_model_prefers_provider_model_over_llm_unknown():
    from app.api.unified_generation_routes import _history_model_used

    assert _history_model_used({
        "_provider_raw": {"model": "gpt-image-2-pro", "requested_model": "gpt-image-1.5-sp", "provider": "dataeyes"},
        "main_image": {"model": "gpt-image-1.5-sp", "provider_model": "gpt-image-2-pro"},
    }, llm_model="unknown") == "dataeyes:gpt-image-2-pro"


def test_generation_history_model_falls_back_to_requested_model_then_llm():
    from app.api.unified_generation_routes import _history_model_used

    assert _history_model_used({"main_image": {"model": "gpt-image-1-sp"}}, llm_model="unknown") == "gpt-image-1-sp"
    assert _history_model_used({}, llm_model="deepseek-v4-pro") == "deepseek-v4-pro"
