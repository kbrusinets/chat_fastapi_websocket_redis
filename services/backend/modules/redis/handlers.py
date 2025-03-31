from abc import ABC, abstractmethod

from services.app.logger import logger
from services.app.schemas import ServerWsMessage, ServerChatMessage, ServerNewUserMessage, ServerUserLeftMessage, \
    ServerChatProgress, ServerUserProgress, WsMessageType, RedisChannelType
from services.backend.modules.websocket.interface import IWebsocketModule


class RedisMessageHandler(ABC):
    @abstractmethod
    async def __call__(self, ws_module: IWebsocketModule, type: RedisChannelType, message: ServerWsMessage) -> None:
        ...

class NewMessageHandler(RedisMessageHandler):
    async def __call__(self, ws_module: IWebsocketModule, type: RedisChannelType, message: ServerChatMessage) -> None:
        if type == RedisChannelType.CHAT:
            await ws_module.broadcast_to_chat(chat_id=message.chat_id, message=message.model_dump_json())
        elif type == RedisChannelType.USER:
            logger.error(f'Unknown behaviour: {message.model_dump_json()}')
        else:
            logger.error(f'Unknown behaviour: {message.model_dump_json()}')

class NewUserHandler(RedisMessageHandler):
    async def __call__(self, ws_module: IWebsocketModule, type: RedisChannelType, message: ServerNewUserMessage) -> None:
        if type == RedisChannelType.CHAT:
            await ws_module.broadcast_to_chat(chat_id=message.chat_id, message=message.model_dump_json(), skip_users={message.user_id, })
        elif type == RedisChannelType.USER:
            await ws_module.store_user_chat_relation(chat_id=message.chat_id, user_id=message.user_id)
            await ws_module.broadcast_to_user(user_id=message.user_id, message=message.model_dump_json())
        else:
            logger.error(f'Unknown behaviour: {message.model_dump_json()}')

class UserLeftHandler(RedisMessageHandler):
    async def __call__(self, ws_module: IWebsocketModule, type: RedisChannelType, message: ServerUserLeftMessage) -> None:
        if type == RedisChannelType.CHAT:
            await ws_module.broadcast_to_chat(chat_id=message.chat_id, message=message.model_dump_json(), skip_users={message.user_id, })
        elif type == RedisChannelType.USER:
            await ws_module.remove_user_chat_relation(chat_id=message.chat_id, user_id=message.user_id)
            await ws_module.broadcast_to_user(user_id=message.user_id, message=message.model_dump_json())
        else:
            logger.error(f'Unknown behaviour: {message.model_dump_json()}')

class ChatProgressHandler(RedisMessageHandler):
    async def __call__(self, ws_module: IWebsocketModule, type: RedisChannelType, message: ServerChatProgress) -> None:
        if type == RedisChannelType.CHAT:
            await ws_module.broadcast_to_chat(chat_id=message.chat_id, message=message.model_dump_json())
        elif type == RedisChannelType.USER:
            logger.error('Unknown behaviour')
        else:
            logger.error(f'Unknown behaviour: {message.model_dump_json()}')

class UserProgressHandler(RedisMessageHandler):
    async def __call__(self, ws_module: IWebsocketModule, type: RedisChannelType, message: ServerUserProgress) -> None:
        if type == RedisChannelType.CHAT:
            logger.error('Unknown behaviour')
        elif type == RedisChannelType.USER:
            await ws_module.broadcast_to_user(user_id=message.user_id, message=message.model_dump_json())
        else:
            logger.error(f'Unknown behaviour: {message.model_dump_json()}')

def get_handler(message_type: WsMessageType) -> RedisMessageHandler | None:
    handlers: dict[WsMessageType, RedisMessageHandler] = {
        WsMessageType.MESSAGE: NewMessageHandler(),
        WsMessageType.NEW_USER: NewUserHandler(),
        WsMessageType.USER_LEFT: UserLeftHandler(),
        WsMessageType.CHAT_PROGRESS: ChatProgressHandler(),
        WsMessageType.USER_PROGRESS: UserProgressHandler()
    }
    return handlers.get(message_type, None)
