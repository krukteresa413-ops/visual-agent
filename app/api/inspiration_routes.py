from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix='/api/v1/inspiration', tags=['inspiration'])

class InspirationQuery(BaseModel):
    query: str
    product_name: Optional[str] = ''
    category: Optional[str] = ''

@router.post('/search')
async def search(req: InspirationQuery):
    from app.services.inspiration_search import search_inspiration
    results = await search_inspiration(req.query, req.product_name, req.category)
    return {'results': results}
