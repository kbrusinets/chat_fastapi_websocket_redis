from sqlalchemy import select

from services.backend.modules.base import ModuleWithDb
from services.db.models import User


class UserModule(ModuleWithDb):
    async def get_user(self, user_id: int) -> User | None:
        query = (
            select(User)
            .where(
                User.id == user_id
            )
        )
        async with self.db.session_scope() as sess:
            result = await sess.execute(query)
            user = result.scalar_one_or_none()
            sess.expunge_all()
        return user
