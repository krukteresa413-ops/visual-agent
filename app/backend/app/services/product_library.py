"""Tenant-scoped product library persistence helpers."""
from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.auth import Tenant
from app.models.product_brief import ProductBrief
from app.models.project import Project

logger = logging.getLogger(__name__)

_PRODUCT_FIELDS = (
    "category",
    "specifications",
    "materials",
    "selling_points",
    "target_market",
    "target_customer",
    "usage_scenarios",
    "brand_style",
    "compliance_notes",
)


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _upsert_product_brief(db: Session, tenant_id: int | None, brief: dict) -> ProductBrief | None:
    """Create or update a product brief by (tenant_id, product_name)."""
    product_name = (brief or {}).get("product_name")
    if not product_name or not str(product_name).strip():
        logger.warning("Skip product library upsert: missing product_name")
        return None

    product_name = str(product_name).strip()
    row = (
        db.query(ProductBrief)
        .filter(ProductBrief.tenant_id == tenant_id, ProductBrief.product_name == product_name)
        .first()
    )
    if row is None:
        row = ProductBrief(
            tenant_id=tenant_id,
            project_id=brief.get("project_id"),
            product_name=product_name,
            category=_as_text(brief.get("category")) or "",
        )
        db.add(row)

    for field in _PRODUCT_FIELDS:
        value = brief.get(field)
        if field == "category":
            setattr(row, field, _as_text(value) or "")
        else:
            setattr(row, field, _as_text(value))

    db.commit()
    db.refresh(row)
    return row


def _default_tenant_id(db: Session) -> int | None:
    tenant = db.query(Tenant).filter(Tenant.slug == "muyuanjia").first()
    return tenant.id if tenant else None


def upsert_product_brief_for_project(db: Session, project_id: int | None, brief: dict) -> ProductBrief | None:
    """Resolve project tenant with muyuanjia fallback, then upsert product brief."""
    tenant_id = None
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
        tenant_id = project.tenant_id if project else None
    if tenant_id is None:
        tenant_id = _default_tenant_id(db)
    payload = dict(brief or {})
    payload.setdefault("project_id", project_id)
    return _upsert_product_brief(db, tenant_id, payload)
