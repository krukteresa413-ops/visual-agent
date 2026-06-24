from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.project import Project
from app.models.product_brief import ProductBrief
from app.services.product_library import _upsert_product_brief


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Project.__table__.create(bind=engine)
    ProductBrief.__table__.create(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_same_tenant_same_product_updates_existing_row():
    db = make_db()

    _upsert_product_brief(
        db,
        tenant_id=1,
        brief={
            "product_name": "商务跑鞋",
            "category": "鞋服",
            "selling_points": "轻量",
        },
    )
    _upsert_product_brief(
        db,
        tenant_id=1,
        brief={
            "product_name": "商务跑鞋",
            "category": "商务鞋",
            "selling_points": "防滑",
        },
    )

    rows = db.query(ProductBrief).filter(ProductBrief.tenant_id == 1).all()
    assert len(rows) == 1
    assert rows[0].category == "商务鞋"
    assert rows[0].selling_points == "防滑"


def test_same_product_name_isolated_by_tenant():
    db = make_db()

    _upsert_product_brief(db, tenant_id=1, brief={"product_name": "同名商品", "category": "A"})
    _upsert_product_brief(db, tenant_id=2, brief={"product_name": "同名商品", "category": "B"})

    rows = db.query(ProductBrief).order_by(ProductBrief.tenant_id).all()
    assert len(rows) == 2
    assert [row.tenant_id for row in rows] == [1, 2]
    assert [row.category for row in rows] == ["A", "B"]


def test_missing_product_name_skips_and_logs_warning(caplog):
    db = make_db()

    with caplog.at_level(logging.WARNING):
        result = _upsert_product_brief(db, tenant_id=1, brief={"category": "鞋服"})

    assert result is None
    assert db.query(ProductBrief).count() == 0
    assert "product_name" in caplog.text
