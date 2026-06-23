"""PRD 9 — 结构化错误响应"""
from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: str = "INTERNAL_ERROR"
