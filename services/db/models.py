from datetime import datetime
from typing import Set, List

from sqlalchemy import Integer, String, ForeignKey, Enum, DateTime, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from services.app.schemas import ChatTypeEnum


class Base(DeclarativeBase):
    pass


class ChatParticipant(Base):
    __tablename__ = 'chat_participant'

    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey('chat.id'), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), primary_key=True)


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    chats: Mapped[Set['Chat']] = relationship(secondary='chat_participant', back_populates='users')
    messages: Mapped[List['Message']] = relationship(back_populates='user')


class Chat(Base):
    __tablename__ = 'chat'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[ChatTypeEnum] = mapped_column(Enum(ChatTypeEnum), nullable=False)

    users: Mapped[Set['User']] = relationship(secondary='chat_participant', back_populates='chats')
    messages: Mapped[List['Message']] = relationship(back_populates='chat')


class Message(Base):
    __tablename__ = 'message'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey('chat.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                server_default=text("(now() at time zone 'utc')"))

    chat: Mapped['Chat'] = relationship(back_populates='messages')
    user: Mapped['User'] = relationship(back_populates='messages')


class ReadProgress(Base):
    __tablename__ = 'read_progress'

    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey('chat.id'), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), primary_key=True)
    last_read_message_id: Mapped[int] = mapped_column(Integer, ForeignKey('message.id'), nullable=False)

    chat: Mapped['Chat'] = relationship()
    user: Mapped['User'] = relationship()
    message: Mapped['Message'] = relationship()


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
