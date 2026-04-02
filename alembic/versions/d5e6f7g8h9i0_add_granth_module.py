"""add granth module tables

Revision ID: d5e6f7g8h9i0
Revises: c4d5e6f7g8h9
Create Date: 2025-01-01 00:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d5e6f7g8h9i0"
down_revision: Union[str, None] = "c4d5e6f7g8h9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "granths",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("language", sa.String(50), nullable=False, server_default="punjabi"),
        sa.Column("total_pages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("uploaded_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "granth_pages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("granth_id", sa.String(), sa.ForeignKey("granths.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_granth_pages_granth_id", "granth_pages", ["granth_id"])

    op.create_table(
        "user_granth_progress",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("granth_id", sa.String(), sa.ForeignKey("granths.id", ondelete="CASCADE"), nullable=False),
        sa.Column("current_page", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_granth_progress_user_id", "user_granth_progress", ["user_id"])
    op.create_index("ix_user_granth_progress_granth_id", "user_granth_progress", ["granth_id"])


def downgrade() -> None:
    op.drop_table("user_granth_progress")
    op.drop_table("granth_pages")
    op.drop_table("granths")
