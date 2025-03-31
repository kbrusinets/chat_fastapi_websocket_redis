import asyncio

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from redis._parsers import Encoder
from redis.asyncio.client import PubSub

from services.backend.modules.redis import RedisModule
from services.app.schemas import RedisChannelType, WsMessageType, ServerChatMessage, \
    ServerChatProgress, ServerNewUserMessage, ServerUserLeftMessage, ServerUserProgress, ServerWsMessage
from services.backend.modules.websocket.interface import IWebsocketModule


@pytest.fixture
def mock_ws_module():
    return MagicMock(IWebsocketModule)


@pytest.fixture
def redis_module():
    with patch('redis.asyncio.Redis') as mock_redis_class:
        mock_pubsub = PubSub(
            connection_pool=MagicMock(),
            encoder=Encoder(
                encoding="utf-8",
                encoding_errors="strict",
                decode_responses=False,
            )
        )
        mock_pubsub.execute_command = AsyncMock()
        mock_pubsub.connect = AsyncMock()

        mock_redis_instance = MagicMock()
        mock_redis_instance.pubsub.return_value = mock_pubsub
        mock_redis_instance.publish = AsyncMock()
        mock_redis_class.return_value = mock_redis_instance
        yield RedisModule()


@pytest.mark.asyncio
async def test_subscribe_new_message_handler(redis_module, mock_ws_module):
    redis_module.pubsub.subscribe = AsyncMock(side_effect=redis_module.pubsub.subscribe)
    redis_module.set_websocket_module(mock_ws_module)
    new_chat_message = ServerChatMessage(
        type=WsMessageType.MESSAGE,
        chat_id=1,
        user_id=1,
        content='',
        message_id=1
    )
    redis_module.pubsub.parse_response = AsyncMock(
        side_effect=[
            ['message', 'user'.encode("utf-8"), new_chat_message.model_dump_json().encode("utf-8")],
            asyncio.CancelledError
        ]
    )
    redis_module.run = AsyncMock(side_effect=redis_module.run)

    with patch("services.backend.modules.redis.handlers.NewMessageHandler.__call__",
               new_callable=AsyncMock) as mock_handler:
        try:
            await redis_module.subscribe(RedisChannelType.USER, 1)
            await redis_module.running_task
        except asyncio.CancelledError as e:
            pass

        redis_module.pubsub.subscribe.assert_awaited_once_with(**{'user': redis_module._processor})
        redis_module.run.assert_awaited_once()
        assert 'user' in redis_module.channels_subscriptions
        mock_handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscribe_new_user_handler(redis_module, mock_ws_module):
    redis_module.pubsub.subscribe = AsyncMock(side_effect=redis_module.pubsub.subscribe)
    redis_module.set_websocket_module(mock_ws_module)
    new_chat_message = ServerNewUserMessage(
        type=WsMessageType.NEW_USER,
        chat_id=1,
        user_id=1,
        message_id=1,
        content=''
    )
    redis_module.pubsub.parse_response = AsyncMock(
        side_effect=[
            ['message', 'user'.encode("utf-8"), new_chat_message.model_dump_json().encode("utf-8")],
            asyncio.CancelledError
        ]
    )
    redis_module.run = AsyncMock(side_effect=redis_module.run)

    with patch("services.backend.modules.redis.handlers.NewUserHandler.__call__",
               new_callable=AsyncMock) as mock_handler:
        try:
            await redis_module.subscribe(RedisChannelType.USER, 1)
            await redis_module.running_task
        except asyncio.CancelledError as e:
            pass

        redis_module.pubsub.subscribe.assert_awaited_once_with(**{'user': redis_module._processor})
        redis_module.run.assert_awaited_once()
        assert 'user' in redis_module.channels_subscriptions
        mock_handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscribe_user_left_handler(redis_module, mock_ws_module):
    redis_module.pubsub.subscribe = AsyncMock(side_effect=redis_module.pubsub.subscribe)
    redis_module.set_websocket_module(mock_ws_module)
    new_chat_message = ServerUserLeftMessage(
        type=WsMessageType.USER_LEFT,
        chat_id=1,
        user_id=1,
        message_id=1,
        content=''
    )
    redis_module.pubsub.parse_response = AsyncMock(
        side_effect=[
            ['message', 'user'.encode("utf-8"), new_chat_message.model_dump_json().encode("utf-8")],
            asyncio.CancelledError
        ]
    )
    redis_module.run = AsyncMock(side_effect=redis_module.run)

    with patch("services.backend.modules.redis.handlers.UserLeftHandler.__call__",
               new_callable=AsyncMock) as mock_handler:
        try:
            await redis_module.subscribe(RedisChannelType.USER, 1)
            await redis_module.running_task
        except asyncio.CancelledError as e:
            pass

        redis_module.pubsub.subscribe.assert_awaited_once_with(**{'user': redis_module._processor})
        redis_module.run.assert_awaited_once()
        assert 'user' in redis_module.channels_subscriptions
        mock_handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscribe_chat_progress_handler(redis_module, mock_ws_module):
    redis_module.pubsub.subscribe = AsyncMock(side_effect=redis_module.pubsub.subscribe)
    redis_module.set_websocket_module(mock_ws_module)
    new_chat_message = ServerChatProgress(
        type=WsMessageType.CHAT_PROGRESS,
        chat_id=1,
        last_read_message_id=1
    )
    redis_module.pubsub.parse_response = AsyncMock(
        side_effect=[
            ['message', 'user'.encode("utf-8"), new_chat_message.model_dump_json().encode("utf-8")],
            asyncio.CancelledError
        ]
    )
    redis_module.run = AsyncMock(side_effect=redis_module.run)

    with patch("services.backend.modules.redis.handlers.ChatProgressHandler.__call__",
               new_callable=AsyncMock) as mock_handler:
        try:
            await redis_module.subscribe(RedisChannelType.USER, 1)
            await redis_module.running_task
        except asyncio.CancelledError as e:
            pass

        redis_module.pubsub.subscribe.assert_awaited_once_with(**{'user': redis_module._processor})
        redis_module.run.assert_awaited_once()
        assert 'user' in redis_module.channels_subscriptions
        mock_handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscribe_user_progress_handler(redis_module, mock_ws_module):
    redis_module.pubsub.subscribe = AsyncMock(side_effect=redis_module.pubsub.subscribe)
    redis_module.set_websocket_module(mock_ws_module)
    new_chat_message = ServerUserProgress(
        type=WsMessageType.USER_PROGRESS,
        chat_id=1,
        user_id=1,
        last_read_message_id=1
    )
    redis_module.pubsub.parse_response = AsyncMock(
        side_effect=[
            ['message', 'user'.encode("utf-8"), new_chat_message.model_dump_json().encode("utf-8")],
            asyncio.CancelledError
        ]
    )
    redis_module.run = AsyncMock(side_effect=redis_module.run)

    with patch("services.backend.modules.redis.handlers.UserProgressHandler.__call__",
               new_callable=AsyncMock) as mock_handler:
        try:
            await redis_module.subscribe(RedisChannelType.USER, 1)
            await redis_module.running_task
        except asyncio.CancelledError as e:
            pass

        redis_module.pubsub.subscribe.assert_awaited_once_with(**{'user': redis_module._processor})
        redis_module.run.assert_awaited_once()
        assert 'user' in redis_module.channels_subscriptions
        mock_handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_unsubscribe(redis_module, mock_ws_module):
    redis_module.pubsub.unsubscribe = AsyncMock(side_effect=redis_module.pubsub.unsubscribe)
    channel = 'user'
    redis_module.channels_subscriptions.add(channel)
    await redis_module.unsubscribe(RedisChannelType.USER, 1)

    redis_module.pubsub.unsubscribe.assert_awaited_once_with('user')
    assert len(redis_module.channels_subscriptions) == 0


@pytest.mark.asyncio
async def test_publish(redis_module, mock_ws_module):
    channel_type = RedisChannelType.USER
    chat_id = 1
    message = ServerWsMessage(type=WsMessageType.MESSAGE, chat_id=chat_id)
    await redis_module.publish(type=channel_type, key=chat_id, message=message)
    channel = redis_module.get_channel(type=channel_type, key=chat_id)
    redis_module.redis.publish.assert_awaited_once_with(channel, message.model_dump_json())