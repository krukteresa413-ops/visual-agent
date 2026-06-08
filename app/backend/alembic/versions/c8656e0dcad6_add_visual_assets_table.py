"""add visual_assets table

Revision ID: c8656e0dcad6
Revises:
Create Date: 2026-06-06 15:29:34.291735
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c8656e0dcad6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table("visual_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("brief_id", sa.Integer(), nullable=True),
        sa.Column("asset_plan_json", sa.Text(), nullable=False),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("generation_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["brief_id"], ["product_briefs.id"],),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_visual_assets_id"), "visual_assets", ["id"], unique=False)
    op.create_index(op.f("ix_visual_assets_project_id"), "visual_assets", ["project_id"], unique=False)

def downgrade() -> None:
    op.drop_index(op.f("ix_visual_assets_project_id"), table_name="visual_assets")
    op.drop_index(op.f("ix_visual_assets_id"), table_name="visual_assets")
    op.drop_table("visual_assets")
