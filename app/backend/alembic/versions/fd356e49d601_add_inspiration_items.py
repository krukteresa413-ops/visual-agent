"""add inspiration_items

Revision ID: fd356e49d601
Revises: ded8d2c88855
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'fd356e49d601'
down_revision: Union[str, Sequence[str], None] = 'ded8d2c88855'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'inspiration_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('sub_category', sa.String(100), nullable=False),
        sa.Column('preview_url', sa.String(1024), nullable=False),
        sa.Column('prompt_template', sa.Text(), nullable=False),
        sa.Column('aspect_ratio', sa.String(20), nullable=True),
        sa.Column('source', sa.String(50), nullable=True, server_default='image2_seed'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_inspiration_items_category', 'inspiration_items', ['category'])


def downgrade() -> None:
    op.drop_index('ix_inspiration_items_category', table_name='inspiration_items')
    op.drop_table('inspiration_items')
