import json
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from services.app.api.v1.authentication import get_current_user
from services.app.api.v1.websocket.handlers import get_handler
from services.app.schemas import WsMessageBase
from services.backend import Backend, get_backend
from services.db.models import User

router = APIRouter(tags=['ws'])

@router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        backend: Annotated[Backend, Depends(get_backend)],
        user: Annotated[User, Depends(get_current_user)]
):
    await backend.ws_module.connect_user(user_id=user.id, websocket=websocket)
    chats = await backend.chat_module.get_user_chats(user_id=user.id)
    for chat in chats:
        await backend.ws_module.store_user_chat_relation(chat_id=chat.id, user_id=user.id)

    while True:
        try:
            message = await websocket.receive_json()
            try:
                preparsed_message = WsMessageBase(**message)
            except ValidationError as e:
                continue
            handler = get_handler(message_type=preparsed_message.type)
            if handler:
                await handler(
                    backend=backend,
                    user=user,
                    websocket=websocket,
                    message=message)
            else:
                print(f'Unknown user ws message - {json.dumps(message)}')
        except WebSocketDisconnect:
            await backend.ws_module.disconnect_user(user_id=user.id, websocket=websocket)
            break
        except Exception as e:
            print(e)
