"""add brand_profiles table"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'ded8d2c88855'
down_revision: Union[str, Sequence[str], None] = 'c8656e0dcad6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('brand_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('primary_color', sa.String(20), nullable=True),
        sa.Column('secondary_color', sa.String(20), nullable=True),
        sa.Column('accent_color', sa.String(20), nullable=True),
        sa.Column('font_style', sa.String(100), nullable=True),
        sa.Column('tone_of_voice', sa.String(500), nullable=True),
        sa.Column('visual_keywords', sa.Text(), nullable=True),
        sa.Column('forbidden_words', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'],),
        sa.PrimaryKeyConstraint('id'),
    )

def downgrade() -> None:
    op.drop_table('brand_profiles')
