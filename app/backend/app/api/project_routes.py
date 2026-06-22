from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.session import SessionLocal
from app.models.auth import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix='/api/v1/projects', tags=['projects'])

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def _can_access_project(current_user: User, project) -> bool:
    if current_user.role == 'platform_admin':
        return True
    return project.tenant_id == current_user.tenant_id

@router.get('/')
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.project import Project
    from app.models.visual_asset import VisualAsset
    from sqlalchemy import func
    query = db.query(Project)
    if current_user.role != 'platform_admin':
        query = query.filter(Project.tenant_id == current_user.tenant_id)
    projects = query.order_by(Project.created_at.desc()).all()
    result = []
    for p in projects:
        count = db.query(func.count(VisualAsset.id)).filter(VisualAsset.project_id == p.id).scalar()
        result.append({'id': p.id, 'name': p.name, 'description': p.description,
            'created_at': p.created_at.isoformat() if p.created_at else None, 'generation_count': count or 0})
    return result

@router.post('/')
def create_project(req: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.project import Project
    p = Project(name=req.name, description=req.description, tenant_id=current_user.tenant_id)
    db.add(p); db.commit(); db.refresh(p)
    return {'id': p.id, 'name': p.name, 'description': p.description}

@router.get('/{project_id}')
def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.project import Project
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p: raise HTTPException(status_code=404, detail='Project not found')
    if not _can_access_project(current_user, p): raise HTTPException(status_code=404, detail='Project not found')
    return p

@router.delete('/{project_id}')
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.project import Project
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p: raise HTTPException(status_code=404, detail='Project not found')
    if not _can_access_project(current_user, p): raise HTTPException(status_code=404, detail='Project not found')
    db.delete(p); db.commit()
    return {'message': f'Project {project_id} deleted'}
