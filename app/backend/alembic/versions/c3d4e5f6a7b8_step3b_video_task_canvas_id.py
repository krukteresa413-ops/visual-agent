"""Phase C Step 3b: add nullable canvas_id to video_tasks

异步视频任务要落回"发起时的那张画布",而非项目默认画布。给 video_tasks 加一个
可空 canvas_id —— 与既有 project_id 同风格(普通 Integer + 索引, 无 FK; video_tasks
本就不对 projects 建 FK)。worker 落画布时按 task.canvas_id 经 resolve_canvas 解析;
缺省(None)→回退项目默认画布(旧行为不变)。纯加法、可回退。

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-01 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("video_tasks", sa.Column("canvas_id", sa.Integer(), nullable=True))
    op.create_index("ix_video_tasks_canvas_id", "video_tasks", ["canvas_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_video_tasks_canvas_id", table_name="video_tasks")
    op.drop_column("video_tasks", "canvas_id")
