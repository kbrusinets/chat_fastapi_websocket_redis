from typing import Annotated

from fastapi import APIRouter, Depends

from services.app.api.v1.authentication import get_current_user
from services.app.exceptions import EntityDoesNotExistError, Forbidden
from services.backend import Backend, get_backend
from services.backend.modules.message.schemas import MessagesPagination
from services.db.models import User, Chat

router = APIRouter(prefix='/message', tags=['message'])


@router.get('/get_chat_messages',
            summary='Get DESC ordered chat messages, with optional filtering by user',
            response_model=MessagesPagination)
async def get_chat_messages(
        backend: Annotated[Backend, Depends(get_backend)],
        user: Annotated[User, Depends(get_current_user)],
        chat_id: int,
        user_id: int | None = None,
        limit: int = 100,
        offset: int = 0
):
    chat: Chat = await backend.chat_module.get_chat(chat_id=chat_id)
    if chat is None:
        raise EntityDoesNotExistError(message='Chat does not exist')
    author_in_chat = await backend.chat_module.check_user_in_chat(chat_id=chat_id, user_id=user.id)
    if not author_in_chat:
        raise Forbidden(message='You are not a chat participant')
    return await backend.message_module.get_messages_with_pagination_data(
        chat_id=chat_id, user_id=user_id, limit=limit, offset=offset
    )


@router.get('/get_user_unread',
            summary=' Get number of unread messages in chat for the user.',
            response_model=int)
async def get_unread(
        backend: Annotated[Backend, Depends(get_backend)],
        user: Annotated[User, Depends(get_current_user)],
        chat_id: int,
        until_mess_id: int | None = None
):
    user_in_chat = await backend.chat_module.check_user_in_chat(chat_id=chat_id, user_id=user.id)
    if not user_in_chat:
        raise Forbidden(message='User is not in the chat')
    return await backend.progress_module.get_user_unread_in_chat(
        chat_id=chat_id, user_id=user.id, until_mess_id=until_mess_id)
