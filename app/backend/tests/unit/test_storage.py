"""storage.py 单测（Phase O1）。刻意不 import main/db/models，可脱离生产库独立跑。
放置：app/backend/tests/unit/test_storage.py；跑：.venv/bin/python -m pytest tests/unit/test_storage.py -q"""
from __future__ import annotations

import asyncio
import re

import pytest

from app.services import storage
from app.services.storage import (
    build_key, LocalBackend, OSSBackend, get_storage, reset_storage,
)

KEY_TP = re.compile(r"^t/5/p/12/generated/\d{6}/[0-9a-f]{32}\.png$")
KEY_MISC = re.compile(r"^t/5/_misc/upload/\d{6}/[0-9a-f]{32}\.jpg$")
KEY_SHARED = re.compile(r"^shared/generated/\d{6}/[0-9a-f]{32}\.png$")


# ── build_key ─────────────────────────────────────────────
def test_build_key_tenant_project():
    assert KEY_TP.match(build_key(tenant_id=5, project_id=12, category="generated", ext="png"))

def test_build_key_tenant_only_goes_misc():
    assert KEY_MISC.match(build_key(tenant_id=5, project_id=None, category="upload", ext=".JPG"))

def test_build_key_no_tenant_goes_shared():
    assert KEY_SHARED.match(build_key(tenant_id=None, project_id=None, category="generated", ext="png"))

def test_build_key_unique_each_call():
    a = build_key(tenant_id=1, project_id=1, category="generated", ext="png")
    b = build_key(tenant_id=1, project_id=1, category="generated", ext="png")
    assert a != b

def test_build_key_ext_normalized():
    assert build_key(tenant_id=1, project_id=1, category="generated", ext=".PNG").endswith(".png")


# ── LocalBackend ──────────────────────────────────────────
@pytest.fixture
def local(tmp_path):
    return LocalBackend(root=str(tmp_path))

def test_local_save_read_delete(local, tmp_path):
    url = local.save_bytes_sync(b"hello", tenant_id=5, project_id=12, category="generated", ext="png")
    assert url.startswith("/uploads/t/5/p/12/generated/") and url.endswith(".png")
    rel = url[len("/uploads/"):]
    assert (tmp_path / rel).read_bytes() == b"hello"      # 真落盘
    assert local.read_bytes_sync(url) == b"hello"          # 传 url 能读
    assert local.read_bytes_sync(rel) == b"hello"          # 传 key 也能读
    local.delete_sync(url)
    assert not (tmp_path / rel).exists()

def test_local_tenant_only_misc(local):
    url = local.save_bytes_sync(b"x", tenant_id=9, project_id=None, category="upload", ext="bin")
    assert "/uploads/t/9/_misc/upload/" in url

def test_local_list_prefix_is_project_scoped(local):
    local.save_bytes_sync(b"1", tenant_id=5, project_id=12, category="generated", ext="png")
    local.save_bytes_sync(b"2", tenant_id=5, project_id=99, category="generated", ext="png")
    local.save_bytes_sync(b"3", tenant_id=7, project_id=1, category="generated", ext="png")
    assert len(local.list_prefix(5)) == 2         # 整租户
    assert len(local.list_prefix(5, 12)) == 1     # 单项目：删除安全，只命中该项目
    assert local.list_prefix(999) == []

def test_local_save_pil(local):
    Image = pytest.importorskip("PIL.Image")
    img = Image.new("RGB", (4, 4), (10, 20, 30))
    url = local.save_pil_sync(img, tenant_id=5, project_id=12, category="generated", fmt="PNG")
    assert url.endswith(".png")
    assert local.read_bytes_sync(url)[:8] == b"\x89PNG\r\n\x1a\n"

def test_local_path_traversal_guarded(local):
    with pytest.raises(ValueError):
        local._abs("../../etc/passwd")

