from app.services.provider_inventory import build_inventory


def test_inventory_items_have_source_field():
    items = build_inventory()
    assert items
    assert {item.source for item in items} <= {"production", "benchmark", "experimental", "local"}


def test_lovart_marked_benchmark():
    items = [item for item in build_inventory() if item.provider.startswith("lovart")]
    assert items
    assert all(item.source == "benchmark" for item in items)
    assert all(item.production_usable is False for item in items)


def test_three_layers_not_mixed():
    items = build_inventory()
    assert {item.modality for item in items} <= {"image", "video"}
    assert all("zydmx" not in item.provider.lower() for item in items)
    assert all("deepseek" not in item.provider.lower() for item in items)


def test_unconfigured_provider_available_false(monkeypatch):
    monkeypatch.delenv("MIGEAPI_API_KEY", raising=False)
    items = [item for item in build_inventory() if item.provider == "mige"]
    assert items
    assert all(item.configured is False for item in items)
    assert all(item.available is False for item in items)
