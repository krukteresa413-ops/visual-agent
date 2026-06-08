"""Brief parse API route — PRD 8.1"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/brief", tags=["brief"])


class BriefParseRequest(BaseModel):
    text: str


class BriefReviewRequest(BaseModel):
    """追问请求：提交文本或已解析的 brief。"""
    text: Optional[str] = None
    parsed_brief: Optional[dict] = None


@router.post("/parse")
async def parse_brief(req: BriefParseRequest):
    """PRD 8.1：从自由文本提取产品资料"""
    from app.services.brief_parser import parse_brief_text

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")

    try:
        result = await parse_brief_text(req.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.post("/review")
async def review_brief(req: BriefReviewRequest):
    """PRD 8.2：检测 brief 完整性，生成追问。

    接受两种输入：
    1. text: 自由文本 → 先解析再检测
    2. parsed_brief: 已解析的 brief dict → 直接检测

    返回：
    - complete: bool — brief 是否完整
    - questions: list — 追问列表（complete=false 时）
    - parsed_brief: dict — 解析后的 brief（text 模式时）
    """
    from app.services.brief_reviewer import BriefReviewer

    parsed = req.parsed_brief

    if req.text and req.text.strip():
        from app.services.brief_parser import parse_brief_text
        try:
            parsed = await parse_brief_text(req.text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")

    if parsed is None:
        raise HTTPException(status_code=400, detail="请提供 text 或 parsed_brief")

    questions = BriefReviewer.generate_questions(parsed)

    return {
        "complete": len(questions) == 0,
        "questions": questions,
        "parsed_brief": parsed,
    }


class BriefSaveRequest(BaseModel):
    project_id: int
    brief: dict

@router.post('/save')
def save_brief(req: BriefSaveRequest, db = None):
    from app.db.session import SessionLocal
    from app.models.product_brief import ProductBrief as PBModel
    import json
    db2 = SessionLocal()
    try:
        record = PBModel(project_id=req.project_id, brief_json=json.dumps(req.brief, ensure_ascii=False))
        db2.add(record); db2.commit(); db2.refresh(record)
        return {'id':record.id,'project_id':req.project_id,'message':'Brief saved'}
    finally: db2.close()

@router.get('/project/{project_id}')
def get_project_brief(project_id: int):
    from app.db.session import SessionLocal
    from app.models.product_brief import ProductBrief as PBModel
    import json
    db = SessionLocal()
    try:
        r = db.query(PBModel).filter(PBModel.project_id == project_id).order_by(PBModel.created_at.desc()).first()
        if not r: return {'project_id':project_id,'brief':None}
        return {'id':r.id,'project_id':project_id,'brief':json.loads(r.brief_json)}
    finally: db.close()
