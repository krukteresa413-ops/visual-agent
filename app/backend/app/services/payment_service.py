"""Alipay (沙箱) payment service — 图四 脚手架.

Self-contained RSA2 (SHA256withRSA) sign/verify via `cryptography`, so we
do not add a third-party Alipay SDK dependency. Credentials come from env;
when they are absent `is_configured()` is False and the routes return 503
instead of breaking — the scaffold ships before sandbox keys exist.
"""
from __future__ import annotations

import base64
import datetime
import os
import time
import uuid
from dataclasses import dataclass
from urllib.parse import quote_plus

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# ---- Recharge tiers (前端展示;基础 10 积分/元,高档加赠) ----
RECHARGE_TIERS = [
    {"amount_fen": 600, "credits": 60, "label": "¥6"},
    {"amount_fen": 3000, "credits": 300, "label": "¥30"},
    {"amount_fen": 9800, "credits": 1000, "label": "¥98"},
    {"amount_fen": 29800, "credits": 3200, "label": "¥298"},
]


def get_tier(amount_fen: int) -> dict | None:
    for tier in RECHARGE_TIERS:
        if tier["amount_fen"] == amount_fen:
            return tier
    return None


@dataclass
class AlipayConfig:
    app_id: str
    app_private_key: str
    alipay_public_key: str
    gateway: str
    notify_url: str
    return_url: str


def load_config() -> AlipayConfig | None:
    app_id = os.getenv("ALIPAY_APP_ID", "").strip()
    app_private_key = os.getenv("ALIPAY_APP_PRIVATE_KEY", "").strip()
    alipay_public_key = os.getenv("ALIPAY_PUBLIC_KEY", "").strip()
    gateway = os.getenv("ALIPAY_GATEWAY", "https://openapi-sandbox.dl.alipaydev.com/gateway.do").strip()
    if not (app_id and app_private_key and alipay_public_key and gateway):
        return None
    return AlipayConfig(
        app_id=app_id,
        app_private_key=app_private_key,
        alipay_public_key=alipay_public_key,
        gateway=gateway,
        notify_url=os.getenv("ALIPAY_NOTIFY_URL", "").strip(),
        return_url=os.getenv("ALIPAY_RETURN_URL", "").strip(),
    )


def is_configured() -> bool:
    return load_config() is not None


# ---- key helpers: accept raw base64 body OR full PEM ----
def _wrap_pem(body: str, label: str) -> str:
    body = body.strip()
    if "-----BEGIN" in body:
        return body
    body = body.replace("\n", "").replace("\r", "").replace(" ", "")
    lines = "\n".join(body[i:i + 64] for i in range(0, len(body), 64))
    return f"-----BEGIN {label}-----\n{lines}\n-----END {label}-----\n"


def _load_private_key(pem_or_body: str):
    pem = _wrap_pem(pem_or_body, "PRIVATE KEY")
    return serialization.load_pem_private_key(pem.encode("utf-8"), password=None)


def _load_public_key(pem_or_body: str):
    pem = _wrap_pem(pem_or_body, "PUBLIC KEY")
    return serialization.load_pem_public_key(pem.encode("utf-8"))


# ---- sign / verify (RSA2) ----
def _sign_content(params: dict) -> str:
    items = sorted(
        (k, v) for k, v in params.items()
        if k not in ("sign", "sign_type") and v not in (None, "")
    )
    return "&".join(f"{k}={v}" for k, v in items)


def sign(params: dict, private_key_pem: str) -> str:
    key = _load_private_key(private_key_pem)
    sig = key.sign(_sign_content(params).encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode("ascii")


def verify(params: dict, public_key_pem: str) -> bool:
    sign_b64 = params.get("sign")
    if not sign_b64:
        return False
    try:
        key = _load_public_key(public_key_pem)
        key.verify(
            base64.b64decode(sign_b64),
            _sign_content(params).encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


def generate_out_trade_no() -> str:
    return f"MOYAG{int(time.time())}{uuid.uuid4().hex[:8]}"


def build_page_pay_url(config: AlipayConfig, out_trade_no: str, amount_fen: int, subject: str) -> str:
    """Build the alipay.trade.page.pay redirect URL (signed)."""
    import json

    biz_content = {
        "out_trade_no": out_trade_no,
        "total_amount": f"{amount_fen / 100:.2f}",
        "subject": subject,
        "product_code": "FAST_INSTANT_TRADE_PAY",
    }
    params = {
        "app_id": config.app_id,
        "method": "alipay.trade.page.pay",
        "format": "JSON",
        "charset": "utf-8",
        "sign_type": "RSA2",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0",
        "biz_content": json.dumps(biz_content, ensure_ascii=False, separators=(",", ":")),
    }
    if config.notify_url:
        params["notify_url"] = config.notify_url
    if config.return_url:
        params["return_url"] = config.return_url
    params["sign"] = sign(params, config.app_private_key)
    query = "&".join(f"{k}={quote_plus(str(v))}" for k, v in params.items())
    return f"{config.gateway}?{query}"


def grant_credits(db, out_trade_no: str, alipay_trade_no: str | None = None) -> bool:
    """Idempotently mark an order paid and add its credits to the user.

    Returns True only on the transition pending -> paid (so repeated Alipay
    notifications never double-credit). Returns False if order missing,
    already paid, or user missing.
    """
    from app.models.auth import User
    from app.models.credit import CreditOrder

    order = db.query(CreditOrder).filter(CreditOrder.out_trade_no == out_trade_no).first()
    if order is None or order.status == "paid":
        return False
    user = db.query(User).filter(User.id == order.user_id).first()
    if user is None:
        return False
    user.credits = (user.credits or 0) + order.credits
    order.status = "paid"
    order.alipay_trade_no = alipay_trade_no
    order.paid_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    return True
