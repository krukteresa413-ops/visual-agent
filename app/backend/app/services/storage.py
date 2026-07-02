"""统一资产存储抽象层（OSS 多租户地基 · Phase O1）。

设计见 D:\\Desktop\\MOYAG-OSS-多租户-落地方案.md：
- 收敛全部 ~10 处散落的本地落盘点到一处 save_*()。
- 两个后端：LocalBackend（现行为，dev/兼容兜底）、OSSBackend（阿里云 OSS）。
- key 规则（tenant+project 双层分区，删除安全）：
    t/{tenant_id}/p/{project_id}/{category}/{YYYYMM}/{uuid}.{ext}   有项目
    t/{tenant_id}/_misc/{category}/{YYYYMM}/{uuid}.{ext}            有租户无项目
    shared/{category}/{YYYYMM}/{uuid}.{ext}                        无租户
- 后端由 env STORAGE_BACKEND(local|oss) 选择，可秒级回退。
- oss2 是同步阻塞库 → 公开方法做成 async（asyncio.to_thread offload，不阻塞事件循环）；
  另给 *_sync 变体供少数同步调用点。需 Python 3.9+（asyncio.to_thread）。
- 本模块刻意不 import DB/models：只吃 int 型 tenant_id/project_id，便于隔离单测
  （项目内 pytest 一 import main 就连生产库，本模块要能脱离它独立测）。
- oss2/PIL 延迟 import：本地未装 oss2 也能 import 本模块并跑 LocalBackend。
"""
from __future__ import annotations

import asyncio
import io
import logging
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# 与现有 main.py `app.mount("/uploads", StaticFiles(directory=".../uploads"))` 对齐
LOCAL_ROOT = os.getenv("UPLOADS_ROOT", "/opt/visual-agent/uploads")
LOCAL_URL_PREFIX = "/uploads"

_ALLOWED_CATEGORIES = {"generated", "upload", "font", "logo", "video-edit"}


def _yyyymm() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m")


def build_key(*, tenant_id: Optional[int], project_id: Optional[int],
              category: str, ext: str) -> str:
    """构造对象 key。有 project 时带 p/{project_id} —— 删除安全的关键：
    删项目按 t/{tid}/p/{pid}/ 前缀操作不会误伤同租户其它项目（方案 §3.2 / 审查修正#1）。
    """
    ext = (ext or "bin").lstrip(".").lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    ym = _yyyymm()
    if tenant_id is not None and project_id is not None:
        scope = f"t/{int(tenant_id)}/p/{int(project_id)}"
    elif tenant_id is not None:
        scope = f"t/{int(tenant_id)}/_misc"
    else:
        scope = "shared"
    return f"{scope}/{category}/{ym}/{name}"


