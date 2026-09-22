"""add property image_url

Revision ID: eba73bf36d75
Revises: 750cfb3fb197
Create Date: 2026-09-22 16:14:07.865211

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "eba73bf36d75"
down_revision: Union[str, Sequence[str], None] = "750cfb3fb197"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column("image_url", sa.String(length=500), nullable=False, server_default=""),
    )
    op.alter_column("properties", "image_url", server_default=None)


def downgrade() -> None:
    op.drop_column("properties", "image_url")
