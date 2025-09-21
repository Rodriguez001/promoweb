"""Add exchange rate table

Revision ID: 003_add_exchange_rate_table
Revises: 002_shipping_analytics_tables
Create Date: 2024-09-21 17:47:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_exchange_rate_table'
down_revision = '002_shipping_analytics_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create exchange_rates table
    op.create_table(
        'exchange_rates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_currency', sa.String(length=3), nullable=False),
        sa.Column('to_currency', sa.String(length=3), nullable=False),
        sa.Column('rate', sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for efficient queries
    op.create_index(
        'idx_exchange_rate_currencies_date',
        'exchange_rates',
        ['from_currency', 'to_currency', 'date'],
        unique=False
    )
    
    # Create index on date for time-based queries
    op.create_index(
        'idx_exchange_rates_date',
        'exchange_rates',
        ['date'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_exchange_rates_date', table_name='exchange_rates')
    op.drop_index('idx_exchange_rate_currencies_date', table_name='exchange_rates')
    
    # Drop table
    op.drop_table('exchange_rates')
