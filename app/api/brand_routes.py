import json, os, uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.session import SessionLocal

router = APIRouter(prefix='/api/v1/brand', tags=['brand'])

class BrandProfileCreate(BaseModel):
    project_id: Optional[int] = None
    name: str
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_style: Optional[str] = None
    tone_of_voice: Optional[str] = None
    visual_keywords: Optional[list[str]] = None
    forbidden_words: Optional[list[str]] = None

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.post('/')
def create_brand(req: BrandProfileCreate, db: Session = Depends(get_db)):
    from app.models.brand_profile import BrandProfile
    p = BrandProfile(project_id=req.project_id, name=req.name, primary_color=req.primary_color, secondary_color=req.secondary_color, accent_color=req.accent_color, font_style=req.font_style, tone_of_voice=req.tone_of_voice, visual_keywords=json.dumps(req.visual_keywords or [], ensure_ascii=False), forbidden_words=json.dumps(req.forbidden_words or [], ensure_ascii=False))
    db.add(p); db.commit(); db.refresh(p)
    return {'id': p.id, 'name': p.name}

@router.get('/project/{project_id}')
def get_brand(project_id: int, db: Session = Depends(get_db)):
    from app.models.brand_profile import BrandProfile
    p = db.query(BrandProfile).filter(BrandProfile.project_id == project_id).first()
    if not p: return {'brand': None}
    return {'id': p.id, 'name': p.name, 'primary_color': p.primary_color, 'secondary_color': p.secondary_color, 'accent_color': p.accent_color, 'font_style': p.font_style, 'tone_of_voice': p.tone_of_voice, 'visual_keywords': p.visual_keywords_list, 'forbidden_words': p.forbidden_words_list, 'logo_url': p.logo_url}

@router.post('/{brand_id}/logo')
async def upload_logo(brand_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    from app.models.brand_profile import BrandProfile
    p = db.query(BrandProfile).filter(BrandProfile.id == brand_id).first()
    if not p: raise HTTPException(status_code=404, detail='Not found')
    upload_dir = '/opt/visual-agent/uploads'
    os.makedirs(upload_dir, exist_ok=True)
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'png'
    filename = f'logo_{uuid.uuid4().hex[:8]}.{ext}'
    with open(os.path.join(upload_dir, filename), 'wb') as f: f.write(await file.read())
    p.logo_url = f'/uploads/{filename}'; db.commit()
    return {'logo_url': p.logo_url}
