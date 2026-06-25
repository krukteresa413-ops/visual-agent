"""add is_canonical to brand_profiles

Revision ID: c3d8e1a5f7b2
Revises: a7c9e2f4b6d1
Create Date: 2026-06-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d8e1a5f7b2'
down_revision: Union[str, None] = 'a7c9e2f4b6d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('brand_profiles', sa.Column('is_canonical', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.create_index('uq_brand_canonical_per_tenant', 'brand_profiles', ['tenant_id'], unique=True,
                    postgresql_where=sa.text('is_canonical'))


def downgrade() -> None:
    op.drop_index('uq_brand_canonical_per_tenant', table_name='brand_profiles')
    op.drop_column('brand_profiles', 'is_canonical')
