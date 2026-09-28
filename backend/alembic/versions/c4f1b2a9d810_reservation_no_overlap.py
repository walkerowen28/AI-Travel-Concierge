"""prevent overlapping confirmed reservations

Revision ID: c4f1b2a9d810
Revises: eba73bf36d75
Create Date: 2026-09-28 09:30:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "c4f1b2a9d810"
down_revision: Union[str, Sequence[str], None] = "eba73bf36d75"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONSTRAINT = "reservations_no_overlap"


def upgrade() -> None:
    # btree_gist lets a GiST index mix equality on property_id with range overlap on dates.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        f"""
        ALTER TABLE reservations
        ADD CONSTRAINT {CONSTRAINT}
        EXCLUDE USING gist (
            property_id WITH =,
            daterange(check_in, check_out, '[)') WITH &&
        )
        WHERE (status = 'confirmed')
        """
    )


def downgrade() -> None:
    op.execute(f"ALTER TABLE reservations DROP CONSTRAINT IF EXISTS {CONSTRAINT}")
