import asyncio
import json
from collections import defaultdict
from functools import lru_cache
from typing import Set

from services.app.logger import logger
from services.app.schemas import RedisChannelType, ServerWsMessage, parse_server_message
from services.app.settings import settings

import redis.asyncio as redis

from services.backend.modules.redis.handlers import get_handler
from services.backend.modules.redis.interface import IRedisModule
from services.backend.modules.websocket.interface import IWebsocketModule


class RedisModule(IRedisModule):
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASS,
            db=settings.REDIS_DB,
        )
        self.pubsub = self.redis.pubsub()
        self.running_task = None
        self.websocket_module = None
        self.channels_subscriptions: Set[str] = set()

    def set_websocket_module(self, ws_module: IWebsocketModule):
        self.websocket_module = ws_module

    async def subscribe(self, type: RedisChannelType, key: int | str):
        channel = self.get_channel(type=type, key=key)
        if channel:
            await self.pubsub.subscribe(**{channel: self._processor})
            self.channels_subscriptions.add(channel)
            if not self.running_task:
                await self.run()
        else:
            logger.error(f'Redis module: attempted to unsubscribe but cannot find the channel for the key: {key}')

    async def unsubscribe(self, type: RedisChannelType, key: int | str):
        channel = self.get_channel(type=type, key=key)
        if channel and channel in self.channels_subscriptions:
            await self.pubsub.unsubscribe(channel)
            self.channels_subscriptions.remove(channel)
        else:
            logger.error(f'Redis module: attempted to unsubscribe but cannot find the channel for the key: {key}')

    async def _processor(self, *args, **kwargs):
        logger.debug(args)
        if not self.websocket_module:
            logger.error('Redis module: attempted to parse redis message but no websocket module is set. Skipping.')
            return
        try:
            message_data = args[0]['data'].decode('utf-8')
            message_json = json.loads(message_data)
            channel = args[0]['channel'].decode('utf-8')
        except Exception as e:
            logger.error(f'Error while parsing redis message - {e}.\n'
                         f'Input - {args}')
            return
        message_parsed = parse_server_message(message_json)
        if message_parsed:
            handler = get_handler(message_parsed.type)
            await handler(
                ws_module=self.websocket_module,
                type=self.get_type(channel=channel),
                message=message_parsed
            )
        else:
            logger.error(f'Error while parsing redis message - {message_data}')

    async def publish(self, type: RedisChannelType, key: str | int, message: ServerWsMessage):
        channel = self.get_channel(type=type, key=key)
        await self.redis.publish(channel, message.model_dump_json())
        if channel not in self.channels_subscriptions:
            logger.error(f'Published {message.model_dump_json()} in {channel}, but not subscribed to it')

    async def run(self):
        self.running_task = asyncio.create_task(self.pubsub.run())

    async def stop(self):
        self.running_task.cancel()
        await self.running_task

    @staticmethod
    def get_channel(type: RedisChannelType, key: str | int) -> str | None:
        # You can modify this when you will want more complex redis channel system
        if type == RedisChannelType.CHAT:
            return 'chat'
        if type == RedisChannelType.USER:
            return 'user'
        return None

    @staticmethod
    def get_type(channel: str) -> RedisChannelType | None:
        # You can modify this when you will want more complex redis channel system
        if channel == 'chat':
            return RedisChannelType.CHAT
        if channel == 'user':
            return RedisChannelType.USER


@lru_cache
def get_redis_module():
    return RedisModule()
