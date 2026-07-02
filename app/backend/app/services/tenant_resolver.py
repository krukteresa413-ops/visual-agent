"""Resolve a project's tenant_id for OSS 多租户 storage 分区（Phase O1）。

第一性：storage key 需要 (tenant_id, project_id)，而 tenant_id 是 project_id 的纯函数
(Project.tenant_id)。与其把可推导的 tenant_id 穿过 生成/字体/画布/视频 每一层，不如在靠近
落盘处集中派生一次。本模块刻意保持极小、只吃 int、按需 import DB/models，避免 import 环。

缺 project_id / 项目已删 / 任何异常 → None → storage 归 shared/（合法降级；O3 收紧）。
"""
from __future__ import annotations

from typing import Optional


def resolve_tenant_id(project_id: Optional[int], db=None) -> Optional[int]:
    """按 project_id 查 Project.tenant_id。传入 db 则复用（如 worker 已有 session），
    否则自开一个短会话。任何失败静默降级为 None（分区退化不该拖垮生成/出片）。"""
    if not project_id:
        return None
    own = db is None
    if own:
        from app.db.session import SessionLocal
        db = SessionLocal()
    try:
        from app.models.project import Project
        proj = db.query(Project).filter(Project.id == int(project_id)).first()
        return proj.tenant_id if proj else None
    except Exception:
        return None
    finally:
        if own:
            db.close()
