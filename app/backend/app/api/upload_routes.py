import os, re, uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix='/api/v1/upload', tags=['upload'])
UPLOAD_DIR = '/opt/visual-agent/uploads'
SAFE_FILENAME_RE = re.compile(r'^[A-Za-z0-9_.-]+$')


def _safe_upload_path(filename: str) -> Path:
    if not filename or '/' in filename or '\\' in filename or not SAFE_FILENAME_RE.fullmatch(filename):
        raise HTTPException(status_code=400, detail='invalid filename')
    upload_root = Path(UPLOAD_DIR).resolve()
    target = (upload_root / filename).resolve()
    if target.parent != upload_root:
        raise HTTPException(status_code=400, detail='invalid filename')
    return target
ALLOWED_IMAGE = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
MAX_SIZE = 10 * 1024 * 1024

@router.post('/image')
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE:
        raise HTTPException(status_code=400, detail=f'不支持的文件类型')
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail='文件超过10MB')
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f'{uuid.uuid4().hex[:12]}.{ext}'
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, 'wb') as f: f.write(content)
    return {'filename': filename, 'url': f'/uploads/{filename}', 'size_bytes': len(content), 'content_type': file.content_type}

@router.delete('/image/{filename}')
async def delete_image(filename: str):
    filepath = _safe_upload_path(filename)
    if not filepath.exists(): raise HTTPException(status_code=404, detail='not found')
    filepath.unlink()
    return {'message': f'deleted {filename}'}

ALLOWED_VIDEO = {'video/mp4', 'video/webm', 'video/quicktime', 'video/ogg'}
MAX_VIDEO = 50 * 1024 * 1024  # 50MB

@router.post('/video')
async def upload_video(file: UploadFile = File(...)):
    # 本地视频导入:落盘到 /uploads 并返回可播放 URL(与 /image 同机制,仅放开视频类型与更大上限)。
    if file.content_type not in ALLOWED_VIDEO:
        raise HTTPException(status_code=400, detail='不支持的视频类型(仅 mp4/webm/mov/ogg)')
    content = await file.read()
    if len(content) > MAX_VIDEO:
        raise HTTPException(status_code=400, detail='视频超过50MB')
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'mp4'
    filename = f'{uuid.uuid4().hex[:12]}.{ext}'
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, 'wb') as f: f.write(content)
    return {'filename': filename, 'url': f'/uploads/{filename}', 'size_bytes': len(content), 'content_type': file.content_type}

ALLOWED_DOC = {'application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/vnd.openxmlformats-officedocument.presentationml.presentation','application/msword','application/vnd.ms-excel','application/vnd.ms-powerpoint','text/plain','text/csv'}
MAX_DOC = 20*1024*1024

@router.post('/document/parse')
async def upload_and_parse(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_DOC:
        raise HTTPException(status_code=400, detail=f'不支持的文件类型: {file.content_type}')
    content = await file.read()
    if len(content) > MAX_DOC:
        raise HTTPException(status_code=400, detail='文件超过20MB')
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    tmp = os.path.join(UPLOAD_DIR, f'doc_{uuid.uuid4().hex[:8]}.{ext}')
    with open(tmp, 'wb') as f: f.write(content)
    try:
        from app.services.document_parser import parse_document
        from app.services.brief_parser import parse_brief_text
        from app.services.text_prefilter import clean_pdf_text
        raw_text = await parse_document(tmp, file.content_type)
        if not raw_text.strip(): raise HTTPException(status_code=422, detail='无法提取文本')
        text = clean_pdf_text(raw_text)[:8000]
        brief = await parse_brief_text(text)
        return {'filename':file.filename,'extracted_text_length':len(text),'extracted_text_preview':text[:500],'parsed_brief':brief}
    finally:
        if os.path.exists(tmp): os.remove(tmp)