def test_unknown_category_rejected(local):
    with pytest.raises(ValueError):
        local.save_bytes_sync(b"x", tenant_id=1, project_id=1, category="bogus", ext="png")

def test_async_save_offloads(local):
    url = asyncio.run(local.save_bytes(b"async", tenant_id=5, project_id=12, category="generated", ext="png"))
    assert local.read_bytes_sync(url) == b"async"


# ── OSSBackend（注入 FakeBucket，绕过真实 oss2） ──────────────
class _FakeObj:
    def __init__(self, data): self._d = data
    def read(self): return self._d

class _KeyObj:
    def __init__(self, key): self.key = key

class FakeBucket:
    def __init__(self, fail_times=0):
        self.puts, self.deleted, self._store = [], [], {}
        self._fail_times, self._put_calls = fail_times, 0
    def put_object(self, key, data, headers=None):
        self._put_calls += 1
        if self._put_calls <= self._fail_times:
            raise RuntimeError("transient oss error")
        self._store[key] = data
        self.puts.append((key, data, headers))
    def get_object(self, key):
        return _FakeObj(self._store[key])
    def delete_object(self, key):
        self.deleted.append(key); self._store.pop(key, None)

class FakeOss2:
    @staticmethod
    def ObjectIterator(bucket, prefix=""):
        return [_KeyObj(k) for k in bucket._store if k.startswith(prefix)]

def _oss(**kw):
    b = FakeBucket(**kw)
    return OSSBackend(bucket=b, public_base="https://cdn.test", oss2_mod=FakeOss2), b

def test_oss_put_returns_cdn_url_and_headers():
    oss, b = _oss()
    url = oss.save_bytes_sync(b"img", tenant_id=5, project_id=12, category="generated",
                              ext="png", content_type="image/png")
    key = url[len("https://cdn.test/"):]
    assert url == f"https://cdn.test/{key}" and key.startswith("t/5/p/12/generated/")
    put_key, put_data, headers = b.puts[0]
    assert put_key == key and put_data == b"img"
    assert headers["Content-Type"] == "image/png" and "max-age" in headers["Cache-Control"]

def test_oss_put_retries_then_succeeds():
    oss, b = _oss(fail_times=2)     # 前两次失败，第三次成功（默认 max_retries=3）
    url = oss.save_bytes_sync(b"x", tenant_id=1, project_id=1, category="generated", ext="png")
    assert url.startswith("https://cdn.test/") and b._put_calls == 3

def test_oss_put_raises_after_retries_exhausted():
    oss, _ = _oss(fail_times=99)
    with pytest.raises(RuntimeError):
        oss.save_bytes_sync(b"x", tenant_id=1, project_id=1, category="generated", ext="png")

def test_oss_get_delete_accept_url_or_key():
    oss, b = _oss()
    url = oss.save_bytes_sync(b"data", tenant_id=5, project_id=12, category="generated", ext="png")
    assert oss.read_bytes_sync(url) == b"data"
    oss.delete_sync(url)
    assert b.deleted[0] == url[len("https://cdn.test/"):]

def test_oss_list_prefix_project_scoped():
    oss, _ = _oss()
    oss.save_bytes_sync(b"1", tenant_id=5, project_id=12, category="generated", ext="png")
    oss.save_bytes_sync(b"2", tenant_id=5, project_id=99, category="generated", ext="png")
    assert len(oss.list_prefix(5)) == 2 and len(oss.list_prefix(5, 12)) == 1


# ── get_storage 选择 ──────────────────────────────────────
def test_get_storage_defaults_local(monkeypatch):
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    reset_storage()
    assert isinstance(get_storage(), LocalBackend)
    reset_storage()

def test_get_storage_selects_oss(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "oss")
    monkeypatch.setattr(storage, "OSSBackend", lambda: "OSS_SENTINEL")
    reset_storage()
    assert get_storage() == "OSS_SENTINEL"
    reset_storage()
