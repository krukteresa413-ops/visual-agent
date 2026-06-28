"""借零件#4: 品牌记忆字段(target_audience/product_images/memory_summary)接口往返测试.

测试品牌名以 TestBrand 前缀(会被 list 接口过滤,不污染展示),并在 finally 删除。
"""
import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_brand_memory_fields_create_update_roundtrip():
    name = f"TestBrandMem_{uuid.uuid4().hex[:6]}"
    payload = {
        "name": name,
        "primary_color": "#123456",
        "target_audience": "25-35岁都市女性",
        "product_images": ["/uploads/a.png", "/uploads/b.png"],
        "memory_summary": "东方、松弛、高级,不要太网红",
    }
    r = client.post("/api/v1/brand/manage/create", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    bid = data["id"]
    try:
        # 创建即往返
        assert data["target_audience"] == "25-35岁都市女性"
        assert data["product_images"] == ["/uploads/a.png", "/uploads/b.png"]
        assert data["memory_summary"] == "东方、松弛、高级,不要太网红"
        # 更新往返
        upd = {**payload, "memory_summary": "改后:更克制的高级感"}
        r2 = client.patch(f"/api/v1/brand/manage/{bid}", json=upd)
        assert r2.status_code == 200, r2.text
        assert r2.json()["memory_summary"] == "改后:更克制的高级感"
        assert r2.json()["target_audience"] == "25-35岁都市女性"
    finally:
        client.delete(f"/api/v1/brand/manage/{bid}")


def test_brand_memory_fields_optional():
    """不传新字段也应正常创建(向后兼容)。"""
    name = f"TestBrandMem_{uuid.uuid4().hex[:6]}"
    r = client.post("/api/v1/brand/manage/create", json={"name": name, "primary_color": "#abcdef"})
    assert r.status_code == 200, r.text
    data = r.json()
    bid = data["id"]
    try:
        assert data["target_audience"] is None
        assert data["product_images"] == []
        assert data["memory_summary"] is None
    finally:
        client.delete(f"/api/v1/brand/manage/{bid}")
