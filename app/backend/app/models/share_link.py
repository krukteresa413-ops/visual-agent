"""ShareLink：画布「真·分享」——冻结快照 + 免登录只读 token 链接。

Phase S（自包含，不改现有 canvas/chat 模型）：分享时把该 project 当前画布
(elements/connections/viewport) 冻结成 snapshot_json 存一行；`GET /share/{token}`
免登录返回快照，前端 `/share/:token` 只读渲染。scope 预留（v1 只做 public）。
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.db.session import Base


class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(Integer, primary_key=True, index=True)
    # 不可猜测的能力令牌(uuid4 hex);持有链接即可只读查看
    token = Column(String(64), unique=True, index=True, nullable=False)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 冗余租户/创建者用于审计与后续「仅同公司可见」收紧
    tenant_id = Column(Integer, nullable=True, index=True)
    created_by = Column(Integer, nullable=True)
    # 'public' = 任何持链者只读;预留 'tenant' 收紧(v1 未实现)
    scope = Column(String(20), nullable=False, default="public")
    title = Column(String(255), nullable=True)
    # 冻结快照 JSON: {"canvas": {"elements":[...],"connections":[...],"viewport":{...}}, "meta": {...}}
    snapshot_json = Column(Text, nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
