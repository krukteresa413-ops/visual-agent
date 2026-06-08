from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.crud_project import (
    create_project,
    get_projects,
    get_project,
    update_project,
    delete_project,
)
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut)
def api_create_project(
    project_create: ProjectCreate,
    db: Session = Depends(get_db),
):
    return create_project(db, project_create)


@router.get("", response_model=List[ProjectOut])
def api_get_projects(
    db: Session = Depends(get_db),
):
    return get_projects(db)


@router.get("/{project_id}", response_model=ProjectOut)
def api_get_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = get_project(db, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def api_update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
):
    project = update_project(db, project_id, project_update)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.delete("/{project_id}")
def api_delete_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = delete_project(db, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "deleted": True,
        "project_id": project_id,
    }
