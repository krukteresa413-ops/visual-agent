"""Phase C.2 (收紧约束): 开启一项目多画布。

- canvas_states: 去掉 project_id 的 UNIQUE(改普通索引); canvas_id 升为 NOT NULL + UNIQUE(权威键)。
- chat_conversations: 去掉 UNIQUE(tenant_id, project_id); canvas_id 升为 NOT NULL + UNIQUE。

前置(C.1 已回填 + 已验证): 两表 canvas_id 无 NULL、无重复。此迁移后一个 project 可挂多张
canvas,各自 1 行 state / 1 行 chat。**不可逆点**: 一旦建了第 2 张 canvas, downgrade 里
恢复 project_id UNIQUE 会失败(设计已知)。

Revision ID: b2c3d4e5f6a7
Revises: a7b8c9d0e1f2
Create Date: 2026-07-01 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # canvas_states: project_id 去唯一(保留普通索引), canvas_id → NOT NULL + UNIQUE
    op.drop_index("ix_canvas_states_project_id", table_name="canvas_states")
    op.create_index("ix_canvas_states_project_id", "canvas_states", ["project_id"], unique=False)
    op.alter_column("canvas_states", "canvas_id", existing_type=sa.Integer(), nullable=False)
    op.drop_index("ix_canvas_states_canvas_id", table_name="canvas_states")
    op.create_index("ix_canvas_states_canvas_id", "canvas_states", ["canvas_id"], unique=True)

    # chat_conversations: 去 uq(tenant,project), canvas_id → NOT NULL + UNIQUE
    op.drop_constraint("uq_chat_conv_tenant_project", "chat_conversations", type_="unique")
    op.alter_column("chat_conversations", "canvas_id", existing_type=sa.Integer(), nullable=False)
    op.drop_index("ix_chat_conversations_canvas_id", table_name="chat_conversations")
    op.create_index("ix_chat_conversations_canvas_id", "chat_conversations", ["canvas_id"], unique=True)


def downgrade() -> None:
    # 反向(仅在尚未产生"一项目多画布"数据时可干净回退; 有 2+ canvas 时 project_id UNIQUE 会失败)
    op.drop_index("ix_chat_conversations_canvas_id", table_name="chat_conversations")
    op.create_index("ix_chat_conversations_canvas_id", "chat_conversations", ["canvas_id"], unique=False)
    op.alter_column("chat_conversations", "canvas_id", existing_type=sa.Integer(), nullable=True)
    op.create_unique_constraint(
        "uq_chat_conv_tenant_project", "chat_conversations", ["tenant_id", "project_id"]
    )
    op.drop_index("ix_canvas_states_canvas_id", table_name="canvas_states")
    op.create_index("ix_canvas_states_canvas_id", "canvas_states", ["canvas_id"], unique=False)
    op.alter_column("canvas_states", "canvas_id", existing_type=sa.Integer(), nullable=True)
    op.drop_index("ix_canvas_states_project_id", table_name="canvas_states")
    op.create_index("ix_canvas_states_project_id", "canvas_states", ["project_id"], unique=True)
