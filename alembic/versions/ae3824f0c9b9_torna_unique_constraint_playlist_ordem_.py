"""torna_unique_constraint_playlist_ordem_deferrable

Revision ID: ae3824f0c9b9
Revises: 99fb3f986b97
Create Date: 2025-12-15 18:15:45.128280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'ae3824f0c9b9'
down_revision: Union[str, Sequence[str], None] = '99fb3f986b97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Substitui a constraint por uma versão DEFERRABLE para permitir atualizações
    # que temporariamente violam a unicidade dentro da mesma transação.
    # Execute statements separately to avoid prepared-statement restrictions
    op.execute("ALTER TABLE \"PlaylistRecurso\" DROP CONSTRAINT IF EXISTS uq_playlist_ordem_per_playlist")
    op.execute(
        "ALTER TABLE \"PlaylistRecurso\" ADD CONSTRAINT uq_playlist_ordem_per_playlist UNIQUE (playlist_id, ordem) DEFERRABLE INITIALLY DEFERRED"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Recria a constraint como não-deferrable padrão
    op.execute("ALTER TABLE \"PlaylistRecurso\" DROP CONSTRAINT IF EXISTS uq_playlist_ordem_per_playlist")
    op.execute(
        "ALTER TABLE \"PlaylistRecurso\" ADD CONSTRAINT uq_playlist_ordem_per_playlist UNIQUE (playlist_id, ordem)"
    )
