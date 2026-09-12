"""Align unique indexes with SQLAlchemy metadata.

Revision ID: 0002_align_unique_indexes
Revises: 0001_initial
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_align_unique_indexes"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_constraint("uq_auth_sessions_token_hash", "auth_sessions", type_="unique")
    op.drop_constraint("uq_creator_profiles_slug", "creator_profiles", type_="unique")
    op.drop_constraint("uq_provider_profiles_slug", "provider_profiles", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("uq_provider_profiles_slug", "provider_profiles", ["slug"])
    op.create_unique_constraint("uq_creator_profiles_slug", "creator_profiles", ["slug"])
    op.create_unique_constraint("uq_auth_sessions_token_hash", "auth_sessions", ["token_hash"])
    op.create_unique_constraint("uq_users_email", "users", ["email"])
