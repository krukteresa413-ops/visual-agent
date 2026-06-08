from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.session import SessionLocal

router = APIRouter(prefix='/api/v1/projects', tags=['projects'])

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get('/')
def list_projects(db: Session = Depends(get_db)):
    from app.models.project import Project
    from app.models.visual_asset import VisualAsset
    from sqlalchemy import func
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    result = []
    for p in projects:
        count = db.query(func.count(VisualAsset.id)).filter(VisualAsset.project_id == p.id).scalar()
        result.append({'id': p.id, 'name': p.name, 'description': p.description,
            'created_at': p.created_at.isoformat() if p.created_at else None, 'generation_count': count or 0})
    return result

@router.post('/')
def create_project(req: ProjectCreate, db: Session = Depends(get_db)):
    from app.models.project import Project
    p = Project(name=req.name, description=req.description)
    db.add(p); db.commit(); db.refresh(p)
    return {'id': p.id, 'name': p.name, 'description': p.description}

@router.get('/{project_id}')
def get_project(project_id: int, db: Session = Depends(get_db)):
    from app.models.project import Project
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p: raise HTTPException(status_code=404, detail='Project not found')
    return p

@router.delete('/{project_id}')
def delete_project(project_id: int, db: Session = Depends(get_db)):
    from app.models.project import Project
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p: raise HTTPException(status_code=404, detail='Project not found')
    db.delete(p); db.commit()
    return {'message': f'Project {project_id} deleted'}

@router.get('/{project_id}/generations')
def list_generations(project_id: int, db: Session = Depends(get_db)):
    from app.db.crud_visual_asset_v2 import list_by_project
    records = list_by_project(db=db, project_id=project_id, limit=20)
    return [{'id': r.id, 'model_used': r.model_used, 'generation_seconds': r.generation_seconds,
        'created_at': r.created_at.isoformat() if r.created_at else None} for r in records]
