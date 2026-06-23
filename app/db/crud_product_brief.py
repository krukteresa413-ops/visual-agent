from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.product_brief import ProductBrief
from app.schemas.product_brief import ProductBriefCreate, ProductBriefUpdate


def create_product_brief(
    db: Session,
    project_id: int,
    brief_create: ProductBriefCreate,
) -> ProductBrief:
    db_brief = ProductBrief(
        project_id=project_id,
        **brief_create.model_dump(),
    )

    try:
        db.add(db_brief)
        db.commit()
        db.refresh(db_brief)
        return db_brief
    except IntegrityError as e:
        db.rollback()
        if "duplicate key" in str(e):
            raise ValueError(f"Product brief already exists for project {project_id}")
        raise
    except SQLAlchemyError:
        db.rollback()
        raise


def get_product_brief_by_project(db: Session, project_id: int):
    return (
        db.query(ProductBrief)
        .filter(ProductBrief.project_id == project_id)
        .first()
    )


def get_product_brief(db: Session, brief_id: int):
    return (
        db.query(ProductBrief)
        .filter(ProductBrief.id == brief_id)
        .first()
    )


def update_product_brief(
    db: Session,
    brief_id: int,
    brief_update: ProductBriefUpdate,
):
    db_brief = get_product_brief(db, brief_id)

    if not db_brief:
        return None

    update_data = brief_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_brief, key, value)

    try:
        db.commit()
        db.refresh(db_brief)
        return db_brief
    except SQLAlchemyError:
        db.rollback()
        raise


def delete_product_brief(db: Session, brief_id: int):
    db_brief = get_product_brief(db, brief_id)

    if not db_brief:
        return None

    try:
        db.delete(db_brief)
        db.commit()
        return db_brief
    except SQLAlchemyError:
        db.rollback()
        raise
