"""Phase C.1 (additive): add canvases table + nullable canvas_id on
canvas_states/chat_conversations + backfill one default canvas per project.

不动旧的 UNIQUE 约束(canvas_states.project_id / chat uq_tenant_project),
以保持本迁移为纯加法、可回退、行为零变化。收紧约束在后续 C.2 迁移。

Revision ID: a7b8c9d0e1f2
Revises: d4e5f6a7b8c9
Create Date: 2026-07-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) canvases 表
    op.create_table(
        "canvases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), server_default="画布 1", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_canvases_id", "canvases", ["id"], unique=False)
    op.create_index("ix_canvases_project_id", "canvases", ["project_id"], unique=False)
    op.create_index("ix_canvases_tenant_id", "canvases", ["tenant_id"], unique=False)

    # 2) 加法列: canvas_id(可空, FK CASCADE, 索引; 暂不加 unique/not-null — 留到 C.2)
    op.add_column("canvas_states", sa.Column("canvas_id", sa.Integer(), nullable=True))
    op.add_column("chat_conversations", sa.Column("canvas_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_canvas_states_canvas_id", "canvas_states", "canvases",
        ["canvas_id"], ["id"], ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_chat_conv_canvas_id", "chat_conversations", "canvases",
        ["canvas_id"], ["id"], ondelete="CASCADE",
    )
    op.create_index("ix_canvas_states_canvas_id", "canvas_states", ["canvas_id"], unique=False)
    op.create_index("ix_chat_conversations_canvas_id", "chat_conversations", ["canvas_id"], unique=False)

    # 3) 回填: 对每个"有 canvas_state 或 chat_conversation"的 project 建一张默认画布,
    #    再把该 project 现有的 canvas_state / chat_conversation 挂到这张默认画布上。
    #    (此刻每个 project 至多 1 个 canvas_state / 1 个 chat, 故 project→canvas 1:1)
    op.execute(
        """
        INSERT INTO canvases (project_id, tenant_id, name, sort_order, created_at, updated_at)
        SELECT p.id, p.tenant_id, '画布 1', 0, now(), now()
        FROM projects p
        WHERE p.id IN (
            SELECT project_id FROM canvas_states
            UNION
            SELECT project_id FROM chat_conversations
        )
        """
    )
    op.execute(
        """
        UPDATE canvas_states cs
        SET canvas_id = c.id
        FROM canvases c
        WHERE c.project_id = cs.project_id AND cs.canvas_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE chat_conversations ch
        SET canvas_id = c.id
        FROM canvases c
        WHERE c.project_id = ch.project_id AND ch.canvas_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_chat_conversations_canvas_id", table_name="chat_conversations")
    op.drop_index("ix_canvas_states_canvas_id", table_name="canvas_states")
    op.drop_constraint("fk_chat_conv_canvas_id", "chat_conversations", type_="foreignkey")
    op.drop_constraint("fk_canvas_states_canvas_id", "canvas_states", type_="foreignkey")
    op.drop_column("chat_conversations", "canvas_id")
    op.drop_column("canvas_states", "canvas_id")
    op.drop_index("ix_canvases_tenant_id", table_name="canvases")
    op.drop_index("ix_canvases_project_id", table_name="canvases")
    op.drop_index("ix_canvases_id", table_name="canvases")
    op.drop_table("canvases")
