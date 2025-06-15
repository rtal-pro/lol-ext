"""Update spell range to BIGINT

Revision ID: 002
Revises: 001_initial_schema
Create Date: 2025-06-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Update the spells.range column to use ARRAY(BIGINT) instead of ARRAY(Integer)
    op.alter_column('spells', 'range',
                    type_=ARRAY(BIGINT),
                    existing_type=ARRAY(sa.Integer()),
                    postgresql_using='range::bigint[]')
    
    # Also update the summoner_spells.range column for consistency
    op.alter_column('summoner_spells', 'range',
                    type_=ARRAY(BIGINT),
                    existing_type=ARRAY(sa.Integer()),
                    postgresql_using='range::bigint[]')


def downgrade():
    # Note: Downgrading might cause data loss if values exceed Integer range
    op.alter_column('spells', 'range',
                    type_=ARRAY(sa.Integer()),
                    existing_type=ARRAY(BIGINT),
                    postgresql_using='range::integer[]')
    
    op.alter_column('summoner_spells', 'range',
                    type_=ARRAY(sa.Integer()),
                    existing_type=ARRAY(BIGINT),
                    postgresql_using='range::integer[]')