from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.models.auth import Tenant
from app.models.brand_profile import BrandProfile
from app.models.product_brief import ProductBrief
from app.models.project import Project
from app.api.library_routes import router


@pytest.fixture
def db_session(tmp_path):
    db_path = tmp_path / "library.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Tenant.__table__.create(bind=engine)
    Project.__table__.create(bind=engine)
    ProductBrief.__table__.create(bind=engine)
    BrandProfile.__table__.create(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def seed_library(db):
    tenant_a = Tenant(id=1, name="Tenant A", slug="tenant-a")
    tenant_b = Tenant(id=2, name="Tenant B", slug="tenant-b")
    default_tenant = Tenant(id=5, name="沐源甲科技", slug="muyuanjia")
    db.add_all([tenant_a, tenant_b, default_tenant])
    db.add_all([
        ProductBrief(
            tenant_id=1,
            project_id=None,
            product_name="商务跑鞋",
            category="鞋服",
            specifications="轻量鞋底",
            materials="网布",
            selling_points=json.dumps(["轻量", "防滑"], ensure_ascii=False),
            target_market="企业礼品",
            target_customer="商务人士",
            usage_scenarios="通勤",
            brand_style="简洁专业",
            compliance_notes="无",
        ),
        ProductBrief(
            tenant_id=2,
            project_id=None,
            product_name="商务跑鞋",
            category="隔离鞋服",
            selling_points="B 租户卖点",
        ),
    ])
    db.add(
        BrandProfile(
            tenant_id=1,
            project_id=None,
            name="Tenant A Brand",
            primary_color="#111111",
            secondary_color="#eeeeee",
            accent_color="#ff6900",
            tone_of_voice="专业可信",
            forbidden_words=json.dumps(["廉价"], ensure_ascii=False),
        )
    )
    db.commit()


def test_list_products_by_tenant(client, db_session):
    seed_library(db_session)

    resp = client.get("/api/v1/library/products?tenant_id=1")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["product_name"] == "商务跑鞋"
    assert data[0]["category"] == "鞋服"
    assert "轻量" in data[0]["selling_points"]


def test_get_product_detail_returns_complete_brief(client, db_session):
    seed_library(db_session)
    product_id = db_session.query(ProductBrief).filter(ProductBrief.tenant_id == 1).first().id

    resp = client.get(f"/api/v1/library/product/{product_id}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["product_name"] == "商务跑鞋"
    assert data["specifications"] == "轻量鞋底"
    assert data["target_customer"] == "商务人士"
    assert data["brand_style"] == "简洁专业"


def test_get_brand_by_tenant(client, db_session):
    seed_library(db_session)

    resp = client.get("/api/v1/library/brand?tenant_id=1")

    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Tenant A Brand"
    assert data["primary_color"] == "#111111"
    assert data["secondary_color"] == "#eeeeee"
    assert data["accent_color"] == "#ff6900"
    assert data["tone_of_voice"] == "专业可信"
    assert data["forbidden_words"] == ["廉价"]


def test_tenant_isolation_for_products(client, db_session):
    seed_library(db_session)

    resp = client.get("/api/v1/library/products?tenant_id=2")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["category"] == "隔离鞋服"
    assert data[0]["tenant_id"] == 2
