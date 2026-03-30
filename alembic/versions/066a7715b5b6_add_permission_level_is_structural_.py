"""Initial schema — create all tables

Revision ID: 066a7715b5b6
Revises: 
Create Date: 2026-03-22 03:08:14.818031

"""
from typing import Sequence, Union

from alembic import op
from app.models import Base  # noqa: F401 — registers all models

# revision identifiers, used by Alembic.
revision: str = '066a7715b5b6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all tables as defined in current models, including:
    # - entity_permissions.permission_level (permission_level_enum)
    # - entity_permissions.is_structural (boolean)
    # - meanings.visibility (visibility_enum)
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
