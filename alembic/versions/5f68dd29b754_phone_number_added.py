"""phone number added

Revision ID: 5f68dd29b754
Revises: 
Create Date: 2025-03-11 23:37:09.849173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f68dd29b754'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(), nullable=True)
)


def downgrade() -> None:
    pass
