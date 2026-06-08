from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, project_create: ProjectCreate) -> Project:
    db_project = Project(
        name=project_create.name,
        tenant=project_create.tenant,
        description=project_create.description,
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project


def get_projects(db: Session):
    return db.query(Project).order_by(Project.id.desc()).all()


def get_project(db: Session, project_id: int):
    return db.query(Project).filter(Project.id == project_id).first()


def update_project(db: Session, project_id: int, project_update: ProjectUpdate):
    db_project = db.query(Project).filter(Project.id == project_id).first()

    if not db_project:
        return None

    update_data = project_update.model_dump(exclude_unset=True)

    # 当前 projects 表还没有 product_brief 字段，先跳过
    update_data.pop("product_brief", None)

    for key, value in update_data.items():
        setattr(db_project, key, value)

    db.commit()
    db.refresh(db_project)

    return db_project


def delete_project(db: Session, project_id: int):
    db_project = db.query(Project).filter(Project.id == project_id).first()

    if not db_project:
        return None

    db.delete(db_project)
    db.commit()

    return db_project
