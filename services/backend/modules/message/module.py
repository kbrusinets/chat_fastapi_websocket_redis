import asyncio
from typing import List

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from services.backend.modules.base import ModuleWithDb
from services.backend.modules.message.schemas import MessagesPagination, MessageFull
from services.db.models import Message


class MessageModule(ModuleWithDb):
    async def get_messages(self,
                           chat_id: int,
                           user_id: int | None = None,
                           limit: int = 100,
                           offset: int = 0) -> List[Message]:
        query = (
            select(Message)
            .where(
                Message.chat_id == chat_id
            )
            .order_by(Message.id.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(Message.user))
        )
        if user_id is not None:
            query = query.where(Message.user_id == user_id)

        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            messages = result.scalars().all()
            sess.expunge_all()
        return messages

    async def get_count(self,
                        chat_id: int,
                        user_id: int | None = None) -> int:
        query = (
            select(func.count(Message.id))
            .where(Message.chat_id == chat_id)
        )
        if user_id is not None:
            query = query.where(Message.user_id == user_id)

        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            count = result.scalar_one()
        return count

    async def get_messages_with_pagination_data(self,
                                                chat_id: int,
                                                user_id: int | None = None,
                                                limit: int = 100,
                                                offset: int = 0) -> MessagesPagination:
        messages, count = await asyncio.gather(
            self.get_messages(chat_id=chat_id, user_id=user_id, limit=limit, offset=offset),
            self.get_count(chat_id=chat_id, user_id=user_id)
        )
        return MessagesPagination(
            messages=[MessageFull.model_validate(message) for message in messages],
            limit=limit,
            offset=offset,
            total_count=count
        )

    async def store_message(self,
                            chat_id: int,
                            user_id: int,
                            content: str) -> Message:
        new_message = Message(
            chat_id=chat_id,
            user_id=user_id,
            content=content
        )
        async with self.db.session_scope() as sess:
            sess.add(new_message)
            await sess.commit()
            await sess.refresh(new_message)
            sess.expunge_all()
        return new_message
