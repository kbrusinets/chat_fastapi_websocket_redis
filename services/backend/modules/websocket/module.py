from functools import lru_cache
from typing import Set

from fastapi import WebSocket

from services.app.logger import logger
from services.app.schemas import RedisChannelType
from services.backend.modules.redis.interface import IRedisModule
from services.backend.modules.websocket.interface import IWebsocketModule


class WebsocketModule(IWebsocketModule):
    def __init__(self):
        self.chats_to_users: dict[int, Set[int]] = {}
        self.users_to_chats: dict[int, Set[int]] = {}
        self.users: dict[int, Set[WebSocket]] = {}
        self.redis_module: IRedisModule | None = None

    def set_redis_module(self, redis_module: IRedisModule):
        self.redis_module = redis_module

    async def redis_subscribe(self, type: RedisChannelType, key: int | str):
        if not self.redis_module:
            logger.error('Websocket module: attempted to subscribe, but no redis module is set')
            return
        else:
            await self.redis_module.subscribe(type=type, key=key)

    async def redis_unsubscribe(self, type: RedisChannelType, key: int | str):
        if not self.redis_module:
            print('Websocket module: attempted to unsubscribe, but no redis module is set')
            return
        else:
            await self.redis_module.unsubscribe(type=type, key=key)

    async def connect_user(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        if user_id in self.users:
            self.users[user_id].add(websocket)
        else:
            self.users[user_id] = {websocket}
            if len(self.users) == 1:
                await self.redis_subscribe(type=RedisChannelType.USER, key=user_id)

    async def disconnect_user(self, user_id: int, websocket: WebSocket) -> None:
        user_connections = self.users.get(user_id, [])
        if user_connections:
            if websocket in user_connections:
                user_connections.remove(websocket)
            if len(user_connections) == 0:
                self.users.pop(user_id)
                if len(self.users) == 0:
                    await self.redis_unsubscribe(type=RedisChannelType.USER, key=user_id)
                user_chats = self.users_to_chats.get(user_id, []).copy()
                for chat_id in user_chats:
                    await self.remove_user_chat_relation(chat_id=chat_id, user_id=user_id)

    async def store_user_chat_relation(self, chat_id: int, user_id: int) -> None:
        if user_id in self.users:
            if chat_id in self.chats_to_users:
                self.chats_to_users[chat_id].add(user_id)
            else:
                self.chats_to_users[chat_id] = {user_id}
                if len(self.chats_to_users) == 1:
                    await self.redis_subscribe(type=RedisChannelType.CHAT, key=chat_id)
            if user_id in self.users_to_chats:
                self.users_to_chats[user_id].add(chat_id)
            else:
                self.users_to_chats[user_id] = {chat_id}

    async def remove_user_chat_relation(self, chat_id: int, user_id: int) -> None:
        if user_id in self.chats_to_users[chat_id]:
            self.chats_to_users[chat_id].remove(user_id)
            if len(self.chats_to_users[chat_id]) == 0:
                self.chats_to_users.pop(chat_id)
                if len(self.chats_to_users) == 0:
                    await self.redis_unsubscribe(type=RedisChannelType.CHAT, key=chat_id)

        if chat_id in self.users_to_chats[user_id]:
            self.users_to_chats[user_id].remove(chat_id)
            if len(self.users_to_chats[user_id]) == 0:
                self.users_to_chats.pop(user_id)

    async def broadcast_to_chat(self, chat_id: int, message: str, skip_users: Set | None = None) -> None:
        for user_id in self.chats_to_users.get(chat_id, []):
            if skip_users and user_id in skip_users:
                continue
            for ws in self.users.get(user_id, []):
                try:
                    await ws.send_text(message)
                except Exception as e:
                    print(e)
                    await self.disconnect_user(user_id=user_id, websocket=ws)

    async def broadcast_to_user(self, user_id: int, message: str) -> None:
        for ws in self.users.get(user_id, []):
            try:
                await ws.send_text(message)
            except Exception as e:
                print(e)
                await self.disconnect_user(user_id=user_id, websocket=ws)


@lru_cache
def get_ws_module() -> WebsocketModule:
    return WebsocketModule()