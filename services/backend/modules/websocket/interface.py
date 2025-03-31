from abc import ABC, abstractmethod
from typing import Set


class IWebsocketModule(ABC):
    @abstractmethod
    async def broadcast_to_chat(self, chat_id: int, message: str, skip_users: Set | None = None) -> None:
        ...

    @abstractmethod
    async def broadcast_to_user(self, user_id: int, message: str) -> None:
        ...

    @abstractmethod
    async def store_user_chat_relation(self, chat_id: int, user_id: int) -> None:
        ...

    @abstractmethod
    async def remove_user_chat_relation(self, chat_id: int, user_id: int) -> None:
        ...
