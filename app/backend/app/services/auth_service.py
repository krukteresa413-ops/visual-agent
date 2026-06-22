from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from typing import Any

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.auth import Tenant, User

TOKEN_TTL_SECONDS = 60 * 60 * 12
PBKDF2_ITERATIONS = 260_000
ALLOWED_ROLES = {"platform_admin", "tenant_admin", "member"}


def _secret_key() -> bytes:
    value = os.getenv("AUTH_SECRET_KEY") or os.getenv("SECRET_KEY") or "moyag-dev-auth-secret-change-me"
    return value.encode("utf-8")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64url(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or f"tenant-{secrets.token_hex(4)}"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64url(salt)}${_b64url(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _unb64url(salt_b64), int(iterations))
        return hmac.compare_digest(_b64url(digest), digest_b64)
    except Exception:
        return False


def create_access_token(user: User) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user.id),
        "tenant_id": user.tenant_id,
        "role": user.role,
        "email": user.email,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    signing_input = f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}.{_b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(_secret_key(), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".", 2)
        signing_input = f"{header_b64}.{payload_b64}"
        expected = _b64url(hmac.new(_secret_key(), signing_input.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(expected, signature_b64):
            raise ValueError("bad signature")
        payload = json.loads(_unb64url(payload_b64))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("expired token")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="not authenticated")
    payload = decode_access_token(authorization.split(" ", 1)[1].strip())
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="invalid user")
    return user


def ensure_role(user: User, roles: set[str]) -> None:
    if user.role not in roles:
        raise HTTPException(status_code=403, detail="forbidden")


def create_tenant(db: Session, name: str) -> Tenant:
    base_slug = slugify(name)
    slug = base_slug
    suffix = 1
    while db.query(Tenant).filter(Tenant.slug == slug).first():
        suffix += 1
        slug = f"{base_slug}-{suffix}"
    tenant = Tenant(name=name.strip() or slug, slug=slug)
    db.add(tenant)
    db.flush()
    return tenant
