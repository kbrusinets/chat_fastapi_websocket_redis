from typing import Annotated, List

from fastapi import APIRouter, Depends

from services.app.api.v1.authentication import get_current_user
from services.app.exceptions import EntityAlreadyExistsError, EntityDoesNotExistError, Forbidden
from services.app.schemas import WsMessageType, ServerNewUserMessage, \
    ServerUserLeftMessage, ServerChatProgress, RedisChannelType
from services.backend import Backend, get_backend
from services.backend.modules.chat.schemas import ChatFull, ChatBase
from services.backend.modules.user.schemas import UserBase
from services.db.models import Chat, User

router = APIRouter(prefix='/chat', tags=['chat'])


@router.get('/progress',
            summary=' Get chat progress',
            response_model=int)
async def progress(
        chat_id: int,
        backend: Annotated[Backend, Depends(get_backend)],
        user: Annotated[User, Depends(get_current_user)]
):
    author_in_chat = await backend.chat_module.check_user_in_chat(chat_id=chat_id, user_id=user.id)
    if not author_in_chat:
        raise Forbidden(message='You are not in the chat')
    return await backend.progress_module.get_chat_progress(chat_id=chat_id)


@router.get('/user_progress',
            summary=' Get user chat progress',
            response_model=int)
async def user_progress(
        chat_id: int,
        backend: Annotated[Backend, Depends(get_backend)],
        user: Annotated[User, Depends(get_current_user)]
):
    author_in_chat = await backend.chat_module.check_user_in_chat(chat_id=chat_id, user_id=user.id)
    if not author_in_chat:
        raise Forbidden(message='You are not in the chat')
    result = await backend.chat_module.get_chat_user_read_progress(chat_id=chat_id, user_id=user.id)
    if result:
        return result.last_read_message_id
    else:
        return -1


@router.post('/create',
             summary='Create a chat',
             response_model=ChatFull)
async def create_chat(
        new_chat: ChatBase,
        backend: Annotated[Backend, Depends(get_backend)],
        user: Annotated[User, Depends(get_current_user)]
):
    chat: Chat = await backend.chat_module.create_chat(name=new_chat.name, type=new_chat.type)
    hello_message = await backend.chat_module.add_user_to_chat(chat_id=chat.id, user_id=user.id)
    await backend.redis_module.publish(
        type=RedisChannelType.USER,
        key=user.id,
        message=ServerNewUserMessage(
            type=WsMessageType.NEW_USER,
            user_id=user.id,
            chat_id=chat.id,
            message_id=hello_message.id,
            content=hello_message.content
        )
    )
    return chat


@router.post('/invite',
             summary='Invite to chat')
async def invite_to_chat(
        chat_id: int,
        user_id: int,
        backend: Annotated[Backend, Depends(get_backend)],
        user: Annotated[User, Depends(get_current_user)]
):
    chat: Chat = await backend.chat_module.get_chat(chat_id=chat_id)
    if chat is None:
        raise EntityDoesNotExistError(message='Chat does not exist')
    invited_user: User = await backend.user_module.get_user(user_id=user_id)
    if invited_user is None:
        raise EntityDoesNotExistError(message='Invited user does not exist')
    author_in_chat = await backend.chat_module.check_user_in_chat(chat_id=chat_id, user_id=user.id)
    if not author_in_chat:
        raise Forbidden(message='You are not in the chat')
    user_in_chat = await backend.chat_module.check_user_in_chat(chat_id=chat_id, user_id=user_id)
    if user_in_chat:
        raise EntityAlreadyExistsError(message='User is already in the chat')
    hello_message = await backend.chat_module.add_user_to_chat(chat_id=chat_id, user_id=user_id)
    new_user_message = ServerNewUserMessage(
        type=WsMessageType.NEW_USER,
        user_id=user_id,
        chat_id=chat_id,
        message_id=hello_message.id,
        content=hello_message.content
    )
    await backend.redis_module.publish(type=RedisChannelType.USER, key=user_id, message=new_user_message)
    await backend.redis_module.publish(type=RedisChannelType.CHAT, key=chat_id, message=new_user_message)


