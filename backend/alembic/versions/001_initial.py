"""Initial migration: Create users, games, rounds, and actions tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-07-27 06:40:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=100), nullable=False),
        sa.Column('chips_balance', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # 2. Create Games Table
    op.create_table(
        'games',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('deck_state', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_games_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_games'))
    )
    op.create_index(op.f('ix_games_id'), 'games', ['id'], unique=False)

    # 3. Create Rounds Table
    op.create_table(
        'rounds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('bet', sa.Integer(), nullable=False),
        sa.Column('insurance_bet', sa.Integer(), nullable=True),
        sa.Column('player_hands', sa.JSON(), nullable=False),
        sa.Column('dealer_hand', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='playing'),
        sa.Column('outcome', sa.String(length=50), nullable=True),
        sa.Column('payout', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], name=op.f('fk_rounds_game_id_games'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_rounds'))
    )
    op.create_index(op.f('ix_rounds_id'), 'rounds', ['id'], unique=False)

    # 4. Create Actions Table
    op.create_table(
        'actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('round_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=20), nullable=False),
        sa.Column('hand_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('card_drawn', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['round_id'], ['rounds.id'], name=op.f('fk_actions_round_id_rounds'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_actions'))
    )
    op.create_index(op.f('ix_actions_id'), 'actions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_actions_id'), table_name='actions')
    op.drop_table('actions')
    op.drop_index(op.f('ix_rounds_id'), table_name='rounds')
    op.drop_table('rounds')
    op.drop_index(op.f('ix_games_id'), table_name='games')
    op.drop_table('games')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
