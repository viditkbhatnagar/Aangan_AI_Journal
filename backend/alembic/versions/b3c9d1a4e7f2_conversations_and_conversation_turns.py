"""baithak: conversations and conversation_turns

Revision ID: b3c9d1a4e7f2
Revises: 705d3c2fe806
Create Date: 2026-07-28 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'b3c9d1a4e7f2'
down_revision = '705d3c2fe806'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('circle_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('last_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['circle_id'], ['family_circles.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'])
    op.create_table(
        'conversation_turns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('snippet_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_conversation_turns_conversation_id'), 'conversation_turns', ['conversation_id']
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_conversation_turns_conversation_id'), table_name='conversation_turns')
    op.drop_table('conversation_turns')
    op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
    op.drop_table('conversations')
