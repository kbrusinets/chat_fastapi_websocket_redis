from fastapi import APIRouter

from .authentication import router as login_router
from .websocket.websocket import router as websocket_router
from .chat import router as chat_router
from .message import router as message_router

router = APIRouter(prefix='/v1')
router.include_router(login_router)
router.include_router(websocket_router)
router.include_router(chat_router)
router.include_router(message_router)
