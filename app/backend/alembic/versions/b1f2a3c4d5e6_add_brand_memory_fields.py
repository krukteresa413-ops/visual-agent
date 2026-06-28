"""add brand memory fields to brand_profiles (借零件#4: PRD 7.6/12.2)

新增可跨项目复用的品牌记忆字段:target_audience / product_images / memory_summary。
全部 nullable,纯增量,可 downgrade 回滚。

Revision ID: b1f2a3c4d5e6
Revises: c3d8e1a5f7b2
Create Date: 2026-06-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1f2a3c4d5e6'
down_revision: Union[str, None] = 'c3d8e1a5f7b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('brand_profiles', sa.Column('target_audience', sa.String(length=500), nullable=True))
    op.add_column('brand_profiles', sa.Column('product_images', sa.Text(), nullable=True))
    op.add_column('brand_profiles', sa.Column('memory_summary', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('brand_profiles', 'memory_summary')
    op.drop_column('brand_profiles', 'product_images')
    op.drop_column('brand_profiles', 'target_audience')
