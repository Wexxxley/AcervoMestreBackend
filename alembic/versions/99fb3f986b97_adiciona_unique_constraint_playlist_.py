"""adiciona_unique_constraint_playlist_ordem

Revision ID: 99fb3f986b97
Revises: f1a2b3c4d5e6
Create Date: 2025-12-15 10:50:46.376534

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '99fb3f986b97'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Adiciona constraint única para garantir que cada playlist tenha ordens únicas
    op.create_unique_constraint(
        'uq_playlist_ordem_per_playlist',
        'PlaylistRecurso',
        ['playlist_id', 'ordem']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove a constraint única
    op.drop_constraint(
        'uq_playlist_ordem_per_playlist',
        'PlaylistRecurso',
        type_='unique'
    )