class StorageBackend(ABC):
    """同步核心原语（_put/_get/_delete/list_prefix）由子类实现；
    对外提供 async（默认，offload）与 *_sync（同步调用点用）两套 save/read/delete。"""

    # ── 子类实现的同步原语 ────────────────────────────────────
    @abstractmethod
    def _put(self, data: bytes, key: str, content_type: Optional[str]) -> str:
        """写对象，返回可访问 URL。"""

    @abstractmethod
    def _get(self, key_or_url: str) -> bytes:
        ...

    @abstractmethod
    def _delete(self, key_or_url: str) -> None:
        ...

    @abstractmethod
    def list_prefix(self, tenant_id: int, project_id: Optional[int] = None) -> List[str]:
        """列 t/{tid}[/p/{pid}] 前缀下的 key（GC/配额用；不做内联删，见方案 O3d）。"""

    # ── 同步公开 API（同步调用点用；OSS 下会阻塞，别在 async 端点里用） ──
    def save_bytes_sync(self, data: bytes, *, tenant_id: Optional[int], category: str,
                        ext: str, project_id: Optional[int] = None,
                        content_type: Optional[str] = None) -> str:
        if category not in _ALLOWED_CATEGORIES:
            raise ValueError(f"unknown storage category: {category!r}")
        key = build_key(tenant_id=tenant_id, project_id=project_id, category=category, ext=ext)
        return self._put(data, key, content_type)

    def save_pil_sync(self, img, *, tenant_id: Optional[int], category: str,
                      project_id: Optional[int] = None, fmt: str = "PNG",
                      **save_kwargs) -> str:
        buf = io.BytesIO()
        img.save(buf, fmt, **save_kwargs)
        fmt_u = fmt.upper()
        content_type = {"PNG": "image/png", "JPEG": "image/jpeg",
                        "WEBP": "image/webp", "GIF": "image/gif"}.get(fmt_u, "application/octet-stream")
        ext = {"JPEG": "jpg"}.get(fmt_u, fmt_u.lower())
        return self.save_bytes_sync(buf.getvalue(), tenant_id=tenant_id, project_id=project_id,
                                    category=category, ext=ext, content_type=content_type)

    def read_bytes_sync(self, key_or_url: str) -> bytes:
        return self._get(key_or_url)

    def delete_sync(self, key_or_url: str) -> None:
        self._delete(key_or_url)

    # ── async 公开 API（async 端点用，offload 到线程，不阻塞事件循环，推荐默认） ──
    async def save_bytes(self, data: bytes, *, tenant_id: Optional[int], category: str,
                         ext: str, project_id: Optional[int] = None,
                         content_type: Optional[str] = None) -> str:
        return await asyncio.to_thread(
            self.save_bytes_sync, data, tenant_id=tenant_id, project_id=project_id,
            category=category, ext=ext, content_type=content_type)

    async def save_pil(self, img, *, tenant_id: Optional[int], category: str,
                       project_id: Optional[int] = None, fmt: str = "PNG",
                       **save_kwargs) -> str:
        return await asyncio.to_thread(
            self.save_pil_sync, img, tenant_id=tenant_id, project_id=project_id,
            category=category, fmt=fmt, **save_kwargs)

    async def read_bytes(self, key_or_url: str) -> bytes:
        return await asyncio.to_thread(self._get, key_or_url)

    async def delete(self, key_or_url: str) -> None:
        await asyncio.to_thread(self._delete, key_or_url)


class LocalBackend(StorageBackend):
    """写本地 {root}/{key}，返回相对 /uploads/{key}。复刻现有静态服务行为，dev 与兼容兜底用。"""

    def __init__(self, root: str = LOCAL_ROOT):
        self._root = Path(root)

    def _abs(self, key: str) -> Path:
        # 防目录穿越：key 由 build_key 生成（无 ..），此处再做一次归一校验兜底
        p = (self._root / key).resolve()
        root = self._root.resolve()
        if p != root and root not in p.parents:
            raise ValueError("resolved path escapes uploads root")
        return p

    def _key_from(self, key_or_url: str) -> str:
        s = key_or_url
        if s.startswith(LOCAL_URL_PREFIX + "/"):
            s = s[len(LOCAL_URL_PREFIX) + 1:]
        return s.lstrip("/")

    def _put(self, data: bytes, key: str, content_type: Optional[str] = None) -> str:
        p = self._abs(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)
        return f"{LOCAL_URL_PREFIX}/{key}"

    def _get(self, key_or_url: str) -> bytes:
        with open(self._abs(self._key_from(key_or_url)), "rb") as f:
            return f.read()

    def _delete(self, key_or_url: str) -> None:
        p = self._abs(self._key_from(key_or_url))
        if p.exists():
            p.unlink()

    def list_prefix(self, tenant_id: int, project_id: Optional[int] = None) -> List[str]:
        base = self._root / "t" / str(tenant_id)
        if project_id is not None:
            base = base / "p" / str(project_id)
        if not base.exists():
            return []
        return [str(p.relative_to(self._root)).replace(os.sep, "/")
                for p in base.rglob("*") if p.is_file()]


