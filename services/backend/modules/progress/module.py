from sqlalchemy import select, and_, func

from services.backend.modules.base import ModuleWithDb
from services.db.models import Message, ReadProgress


class ProgressModule(ModuleWithDb):
    async def get_user_unread_in_chat(self, chat_id: int, user_id: int, until_mess_id: int | None = None) -> bool:
        query = (
            select(func.count())
            .select_from(Message)
            .where(
                and_(
                    Message.id > (
                        select(ReadProgress.last_read_message_id)
                        .where(
                            and_(
                                ReadProgress.chat_id == chat_id,
                                ReadProgress.user_id == user_id
                            )
                        ).scalar_subquery()
                    ),
                    Message.chat_id == chat_id,
                    Message.user_id != user_id
                )
            )
        )
        if until_mess_id is not None:
            query = query.where(Message.id <= until_mess_id)
        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            unread = result.scalar_one_or_none()
            sess.expunge_all()
        return unread

    async def get_chat_progress(self, chat_id):
        query = (
            select(
                func.min(ReadProgress.last_read_message_id)
            ).where(
                ReadProgress.chat_id == chat_id
            )
        )
        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            progress = result.scalar_one_or_none()
            sess.expunge_all()
        if progress is None:
            return -1
        else:
            return progress