@router.post('/join',
             summary='Join chat')
async def join_chat(
        chat_id: int,
        backend: Annotated[Backend, Depends(get_backend)],
        user: Annotated[User, Depends(get_current_user)]
):
    user_id = user.id
    chat: Chat = await backend.chat_module.get_chat(chat_id=chat_id)
    if chat is None:
        raise EntityDoesNotExistError(message='Chat does not exist')
    user_in_chat = await backend.chat_module.check_user_in_chat(chat_id=chat_id, user_id=user_id)
    if user_in_chat:
        raise EntityAlreadyExistsError(message='User is already in the chat')
    hello_message = await backend.chat_module.add_user_to_chat(chat_id=chat_id, user_id=user_id)
    new_user_message = ServerNewUserMessage(
        type=WsMessageType.NEW_USER,
        user_id=user_id,
        chat_id=chat_id,
        message_id=hello_message.id,
        content=hello_message.content
    )
    await backend.redis_module.publish(type=RedisChannelType.USER, key=user_id, message=new_user_message)
    await backend.redis_module.publish(type=RedisChannelType.CHAT, key=chat_id, message=new_user_message)


@router.post('/leave',
             summary='Leave chat')
async def leave_chat(
        chat_id: int,
        backend: Annotated[Backend, Depends(get_backend)],
        user: Annotated[User, Depends(get_current_user)]
):
    user_in_chat = await backend.chat_module.check_user_in_chat(chat_id=chat_id, user_id=user.id)
    if not user_in_chat:
        raise Forbidden(message='User is not in the chat')
    cur_chat_progress = await backend.progress_module.get_chat_progress(chat_id=chat_id)
    goodbye_message = await backend.chat_module.delete_user_from_chat(chat_id=chat_id, user_id=user.id)
    user_left_message = ServerUserLeftMessage(
        type=WsMessageType.USER_LEFT,
        user_id=user.id,
        chat_id=chat_id,
        message_id=goodbye_message.id,
        content=goodbye_message.content
    )
    await backend.redis_module.publish(type=RedisChannelType.USER, key=user.id, message=user_left_message)
    await backend.redis_module.publish(type=RedisChannelType.CHAT, key=chat_id, message=user_left_message)
    new_chat_progress = await backend.progress_module.get_chat_progress(chat_id=chat_id)
    if new_chat_progress and new_chat_progress > cur_chat_progress:
        await backend.redis_module.publish(
            type=RedisChannelType.CHAT,
            key=chat_id,
            message=ServerChatProgress(
                type=WsMessageType.CHAT_PROGRESS,
                chat_id=chat_id,
                last_read_message_id=new_chat_progress
            )
        )


@router.get('/get_user_chats',
            summary=' Get user chats',
            response_model=List[ChatFull])
async def get_user_chats(
        backend: Annotated[Backend, Depends(get_backend)],
        user: Annotated[User, Depends(get_current_user)]
):
    chats: List[Chat] = await backend.chat_module.get_user_chats(user_id=user.id)
    return [ChatFull.model_validate(chat) for chat in chats]


@router.get('/get_chat_users',
            summary=' Get chat users',
            response_model=List[UserBase])
async def get_chat_users(
        backend: Annotated[Backend, Depends(get_backend)],
        user: Annotated[User, Depends(get_current_user)],
        chat_id: int
):
    users: List[User] = await backend.chat_module.get_chat_users(chat_id=chat_id)
    a = [UserBase(id=user.id, name=user.name) for user in users]
    return a


@router.get('/get_all',
            summary=' Get all chats. Just for testing, so no pagination or other fancy stuff.',
            response_model=List[ChatFull])
async def get_all(
        backend: Annotated[Backend, Depends(get_backend)],
        user: Annotated[User, Depends(get_current_user)]
):
    chats: List[Chat] = await backend.chat_module.get_all_chats()
    return [ChatFull.model_validate(chat) for chat in chats]
