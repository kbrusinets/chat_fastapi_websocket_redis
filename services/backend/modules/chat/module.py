from typing import List

from sqlalchemy import select, and_, delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.orm import selectinload

from services.app.exceptions import EntityAlreadyExistsError, InvalidOperationError
from services.app.schemas import ChatTypeEnum
from services.backend.modules.base import ModuleWithDb
from services.db.models import Chat, ChatParticipant, User, ReadProgress, Message


class ChatModule(ModuleWithDb):
    async def get_chat(self, chat_id: int) -> Chat | None:
        query = (
            select(Chat)
            .where(
                Chat.id == chat_id
            )
        )
        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            chat = result.scalar_one_or_none()
            sess.expunge_all()
        return chat

    async def create_chat(self, name: str, type: ChatTypeEnum) -> Chat:
        new_chat = Chat(
            name=name,
            type=type
        )
        async with self.db.session_scope() as sess:
            try:
                sess.add(new_chat)
                await sess.commit()
                await sess.refresh(new_chat)
                sess.expunge_all()
            except IntegrityError:
                raise EntityAlreadyExistsError(
                    message='Chat already exists',
                    name='ChatModule'
                )
        return new_chat

    async def check_user_in_chat(self, chat_id: int, user_id: int) -> bool:
        query = (
            select(ChatParticipant)
            .where(
                and_(
                    ChatParticipant.chat_id == chat_id,
                    ChatParticipant.user_id == user_id
                )
            )
        )
        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            chat_participant = result.scalar_one_or_none()
            sess.expunge_all()
        return bool(chat_participant)

    async def add_user_to_chat(self, chat_id: int, user_id: int) -> Message:
        new_chat_participant = ChatParticipant(
            chat_id=chat_id,
            user_id=user_id
        )
        new_message = Message(
            chat_id=chat_id,
            user_id=user_id,
            content='I joined!'
        )
        async with self.db.session_scope() as sess:
            try:
                sess.add(new_chat_participant)
                sess.add(new_message)
                await sess.flush()
                initial_progress = ReadProgress(
                    chat_id=chat_id,
                    user_id=user_id,
                    last_read_message_id=new_message.id
                )
                sess.add(initial_progress)
                await sess.commit()
                await sess.refresh(new_message)
                sess.expunge_all()
            except IntegrityError as e:
                sql_error_message = str(e.orig)
                raise EntityAlreadyExistsError(
                    message=f'Error while creating the new chat - {sql_error_message}',
                    name='ChatModule'
                )
            except DBAPIError as e:
                sql_error_message = str(e.orig)
                raise InvalidOperationError(
                    message=f'Error while creating the new chat - {sql_error_message}',
                    name='ChatModule'
                )
        return new_message

    async def delete_user_from_chat(self, chat_id: int, user_id: int) -> Message:
        query_1 = (
            delete(ChatParticipant)
            .where(
                and_(
                    ChatParticipant.chat_id == chat_id,
                    ChatParticipant.user_id == user_id
                )
            )
        )
        query_2 = (
            delete(ReadProgress)
            .where(
                and_(
                    ReadProgress.chat_id == chat_id,
                    ReadProgress.user_id == user_id
                )
            )
        )
        new_message = Message(
            chat_id=chat_id,
            user_id=user_id,
            content='I left!'
        )
        async with self.db.session_scope() as sess:
            sess.add(new_message)
            await sess.execute(query_1)
            await sess.execute(query_2)
            await sess.commit()
            await sess.refresh(new_message)
            sess.expunge_all()
        return new_message

    async def get_user_chats(self, user_id: int) -> List[Chat]:
        query = (
            select(Chat)
            .where(Chat.users.any(User.id == user_id))
        )
        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            chats = result.scalars().all()
            sess.expunge_all()
        return chats

    async def get_all_chats(self) -> List[Chat]:
        query = (
            select(Chat)
        )
        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            chats = result.scalars().all()
            sess.expunge_all()
        return chats

    async def get_chat_users_read_progress(self, chat_id: int) -> List[ReadProgress]:
        query = (
            select(ReadProgress)
            .where(ReadProgress.chat_id == chat_id)
        )
        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            progress = result.scalars().all()
            sess.expunge_all()
        return progress

    async def get_chat_user_read_progress(self, chat_id: int, user_id: int) -> ReadProgress | None:
        query = (
            select(ReadProgress)
            .where(
                and_(
                    ReadProgress.chat_id == chat_id,
                    ReadProgress.user_id == user_id
                )
            )
        )
        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            progress = result.scalar_one_or_none()
            sess.expunge_all()
        return progress

    async def get_chat_users(self, chat_id: int) -> List[User]:
        query = (
            select(Chat)
            .where(
                Chat.id == chat_id
            )
            .options(selectinload(Chat.users))
        )
        async with self.db.session_scope() as sess:
            chat = await sess.execute(query)
            chat = chat.scalar_one_or_none()
            users = chat.users if chat else []
            users = sorted(users, key=lambda x: x.id)
            sess.expunge_all()
        return users

    async def store_chat_user_read_progress(self,
                                            chat_id: int,
                                            user_id: int,
                                            last_read_message_id: int) -> ReadProgress | None:
        query = (
            insert(ReadProgress)
            .values(chat_id=chat_id, user_id=user_id, last_read_message_id=last_read_message_id)
            .on_conflict_do_update(
                index_elements=['chat_id', 'user_id'],
                set_={'last_read_message_id': func.greatest(ReadProgress.last_read_message_id, last_read_message_id)})
            .returning(ReadProgress)
        )
        async with self.db.serializable_session_scope() as sess:
            result = await sess.execute(query)
            progress = result.scalar_one_or_none()
            sess.expunge_all()
        return progress
