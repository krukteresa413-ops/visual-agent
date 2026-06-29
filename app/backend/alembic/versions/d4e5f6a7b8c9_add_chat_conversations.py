"""add chat_conversations table (图三 对话持久化, tenant-scoped)

Revision ID: d4e5f6a7b8c9
Revises: b1f2a3c4d5e6
Create Date: 2026-06-29 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "b1f2a3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("messages", sa.Text(), server_default="[]", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "project_id", name="uq_chat_conv_tenant_project"),
    )
    op.create_index("ix_chat_conversations_id", "chat_conversations", ["id"], unique=False)
    op.create_index("ix_chat_conversations_tenant_id", "chat_conversations", ["tenant_id"], unique=False)
    op.create_index("ix_chat_conversations_project_id", "chat_conversations", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_chat_conversations_project_id", table_name="chat_conversations")
    op.drop_index("ix_chat_conversations_tenant_id", table_name="chat_conversations")
    op.drop_index("ix_chat_conversations_id", table_name="chat_conversations")
    op.drop_table("chat_conversations")
