import enum
from enum import Enum
from typing import Literal

from pydantic import BaseModel


# ---------- db types ----------------

class ChatTypeEnum(str, enum.Enum):
    GROUP = "group"
    PRIVATE = "private"


# ---------- ws message --------------

class WsMessageType(str, enum.Enum):
    MESSAGE = 'message'
    CHAT_PROGRESS = 'chat_progress'
    USER_PROGRESS = 'user_progress'
    NEW_USER = 'new_user'
    USER_LEFT = 'user_left'


class WsMessageBase(BaseModel):
    type: WsMessageType


# ---------- user to server ----------

class UserWsMessage(WsMessageBase):
    pass


class UserChatMessage(UserWsMessage):
    type: Literal[WsMessageType.MESSAGE]
    chat_id: int
    content: str


class UserChatProgress(UserWsMessage):
    type: Literal[WsMessageType.USER_PROGRESS]
    chat_id: int
    last_read_message_id: int


# ---------- server to user ----------

class ServerWsMessage(WsMessageBase):
    chat_id: int


class ServerWsMessageWithUser(ServerWsMessage):
    user_id: int


class ServerChatMessage(ServerWsMessageWithUser):
    type: Literal[WsMessageType.MESSAGE]
    content: str | None
    message_id: int


class ServerNewUserMessage(ServerWsMessageWithUser):
    type: Literal[WsMessageType.NEW_USER]
    message_id: int
    content: str


class ServerUserLeftMessage(ServerWsMessageWithUser):
    type: Literal[WsMessageType.USER_LEFT]
    message_id: int
    content: str


class ServerChatProgress(ServerWsMessage):
    type: Literal[WsMessageType.CHAT_PROGRESS]
    last_read_message_id: int


class ServerUserProgress(ServerWsMessageWithUser):
    type: Literal[WsMessageType.USER_PROGRESS]
    last_read_message_id: int


def parse_server_message(message: dict) -> ServerWsMessage | ServerWsMessageWithUser |None:
    mapping: dict[WsMessageType | str, type(ServerWsMessage)] = {
        WsMessageType.MESSAGE: ServerChatMessage,
        WsMessageType.NEW_USER: ServerNewUserMessage,
        WsMessageType.USER_LEFT: ServerUserLeftMessage,
        WsMessageType.CHAT_PROGRESS: ServerChatProgress,
        WsMessageType.USER_PROGRESS: ServerUserProgress
    }
    message_type = message.get('type', None)
    schema = mapping.get(message_type, None)
    if schema is not None:
        try:
            parsed = schema.model_validate(message)
            return parsed
        except Exception as e:
            print(e)
    return None


# ---------- redis -------------------

class RedisChannelType(str, enum.Enum):
    USER = "user"
    CHAT = 'chat'


# ---------- authentication ----------

class UserData(BaseModel):
    id: int
    name: str


class TokenData(BaseModel):
    user_id: int


class Token(BaseModel):
    access_token: str
    token_type: str


class Cookie(BaseModel):
    key: str
    value: str
    httponly: bool = True
    secure: bool = True
    samesite: Literal["lax", "strict", "none"] = "strict"
    max_age: int


class TokenType(str, Enum):
    ACCESS = 'access'
    REFRESH = 'refresh'
