"""Tests for 图四 — Alipay sandbox scaffold + credits.

Covers: tiers endpoint, RSA2 sign/verify roundtrip, create returns 503 when
unconfigured, balance endpoint, and idempotent credit granting.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.services import payment_service
from app.api.payment_routes import router as payment_router
from app.api.credits_routes import router as credits_router
from app.services.auth_service import get_current_user
from app.db.session import get_db


# ---- helpers ----
def _keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pub = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return priv, pub


class FakeUser:
    def __init__(self, uid=1, credits=0):
        self.id = uid
        self.credits = credits


class FakeOrder:
    def __init__(self, out_trade_no="T1", user_id=1, credits=60, status="pending"):
        self.out_trade_no = out_trade_no
        self.user_id = user_id
        self.credits = credits
        self.status = status
        self.alipay_trade_no = None
        self.paid_at = None


class FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *a, **k):
        return self

    def first(self):
        return self._result


class FakeDB:
    def __init__(self, order, user):
        self._order = order
        self._user = user
        self.commits = 0

    def query(self, model):
        from app.models.auth import User
        from app.models.credit import CreditOrder
        if model is CreditOrder:
            return FakeQuery(self._order)
        if model is User:
            return FakeQuery(self._user)
        return FakeQuery(None)

    def commit(self):
        self.commits += 1


# ---- tiers ----
def test_tiers_endpoint_returns_four_tiers():
    app = FastAPI()
    app.include_router(payment_router)
    client = TestClient(app)
    resp = client.get("/api/v1/payment/tiers")
    assert resp.status_code == 200
    tiers = resp.json()["tiers"]
    assert len(tiers) == 4
    assert tiers[0]["amount_fen"] == 600


# ---- sign / verify ----
def test_sign_verify_roundtrip():
    priv, pub = _keypair()
    params = {"app_id": "x", "biz_content": "{}", "charset": "utf-8"}
    params["sign"] = payment_service.sign(params, priv)
    assert payment_service.verify(params, pub) is True


def test_verify_rejects_tampered_payload():
    priv, pub = _keypair()
    params = {"out_trade_no": "T1", "total_amount": "6.00"}
    params["sign"] = payment_service.sign(params, priv)
    params["total_amount"] = "9999.00"  # tamper after signing
    assert payment_service.verify(params, pub) is False


def test_verify_false_without_sign():
    _, pub = _keypair()
    assert payment_service.verify({"a": "1"}, pub) is False


# ---- create returns 503 when unconfigured ----
def test_create_returns_503_when_not_configured(monkeypatch):
    monkeypatch.setattr(payment_service, "load_config", lambda: None)
    app = FastAPI()
    app.include_router(payment_router)
    app.dependency_overrides[get_current_user] = lambda: FakeUser()
    app.dependency_overrides[get_db] = lambda: FakeDB(None, None)
    client = TestClient(app)
    resp = client.post("/api/v1/payment/alipay/create", json={"amount_fen": 600})
    assert resp.status_code == 503


def test_create_rejects_invalid_amount(monkeypatch):
    app = FastAPI()
    app.include_router(payment_router)
    app.dependency_overrides[get_current_user] = lambda: FakeUser()
    app.dependency_overrides[get_db] = lambda: FakeDB(None, None)
    client = TestClient(app)
    resp = client.post("/api/v1/payment/alipay/create", json={"amount_fen": 777})
    assert resp.status_code == 400


# ---- balance ----
def test_balance_endpoint_returns_user_credits():
    app = FastAPI()
    app.include_router(credits_router)
    app.dependency_overrides[get_current_user] = lambda: FakeUser(credits=123)
    client = TestClient(app)
    resp = client.get("/api/v1/credits/balance")
    assert resp.status_code == 200
    assert resp.json()["credits"] == 123


# ---- grant idempotency ----
def test_grant_credits_adds_once_then_noop():
    user = FakeUser(credits=10)
    order = FakeOrder(credits=60, status="pending")
    db = FakeDB(order, user)
    assert payment_service.grant_credits(db, "T1", "alitrade1") is True
    assert user.credits == 70
    assert order.status == "paid"
    # second notification for same order must not double-credit
    assert payment_service.grant_credits(db, "T1") is False
    assert user.credits == 70


def test_grant_credits_false_when_order_missing():
    db = FakeDB(None, FakeUser())
    assert payment_service.grant_credits(db, "missing") is False
