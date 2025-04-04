"""Initial migration

Revision ID: b2b5ef6d7efd
Revises: 
Create Date: 2025-03-28 21:16:18.599028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2b5ef6d7efd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chat',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('type', sa.Enum('GROUP', 'PRIVATE', name='chattypeenum'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('token_blacklist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('chat_participant',
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chat.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('chat_id', 'user_id')
    )
    op.create_table('message',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.String(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chat.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('read_progress',
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('last_read_message_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chat.id'], ),
    sa.ForeignKeyConstraint(['last_read_message_id'], ['message.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('chat_id', 'user_id')
    )
    # ### end Alembic commands ###
    op.execute("""
        INSERT INTO "user" (name, email, password) 
        VALUES 
        ('first_user', 'first@example.com', '$2b$12$9y2PgXLdUOCdN0crMNGCquu5A0mD03SgvEcRtw0b3IyGkFmT.6Fcu'), 
        ('second_user', 'second@example.com', '$2b$12$9y2PgXLdUOCdN0crMNGCquu5A0mD03SgvEcRtw0b3IyGkFmT.6Fcu'), 
        ('third_user', 'third@example.com', '$2b$12$9y2PgXLdUOCdN0crMNGCquu5A0mD03SgvEcRtw0b3IyGkFmT.6Fcu') 
        ON CONFLICT DO NOTHING;
        """)
    op.execute("""
        INSERT INTO chat (name, type) 
        VALUES 
        ('private_chat', 'PRIVATE'),
        ('admin_chat', 'GROUP')
        ON CONFLICT DO NOTHING;
        """)
    op.execute("""
        INSERT INTO chat_participant (chat_id, user_id) 
        VALUES (1, 1), (1, 2), (2, 1), (2, 2), (2, 3) 
        ON CONFLICT DO NOTHING;
        """)
    op.execute("""
        INSERT INTO message (id, chat_id, user_id, content) 
        VALUES 
        (-1, 1, 1, 'Service message')
        ON CONFLICT DO NOTHING;
        """)
    op.execute("""
        INSERT INTO read_progress (chat_id, user_id, last_read_message_id) 
        VALUES 
        (1, 1, -1),
        (1, 2, -1),
        (2, 1, -1),
        (2, 2, -1),
        (2, 3, -1) 
        ON CONFLICT DO NOTHING;
        """)
    op.execute("""
        CREATE OR REPLACE FUNCTION check_private_chat_participants()
        RETURNS TRIGGER AS $$
        BEGIN
          IF (SELECT type FROM chat WHERE id = NEW.chat_id) = 'PRIVATE' THEN
            IF (SELECT COUNT(*) FROM chat_participant WHERE chat_id = NEW.chat_id) >= 2 THEN
              RAISE EXCEPTION 'Private chat cannot have more than 2 participants';
            END IF;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER prevent_private_chat_overflow
        BEFORE INSERT ON chat_participant
        FOR EACH ROW
        EXECUTE FUNCTION check_private_chat_participants();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###

    op.execute('DROP TRIGGER prevent_private_chat_overflow ON chat_participant')
    op.execute('DROP FUNCTION check_private_chat_participants()')
    op.drop_table('read_progress')
    op.drop_table('message')
    op.drop_table('chat_participant')
    op.drop_table('user')
    op.drop_table('token_blacklist')
    op.drop_table('chat')
    op.execute('DROP TYPE chattypeenum')
    # ### end Alembic commands ###
