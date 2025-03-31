from contextlib import asynccontextmanager
from functools import lru_cache
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from services.app.logger import logger
from services.app.settings import settings


class Db:
    def __init__(self, url):
        self.engine = create_async_engine(url, pool_size=50, max_overflow=100, pool_recycle=60 * 10)
        self.serializable_mode = self.engine.execution_options(isolation_level='SERIALIZABLE')
        self.session_maker = async_sessionmaker(bind=self.engine, class_=AsyncSession)

    @asynccontextmanager
    async def session_scope(self) -> AsyncIterator[AsyncSession]:
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
                await session.close()
            except Exception as e:
                logger.exception(e)
                await session.rollback()
                await session.close()
                raise

    @asynccontextmanager
    async def serializable_session_scope(self) -> AsyncIterator[AsyncSession]:
        async with self.session_maker(bind=self.serializable_mode) as session:
            try:
                yield session
                await session.commit()
                await session.close()
            except Exception as e:
                logger.exception(e)
                await session.rollback()
                await session.close()
                raise


@lru_cache
def get_db():
    url = settings.get_db_url()
    return Db(url=url)
