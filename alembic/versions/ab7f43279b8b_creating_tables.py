"""Creating tables

Revision ID: ab7f43279b8b
Revises: 2ad5a3959821
Create Date: 2022-06-18 19:38:47.953744

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab7f43279b8b'
down_revision = '2ad5a3959821'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('channel',
    sa.Column('ch_id', sa.String(length=10), nullable=False),
    sa.Column('disp_name', sa.String(length=80), nullable=False),
    sa.Column('disp_name_l', sa.String(length=80), nullable=False),
    sa.Column('icon', sa.String(length=80), nullable=True),
    sa.PrimaryKeyConstraint('ch_id'),
    sa.UniqueConstraint('disp_name'),
    sa.UniqueConstraint('disp_name_l')
    )
    op.create_table('m3u_users',
    sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=False),
    sa.Column('email', sa.String(length=50), nullable=False),
    sa.Column('password', sa.String(length=80), nullable=True),
    sa.Column('creation_date', sa.DateTime(), nullable=False),
    sa.Column('disabled', sa.String(length=1), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('name')
    )
    op.create_table('telebot_users',
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('first_name', sa.String(length=30), nullable=False),
    sa.Column('shift', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('chat_id')
    )
    op.create_table('programme',
    sa.Column('id', sa.Integer(), sa.Identity(always=True), nullable=False),
    sa.Column('channel', sa.String(length=10), nullable=True),
    sa.Column('pstart', sa.DateTime(), nullable=False),
    sa.Column('pstop', sa.DateTime(), nullable=False),
    sa.Column('title', sa.String(length=400), nullable=True),
    sa.Column('pdesc', sa.String(length=1500), nullable=True),
    sa.Column('cat', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['channel'], ['channel.ch_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('programme')
    op.drop_table('telebot_users')
    op.drop_table('m3u_users')
    op.drop_table('channel')
    # ### end Alembic commands ###
