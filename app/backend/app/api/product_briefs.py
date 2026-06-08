from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.crud_project import get_project
from app.db.crud_product_brief import (
    create_product_brief,
    get_product_brief_by_project,
    get_product_brief,
    update_product_brief,
    delete_product_brief,
)
from app.schemas.product_brief import (
    ProductBriefCreate,
    ProductBriefUpdate,
    ProductBriefOut,
)


router = APIRouter(tags=["product-briefs"])


@router.post("/projects/{project_id}/brief", response_model=ProductBriefOut)
def api_create_product_brief(
    project_id: int,
    brief_create: ProductBriefCreate,
    db: Session = Depends(get_db),
):
    project = get_project(db, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing_brief = get_product_brief_by_project(db, project_id)

    if existing_brief:
        raise HTTPException(
            status_code=409,
            detail="Product brief already exists for this project",
        )

    try:
        return create_product_brief(db, project_id, brief_create)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/projects/{project_id}/brief", response_model=ProductBriefOut)
def api_get_product_brief_by_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = get_project(db, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    brief = get_product_brief_by_project(db, project_id)

    if not brief:
        raise HTTPException(status_code=404, detail="Product brief not found")

    return brief


@router.patch("/product-briefs/{brief_id}", response_model=ProductBriefOut)
def api_update_product_brief(
    brief_id: int,
    brief_update: ProductBriefUpdate,
    db: Session = Depends(get_db),
):
    brief = update_product_brief(db, brief_id, brief_update)

    if not brief:
        raise HTTPException(status_code=404, detail="Product brief not found")

    return brief


@router.delete("/product-briefs/{brief_id}")
def api_delete_product_brief(
    brief_id: int,
    db: Session = Depends(get_db),
):
    brief = delete_product_brief(db, brief_id)

    if not brief:
        raise HTTPException(status_code=404, detail="Product brief not found")

    return {
        "deleted": True,
        "brief_id": brief_id,
    }
