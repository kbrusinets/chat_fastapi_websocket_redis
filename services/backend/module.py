from functools import lru_cache
from services.backend.modules.chat import ChatModule
from services.backend.modules.authentication import AuthenticationModule
from services.backend.modules.message import MessageModule
from services.backend.modules.progress import ProgressModule
from services.backend.modules.redis import RedisModule, get_redis_module
from services.backend.modules.user import UserModule
from services.backend.modules.websocket import WebsocketModule, get_ws_module
from services.db import Db, get_db


class Backend:
    def __init__(self, db: Db):
        self.auth_module = AuthenticationModule(db=db)
        self.chat_module: ChatModule = ChatModule(db=db)
        self.message_module: MessageModule = MessageModule(db=db)
        self.user_module: UserModule = UserModule(db=db)
        self.progress_module: ProgressModule = ProgressModule(db=db)

        self.ws_module: WebsocketModule = get_ws_module()
        self.redis_module: RedisModule = get_redis_module()
        self.ws_module.set_redis_module(redis_module=self.redis_module)
        self.redis_module.set_websocket_module(ws_module=self.ws_module)


@lru_cache
def get_backend() -> Backend:
    return Backend(get_db())
