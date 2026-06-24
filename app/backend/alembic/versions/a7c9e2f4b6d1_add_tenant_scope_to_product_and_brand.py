"""add tenant scope to product and brand profiles

Revision ID: a7c9e2f4b6d1
Revises: fd356e49d601
Create Date: 2026-06-24 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7c9e2f4b6d1"
down_revision: Union[str, Sequence[str], None] = "fd356e49d601"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("product_briefs", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_index("ix_product_briefs_tenant_id", "product_briefs", ["tenant_id"], unique=False)
    op.create_index("ix_product_briefs_tenant_product_name", "product_briefs", ["tenant_id", "product_name"], unique=False)
    op.alter_column("product_briefs", "project_id", existing_type=sa.Integer(), nullable=True)

    op.add_column("brand_profiles", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_index("ix_brand_profiles_tenant_id", "brand_profiles", ["tenant_id"], unique=False)

    op.execute("""
        UPDATE product_briefs
        SET tenant_id = (SELECT id FROM tenants WHERE slug = 'muyuanjia' LIMIT 1)
        WHERE tenant_id IS NULL
    """)
    op.execute("""
        UPDATE brand_profiles
        SET tenant_id = (SELECT id FROM tenants WHERE slug = 'muyuanjia' LIMIT 1)
        WHERE tenant_id IS NULL
    """)


def downgrade() -> None:
    op.drop_index("ix_brand_profiles_tenant_id", table_name="brand_profiles")
    op.drop_column("brand_profiles", "tenant_id")

    op.drop_index("ix_product_briefs_tenant_product_name", table_name="product_briefs")
    op.drop_index("ix_product_briefs_tenant_id", table_name="product_briefs")
    op.drop_column("product_briefs", "tenant_id")
    op.alter_column("product_briefs", "project_id", existing_type=sa.Integer(), nullable=False)
