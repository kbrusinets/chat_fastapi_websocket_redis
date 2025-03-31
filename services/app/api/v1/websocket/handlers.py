from abc import ABC, abstractmethod

from fastapi import WebSocket
from pydantic import ValidationError

from services.app.schemas import UserChatMessage, ServerChatMessage, WsMessageType, UserChatProgress, \
    ServerChatProgress, ServerUserProgress, RedisChannelType
from services.backend.module import Backend
from services.db.models import User, ReadProgress


class WebSocketHandler(ABC):
    @abstractmethod
    async def __call__(self, backend: Backend, user: User, websocket: WebSocket, message: dict):
        pass


class NewMessageHandler(WebSocketHandler):
    async def __call__(self, backend: Backend, user: User, websocket: WebSocket, message: dict):
        try:
            message = UserChatMessage(**message)
        except ValidationError:
            raise
        cur_chat_progress = await backend.progress_module.get_chat_progress(chat_id=message.chat_id)
        new_message = await backend.message_module.store_message(
            chat_id=message.chat_id,
            user_id=user.id,
            content=message.content
        )
        await backend.chat_module.store_chat_user_read_progress(
            chat_id=new_message.chat_id, user_id=user.id, last_read_message_id=new_message.id)
        new_chat_progress = await backend.progress_module.get_chat_progress(chat_id=message.chat_id)

        await backend.redis_module.publish(
            type=RedisChannelType.CHAT,
            key=message.chat_id,
            message=ServerChatMessage(
                type=WsMessageType.MESSAGE,
                user_id=user.id,
                chat_id=message.chat_id,
                content=message.content,
                message_id=new_message.id
            ))
        await backend.redis_module.publish(
            type=RedisChannelType.USER,
            key=user.id,
            message=ServerUserProgress(
                type=WsMessageType.USER_PROGRESS,
                user_id=user.id,
                chat_id=message.chat_id,
                last_read_message_id=new_message.id
            )
        )
        if not cur_chat_progress or new_chat_progress > cur_chat_progress:
            await backend.redis_module.publish(
                type=RedisChannelType.CHAT,
                key=message.chat_id,
                message=ServerChatProgress(
                    type=WsMessageType.CHAT_PROGRESS,
                    chat_id=message.chat_id,
                    last_read_message_id=new_chat_progress
                )
            )

class ProgressHandler(WebSocketHandler):
    async def __call__(self, backend: Backend, user: User, websocket: WebSocket, message: dict):
        try:
            message = UserChatProgress(**message)
        except ValidationError:
            raise
        cur_chat_progress = await backend.progress_module.get_chat_progress(chat_id=message.chat_id)
        progress: ReadProgress = await backend.chat_module.store_chat_user_read_progress(
            chat_id=message.chat_id, user_id=user.id, last_read_message_id=message.last_read_message_id)
        new_chat_progress = await backend.progress_module.get_chat_progress(chat_id=message.chat_id)
        await backend.redis_module.publish(
            type=RedisChannelType.USER,
            key=user.id,
            message=ServerUserProgress(
                type=WsMessageType.USER_PROGRESS,
                user_id=user.id,
                chat_id=message.chat_id,
                last_read_message_id=progress.last_read_message_id
            )
        )
        if not cur_chat_progress or new_chat_progress > cur_chat_progress:
            await backend.redis_module.publish(
                type=RedisChannelType.CHAT,
                key=message.chat_id,
                message=ServerChatProgress(
                    type=WsMessageType.CHAT_PROGRESS,
                    chat_id=message.chat_id,
                    last_read_message_id=new_chat_progress
                )
            )

def get_handler(message_type: WsMessageType) -> WebSocketHandler | None:
    handlers: dict[WsMessageType, WebSocketHandler] = {
        WsMessageType.MESSAGE: NewMessageHandler(),
        WsMessageType.USER_PROGRESS: ProgressHandler()
    }
    return handlers.get(message_type, None)
