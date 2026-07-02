"""Font generation service - orchestrates font image generation."""
import os
import uuid
from datetime import datetime
from typing import Optional

from app.models.font_generation_model import (
    FontGeneration,
    FontGenerationRequest,
    FontGenerationResponse,
    FontGenerationResult,
)
from app.models.image_generation_model import ImageGenerationRequest
from app.services.image_generation_service import image_generation_service
from app.db.session import SessionLocal


FONTS_DIR = "/opt/visual-agent/uploads/fonts"


class FontGenerationService:
    """Font generation service using image generation providers.
    
    Phase 1: Uses Mige API image model to generate font images.
    Phase 2: Will switch to zi2zi-JiT local deployment.
    """

    def __init__(self):
        os.makedirs(FONTS_DIR, exist_ok=True)

    async def generate_font(self, request: FontGenerationRequest) -> FontGenerationResponse:
        """Submit font generation task asynchronously.
        
        Returns task_id immediately, actual generation happens in background.
        """
        task_id = f"font_{uuid.uuid4().hex[:12]}"
        
        # Create database record
        db = SessionLocal()
        try:
            # Build prompt for image generation
            prompt = self._build_font_prompt(request.text, request.style_name)
            
            db_record = FontGeneration(
                task_id=task_id,
                text=request.text,
                style_name=request.style_name,
                status="pending",
                provider=request.provider,
                prompt=prompt,
                width=request.width,
                height=request.height,
            )
            db.add(db_record)
            db.commit()
            db.refresh(db_record)
            
            # Start async generation (fire and forget for now, will add background task later)
            # For MVP, we'll do synchronous generation
            try:
                result = await self._generate_with_provider(
                    task_id=task_id,
                    prompt=prompt,
                    provider=request.provider,
                    width=request.width,
                    height=request.height,
                    tenant_id=request.tenant_id,
                    project_id=request.project_id,
                )
                
                # Update record with result
                db_record.status = result["status"]
                db_record.image_url = result.get("image_url")
                db_record.error_message = result.get("error_message")
                db_record.generation_seconds = result.get("generation_seconds")
                db.commit()
                
            except Exception as e:
                db_record.status = "failed"
                db_record.error_message = str(e)
                db.commit()
            
            return FontGenerationResponse(
                task_id=db_record.task_id,
                status=db_record.status,
                text=db_record.text,
                style_name=db_record.style_name,
                provider=db_record.provider,
                created_at=db_record.created_at,
            )
            
        finally:
            db.close()

    async def _generate_with_provider(
        self,
        task_id: str,
        prompt: str,
        provider: str,
        width: int,
        height: int,
        tenant_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> dict:
        """Generate font image using specified provider."""
        start_time = datetime.now()
        
        if provider == "mige":
            # Phase 1 图片路径:原绑定 mige,但 mige 额度已耗尽(用户额度不足)。改走 DataEyes
            # (生产稳定 provider,画布 AI 图亦用它;默认模型 gpt-image-2),使字体生成实际可用。
            img_request = ImageGenerationRequest(
                provider="dataeyes",
                prompt=prompt,
                width=width,
                height=height,
                category="font",  # O1: 字体图落 font/ 分区
                tenant_id=tenant_id,
                project_id=project_id,
            )
            
            result = await image_generation_service.generate(img_request)
            
            if result.status == "succeeded" and result.images:
                # Save image URL (Mige returns URL directly)
                image_url = result.images[0].url
                
                generation_seconds = int((datetime.now() - start_time).total_seconds())
                
                return {
                    "status": "completed",
                    "image_url": image_url,
                    "generation_seconds": generation_seconds,
                }
            else:
                return {
                    "status": "failed",
                    "error_message": "Image generation failed",
                }
                
        elif provider == "zi2zi":
            # Phase 2: zi2zi-JiT local deployment
            # TODO: Implement zi2zi integration
            return {
                "status": "failed",
                "error_message": "zi2zi provider not yet implemented",
            }
        else:
            return {
                "status": "failed",
                "error_message": f"Unknown provider: {provider}",
            }

    def _build_font_prompt(self, text: str, style_name: Optional[str]) -> str:
        """Build prompt for font image generation."""
        if style_name:
            prompt = f"Chinese calligraphy font art, text: '{text}', style: {style_name}, high quality, artistic typography, white background"
        else:
            prompt = f"Chinese calligraphy font art, text: '{text}', elegant style, high quality, artistic typography, white background"
        
        return prompt

    def get_history(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> dict:
        """Get paginated font generation history."""
        db = SessionLocal()
        try:
            query = db.query(FontGeneration)
            
            # Filter by status if provided
            if status:
                query = query.filter(FontGeneration.status == status)
            
            # Count total
            total = query.count()
            
            # Paginate
            offset = (page - 1) * page_size
            items = query.order_by(FontGeneration.created_at.desc()).offset(offset).limit(page_size).all()
            
            # Convert to Pydantic models
            results = [FontGenerationResult.model_validate(item) for item in items]
            
            total_pages = (total + page_size - 1) // page_size
            
            return {
                "items": results,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
            
        finally:
            db.close()


# Singleton instance
font_generation_service = FontGenerationService()
