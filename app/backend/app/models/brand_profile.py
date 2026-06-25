from app.models.project import Project  # FK resolution
import json
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, String, Boolean, text
from app.db.session import Base

class BrandProfile(Base):
    __tablename__ = 'brand_profiles'
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    is_canonical = Column(Boolean, server_default=text("false"), nullable=False)
    name = Column(String(200), nullable=False)
    primary_color = Column(String(20), nullable=True)
    secondary_color = Column(String(20), nullable=True)
    accent_color = Column(String(20), nullable=True)
    font_style = Column(String(100), nullable=True)
    tone_of_voice = Column(String(500), nullable=True)
    visual_keywords = Column(Text, nullable=True)
    forbidden_words = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    tagline = Column(String(500), nullable=True)
    brand_story = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def visual_keywords_list(self) -> list:
        return json.loads(self.visual_keywords) if self.visual_keywords else []
    @property
    def forbidden_words_list(self) -> list:
        return json.loads(self.forbidden_words) if self.forbidden_words else []
    def to_prompt_context(self) -> str:
        parts = [f'品牌: {self.name}']
        if self.primary_color: parts.append(f'主色: {self.primary_color}')
        if self.secondary_color: parts.append(f'辅色: {self.secondary_color}')
        if self.font_style: parts.append(f'字体风格: {self.font_style}')
        if self.tone_of_voice: parts.append(f'语调: {self.tone_of_voice}')
        if self.visual_keywords: parts.append(f'视觉关键词: {" ".join(self.visual_keywords_list)}')
        if self.forbidden_words: parts.append(f'禁用词: {" ".join(self.forbidden_words_list)}')
        return '\n'.join(parts)
