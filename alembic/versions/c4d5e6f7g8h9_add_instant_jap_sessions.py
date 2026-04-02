"""add instant jap sessions

Revision ID: c4d5e6f7g8h9
Revises: b3c4d5e6f7g8
Create Date: 2025-01-01 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7g8h9"
down_revision: Union[str, None] = "b3c4d5e6f7g8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "instant_jap_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target", sa.Integer(), nullable=False, server_default="108"),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_instant_jap_sessions_owner_id", "instant_jap_sessions", ["owner_id"])
    op.create_index("ix_instant_jap_sessions_session_date", "instant_jap_sessions", ["session_date"])


def downgrade() -> None:
    op.drop_index("ix_instant_jap_sessions_session_date")
    op.drop_index("ix_instant_jap_sessions_owner_id")
    op.drop_table("instant_jap_sessions")
