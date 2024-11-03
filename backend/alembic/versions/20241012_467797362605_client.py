"""Client

Revision ID: 467797362605
Revises: 
Create Date: 2024-10-12 00:33:23.731623

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '467797362605'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('clients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('login', sa.String(length=20), nullable=True),
    sa.Column('password', sa.String(length=20), nullable=True),
    sa.Column('vk_id', sa.String(length=20), nullable=True),
    sa.Column('name', sa.String(length=20), nullable=True),
    sa.Column('surname', sa.String(length=20), nullable=True),
    sa.Column('telephone', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=20), nullable=True),
    sa.Column('creation_date', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clients_id'), 'clients', ['id'], unique=False)
    op.create_table('auth_user',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('login', sa.String(length=20), nullable=False),
    sa.Column('hashed_password', sa.String(length=64), nullable=True),
    sa.Column('role', sa.Enum('OrgLeaderRole', 'ClientRole', 'OrgManagerRole', 'ProductManagerRole', 'SuperUserRole', name='userrole'), nullable=True),
    sa.Column('client_id', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('creation_date', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auth_user_id'), 'auth_user', ['id'], unique=False)
    op.create_index(op.f('ix_auth_user_login'), 'auth_user', ['login'], unique=False)
    op.create_table('auth_refresh_session',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('refresh_token', sa.UUID(), nullable=False),
    sa.Column('expires_in', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['auth_user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auth_refresh_session_id'), 'auth_refresh_session', ['id'], unique=False)
    op.create_index(op.f('ix_auth_refresh_session_refresh_token'), 'auth_refresh_session', ['refresh_token'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_auth_refresh_session_refresh_token'), table_name='auth_refresh_session')
    op.drop_index(op.f('ix_auth_refresh_session_id'), table_name='auth_refresh_session')
    op.drop_table('auth_refresh_session')
    op.drop_index(op.f('ix_auth_user_login'), table_name='auth_user')
    op.drop_index(op.f('ix_auth_user_id'), table_name='auth_user')
    op.drop_table('auth_user')
    op.drop_index(op.f('ix_clients_id'), table_name='clients')
    op.drop_table('clients')
    # ### end Alembic commands ###
