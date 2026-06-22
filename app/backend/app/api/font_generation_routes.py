"""Font generation API routes."""
from fastapi import APIRouter, Query
from typing import Optional

from app.models.font_generation_model import (
    FontGenerationRequest,
    FontGenerationResponse,
    FontHistoryResponse,
)
from app.services.font_generation_service import font_generation_service


router = APIRouter(prefix="/api/v1", tags=["font-generation"])


@router.post("/font-generate", response_model=FontGenerationResponse, status_code=202)
async def generate_font(request: FontGenerationRequest) -> FontGenerationResponse:
    """Generate font images from text.
    
    Phase 1: Uses Mige API image model for fast interaction validation.
    Phase 2: Will switch to zi2zi-JiT local deployment.
    
    Returns task_id for async tracking (currently executes synchronously for MVP).
    """
    return await font_generation_service.generate_font(request)


@router.get("/font-history", response_model=FontHistoryResponse)
async def get_font_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status: pending, processing, completed, failed"),
) -> FontHistoryResponse:
    """Get paginated font generation history."""
    result = font_generation_service.get_history(
        page=page,
        page_size=page_size,
        status=status,
    )
    return FontHistoryResponse(**result)
