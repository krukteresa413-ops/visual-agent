"""Tenant-scoped product and brand library read APIs."""
from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.auth import Tenant
from app.models.brand_profile import BrandProfile
from app.models.product_brief import ProductBrief

router = APIRouter(prefix="/api/v1/library", tags=["library"])

DbDep = Annotated[Session, Depends(get_db)]


def _resolve_tenant_id(db: Session, tenant_id: int | None) -> int | None:
    if tenant_id is not None:
        return tenant_id
    tenant = db.query(Tenant).filter(Tenant.slug == "muyuanjia").first()
    return tenant.id if tenant else None


def _json_list(value: str | None):
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else [str(parsed)]
    except Exception:
        return [value]


@router.get("/products")
def list_products(db: DbDep, tenant_id: Annotated[int | None, Query()] = None) -> list[dict]:
    resolved_tenant_id = _resolve_tenant_id(db, tenant_id)
    query = db.query(ProductBrief)
    if resolved_tenant_id is not None:
        query = query.filter(ProductBrief.tenant_id == resolved_tenant_id)
    rows = query.order_by(ProductBrief.updated_at.desc()).all()
    return [
        {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "product_name": row.product_name,
            "category": row.category,
            "selling_points": row.selling_points,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
        for row in rows
    ]


@router.get("/product/{product_id}")
def get_product(product_id: int, db: DbDep) -> dict:
    row = db.query(ProductBrief).filter(ProductBrief.id == product_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Product brief not found")
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "project_id": row.project_id,
        "product_name": row.product_name,
        "category": row.category,
        "specifications": row.specifications,
        "materials": row.materials,
        "selling_points": row.selling_points,
        "target_market": row.target_market,
        "target_customer": row.target_customer,
        "usage_scenarios": row.usage_scenarios,
        "brand_style": row.brand_style,
        "compliance_notes": row.compliance_notes,
    }


@router.get("/brand")
def get_brand(db: DbDep, tenant_id: Annotated[int | None, Query()] = None) -> dict:
    resolved_tenant_id = _resolve_tenant_id(db, tenant_id)
    query = db.query(BrandProfile)
    if resolved_tenant_id is not None:
        query = query.filter(BrandProfile.tenant_id == resolved_tenant_id)
    row = query.order_by(BrandProfile.updated_at.desc()).first()
    if row is None:
        return {}
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "name": row.name,
        "primary_color": row.primary_color,
        "secondary_color": row.secondary_color,
        "accent_color": row.accent_color,
        "forbidden_words": _json_list(row.forbidden_words),
        "tone_of_voice": row.tone_of_voice,
    }
