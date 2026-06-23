import os, uuid
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix='/api/v1/upload', tags=['upload'])
UPLOAD_DIR = '/opt/visual-agent/uploads'
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
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath): raise HTTPException(status_code=404, detail='not found')
    os.remove(filepath)
    return {'message': f'deleted {filename}'}

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
        text = await parse_document(tmp, file.content_type)
        if not text.strip(): raise HTTPException(status_code=422, detail='无法提取文本')
        brief = await parse_brief_text(text)
        return {'filename':file.filename,'extracted_text_length':len(text),'extracted_text_preview':text[:500],'parsed_brief':brief}
    finally:
        if os.path.exists(tmp): os.remove(tmp)

@router.post('/image/remove-bg')
async def remove_image_background(file: UploadFile = File(...)):
    import uuid
    if file.content_type not in ALLOWED_IMAGE:
        raise HTTPException(status_code=400, detail='Unsupported file type')
    content = await file.read()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    input_name = f'input_{uuid.uuid4().hex[:8]}.jpg'
    output_name = f'whitebg_{uuid.uuid4().hex[:8]}.jpg'
    input_path = os.path.join(UPLOAD_DIR, input_name)
    output_path = os.path.join(UPLOAD_DIR, output_name)
    with open(input_path, 'wb') as f: f.write(content)
    try:
        from app.services.bg_remover import remove_background
        result = remove_background(input_path, output_path)
        return {'original_url': f'/uploads/{input_name}', 'white_bg_url': f'/uploads/{output_name}', 'size': result['output_size']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Background removal failed: {str(e)}')