class OSSBackend(StorageBackend):
    """阿里云 OSS 后端。put/get 走内网 endpoint（免公网流量费），返回 CDN 公共 URL。

    ⚠️ oss2 的凭据类名/签名版本随 SDK 版本略有差异，部署到 ECS 后须按实际安装的
    oss2 版本核对（EcsRamRoleCredentialsProvider / ProviderAuthV4 / AuthV4 / region）。
    测试通过注入 bucket 绕过真实 oss2。
    """

    def __init__(self, *, bucket=None, public_base: Optional[str] = None,
                 oss2_mod=None, max_retries: int = 3):
        # 测试注入路径：直接给 bucket，跳过真实 oss2 初始化
        if bucket is not None:
            self._bucket = bucket
            self._public_base = (public_base or "https://cdn.example").rstrip("/")
            self._oss2 = oss2_mod
            self._max_retries = max_retries
            return

        import oss2  # 延迟 import
        self._bucket_name = os.environ["OSS_BUCKET"]
        self._endpoint = os.environ["OSS_ENDPOINT_INTERNAL"]           # oss-cn-xx-internal.aliyuncs.com
        self._public_base = os.environ["OSS_PUBLIC_BASE"].rstrip("/")  # CDN 域名，如 https://cdn.moyag...
        self._region = os.getenv("OSS_REGION")                          # V4 签名需要
        self._max_retries = int(os.getenv("OSS_PUT_RETRIES", "3"))

        ak, sk = os.getenv("OSS_AK"), os.getenv("OSS_SK")
        if ak and sk:
            # 退路：RAM 子账号 AK/SK（dev / 无法绑角色时）
            auth = oss2.AuthV4(ak, sk) if hasattr(oss2, "AuthV4") else oss2.Auth(ak, sk)
        else:
            # 首选：ECS 实例 RAM 角色，自动取临时凭据，AK/SK 不落地（方案 §3.3）
            from oss2.credentials import EcsRamRoleCredentialsProvider
            role = os.getenv("OSS_RAM_ROLE")
            provider = EcsRamRoleCredentialsProvider(role) if role else EcsRamRoleCredentialsProvider()
            auth = (oss2.ProviderAuthV4(provider) if hasattr(oss2, "ProviderAuthV4")
                    else oss2.ProviderAuth(provider))

        bkw = {}
        if self._region and hasattr(oss2, "AuthV4"):
            bkw["region"] = self._region
        self._bucket = oss2.Bucket(auth, self._endpoint, self._bucket_name, **bkw)
        self._oss2 = oss2

    def _key_from(self, key_or_url: str) -> str:
        s = key_or_url
        if s.startswith(self._public_base + "/"):
            s = s[len(self._public_base) + 1:]
        return s.lstrip("/")

    def _put(self, data: bytes, key: str, content_type: Optional[str] = None) -> str:
        headers = {"Cache-Control": "public, max-age=31536000"}  # 资产不可变，长缓存
        if content_type:
            headers["Content-Type"] = content_type
        last = None
        for attempt in range(1, self._max_retries + 1):
            try:
                self._bucket.put_object(key, data, headers=headers)
                return f"{self._public_base}/{key}"
            except Exception as e:  # noqa: BLE001 — 明确重试；彻底失败要抛，别静默回退本地掩盖问题
                last = e
                logger.warning("OSS put failed (%s/%s) key=%s: %s", attempt, self._max_retries, key, e)
        raise RuntimeError(f"OSS put failed after {self._max_retries} attempts for {key}: {last}")

    def _get(self, key_or_url: str) -> bytes:
        return self._bucket.get_object(self._key_from(key_or_url)).read()

    def _delete(self, key_or_url: str) -> None:
        self._bucket.delete_object(self._key_from(key_or_url))

    def list_prefix(self, tenant_id: int, project_id: Optional[int] = None) -> List[str]:
        prefix = f"t/{tenant_id}/p/{project_id}/" if project_id is not None else f"t/{tenant_id}/"
        return [o.key for o in self._oss2.ObjectIterator(self._bucket, prefix=prefix)]


_backend: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """按 env STORAGE_BACKEND(local|oss) 返回单例后端。默认 local（灰度前安全）。"""
    global _backend
    if _backend is None:
        kind = os.getenv("STORAGE_BACKEND", "local").lower()
        _backend = OSSBackend() if kind == "oss" else LocalBackend()
        logger.info("storage backend = %s", type(_backend).__name__)
    return _backend


def reset_storage() -> None:
    """清单例（测试或改 env 后重取用）。"""
    global _backend
    _backend = None
