from abc import ABC, abstractmethod

from services.app.schemas import RedisChannelType


class IRedisModule(ABC):
    @abstractmethod
    async def subscribe(self, type: RedisChannelType, key: int | str):
        ...

    @abstractmethod
    async def unsubscribe(self, type: RedisChannelType, key: int | str):
        ...
