import pytest
from unittest.mock import call, AsyncMock
from services.backend.modules.websocket import WebsocketModule
from services.app.schemas import RedisChannelType
from fastapi import WebSocket
from services.backend.modules.redis.interface import IRedisModule


@pytest.fixture
def mock_redis_module():
    mock_redis = AsyncMock(spec=IRedisModule)
    return mock_redis


@pytest.fixture
def mock_websocket():
    mock_ws = AsyncMock(spec=WebSocket)
    return mock_ws


@pytest.fixture
def ws_module():
    ws_module = WebsocketModule()
    return ws_module


@pytest.mark.asyncio
async def test_connect_user(ws_module, mock_websocket, mock_redis_module):
    ws_module.redis_subscribe = AsyncMock(side_effect=ws_module.redis_subscribe)
    ws_module.set_redis_module(mock_redis_module)

    await ws_module.connect_user(user_id=1, websocket=mock_websocket)
    await ws_module.connect_user(user_id=2, websocket=mock_websocket)

    assert mock_websocket.accept.call_count == 2
    assert 1 in ws_module.users
    assert 2 in ws_module.users
    assert len(ws_module.users[1]) == 1
    assert len(ws_module.users[2]) == 1

    ws_module.redis_subscribe.assert_awaited_once_with(type=RedisChannelType.USER, key=1)
    mock_redis_module.subscribe.assert_awaited_once_with(type=RedisChannelType.USER, key=1)


@pytest.mark.asyncio
async def test_connect_user_no_redis_module(ws_module, mock_websocket, mock_redis_module):
    ws_module.redis_subscribe = AsyncMock(side_effect=ws_module.redis_subscribe)

    await ws_module.connect_user(user_id=1, websocket=mock_websocket)
    await ws_module.connect_user(user_id=2, websocket=mock_websocket)

    assert mock_websocket.accept.call_count == 2
    assert 1 in ws_module.users
    assert 2 in ws_module.users
    assert len(ws_module.users[1]) == 1
    assert len(ws_module.users[2]) == 1

    ws_module.redis_subscribe.assert_awaited_once_with(type=RedisChannelType.USER, key=1)
    mock_redis_module.subscribe.assert_not_awaited()


@pytest.mark.asyncio
async def test_disconnect_user(ws_module, mock_websocket, mock_redis_module):
    ws_module.redis_unsubscribe = AsyncMock(side_effect=ws_module.redis_unsubscribe)
    ws_module.remove_user_chat_relation = AsyncMock(side_effect=ws_module.remove_user_chat_relation)

    ws_module.set_redis_module(mock_redis_module)
    user_id = 1
    chat_id = 100
    ws_module.users[user_id] = {mock_websocket}
    ws_module.users_to_chats[user_id] = {chat_id, }
    ws_module.chats_to_users[chat_id] = {user_id, }

    await ws_module.disconnect_user(user_id=user_id, websocket=mock_websocket)

    assert user_id not in ws_module.users
    assert ws_module.users_to_chats == {}
    assert ws_module.chats_to_users == {}

    ws_module.redis_unsubscribe.assert_has_awaits([
        call(type=RedisChannelType.USER, key=user_id),
        call(type=RedisChannelType.CHAT, key=chat_id)
    ])
    assert ws_module.redis_unsubscribe.call_count == 2
    ws_module.remove_user_chat_relation.assert_awaited_once_with(chat_id=chat_id, user_id=user_id)
    mock_redis_module.unsubscribe.assert_has_awaits([
        call(type=RedisChannelType.USER, key=user_id),
        call(type=RedisChannelType.CHAT, key=chat_id)
    ])
    assert mock_redis_module.unsubscribe.await_count == 2


@pytest.mark.asyncio
async def test_disconnect_user_no_redis_module(ws_module, mock_websocket, mock_redis_module):
    ws_module.redis_unsubscribe = AsyncMock(side_effect=ws_module.redis_unsubscribe)
    ws_module.remove_user_chat_relation = AsyncMock(side_effect=ws_module.remove_user_chat_relation)

    user_id = 1
    chat_id = 100
    ws_module.users[user_id] = {mock_websocket}
    ws_module.users_to_chats[user_id] = {chat_id, }
    ws_module.chats_to_users[chat_id] = {user_id, }

    await ws_module.disconnect_user(user_id=user_id, websocket=mock_websocket)

    assert user_id not in ws_module.users
    assert ws_module.users_to_chats == {}
    assert ws_module.chats_to_users == {}

    ws_module.redis_unsubscribe.assert_has_awaits([
        call(type=RedisChannelType.USER, key=user_id),
        call(type=RedisChannelType.CHAT, key=chat_id)
    ])
    assert ws_module.redis_unsubscribe.call_count == 2
    ws_module.remove_user_chat_relation.assert_awaited_once_with(chat_id=chat_id, user_id=user_id)
    mock_redis_module.unsubscribe.assert_not_awaited()


@pytest.mark.asyncio
async def test_disconnect_user_subscriptions_stay(ws_module, mock_websocket, mock_redis_module):
    ws_module.redis_unsubscribe = AsyncMock(side_effect=ws_module.redis_unsubscribe)
    ws_module.remove_user_chat_relation = AsyncMock(side_effect=ws_module.remove_user_chat_relation)

    user_id = 1
    keep_user_id = 2
    chat_id = 100
    ws_module.users[user_id] = {mock_websocket}
    ws_module.users[keep_user_id] = {mock_websocket}
    ws_module.users_to_chats[user_id] = {chat_id, }
    ws_module.users_to_chats[keep_user_id] = {chat_id, }
    ws_module.chats_to_users[chat_id] = {user_id, keep_user_id}

    await ws_module.disconnect_user(user_id=user_id, websocket=mock_websocket)

    assert user_id not in ws_module.users
    assert ws_module.users_to_chats == {keep_user_id: {chat_id, }}
    assert ws_module.chats_to_users == {chat_id: {keep_user_id, }}
    ws_module.redis_unsubscribe.assert_not_awaited()
    ws_module.remove_user_chat_relation.assert_awaited_once_with(chat_id=chat_id, user_id=user_id)
    mock_redis_module.unsubscribe.assert_not_awaited()


@pytest.mark.asyncio
async def test_store_user_chat_relation(ws_module, mock_websocket):
    ws_module.redis_subscribe = AsyncMock(side_effect=ws_module.redis_subscribe)

    user_id = 1
    chat_id = 100
    ws_module.users = {user_id: {mock_websocket, }}

    await ws_module.store_user_chat_relation(chat_id=chat_id, user_id=user_id)

    assert ws_module.users_to_chats == {user_id: {chat_id, }}
    assert ws_module.chats_to_users == {chat_id: {user_id, }}

    ws_module.redis_subscribe.assert_awaited_once_with(type=RedisChannelType.CHAT, key=chat_id)


@pytest.mark.asyncio
async def test_remove_user_chat_relation(ws_module):
    ws_module.redis_unsubscribe = AsyncMock(side_effect=ws_module.redis_unsubscribe)

    user_id = 1
    chat_id = 100
    ws_module.users_to_chats = {user_id: {chat_id, }}
    ws_module.chats_to_users = {chat_id: {user_id, }}

    await ws_module.remove_user_chat_relation(chat_id=chat_id, user_id=user_id)

    assert ws_module.users_to_chats == {}
    assert ws_module.chats_to_users == {}

    ws_module.redis_unsubscribe.assert_awaited_once_with(type=RedisChannelType.CHAT, key=chat_id)


@pytest.mark.asyncio
async def test_broadcast_to_chat(ws_module, mock_websocket):
    user_id = 1
    chat_id = 100
    message = "Test message"
    ws_module.users[user_id] = {mock_websocket, }
    ws_module.chats_to_users[chat_id] = {user_id, }
    ws_module.users_to_chats[user_id] = {chat_id, }

    await ws_module.broadcast_to_chat(chat_id=chat_id, message=message)

    mock_websocket.send_text.assert_awaited_once_with(message)


@pytest.mark.asyncio
async def test_broadcast_to_chat_with_skip(ws_module, mock_websocket):
    user_id = 1
    chat_id = 100
    message = "Test message"
    ws_module.users[user_id] = {mock_websocket, }
    ws_module.chats_to_users[chat_id] = {user_id, }
    ws_module.users_to_chats[user_id] = {chat_id, }

    await ws_module.broadcast_to_chat(chat_id=chat_id, message=message, skip_users={user_id, })

    mock_websocket.send_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_broadcast_to_chat_wrong_chat(ws_module, mock_websocket):
    user_id = 1
    chat_id = 100
    message = "Test message"
    ws_module.users[user_id] = {mock_websocket, }
    ws_module.chats_to_users[chat_id] = {user_id, }
    ws_module.users_to_chats[user_id] = {chat_id, }

    await ws_module.broadcast_to_chat(chat_id=101, message=message)

    mock_websocket.send_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_broadcast_to_user(ws_module, mock_websocket):
    user_id = 1
    message = "Test message"
    ws_module.users[user_id] = {mock_websocket, }

    await ws_module.broadcast_to_user(user_id=user_id, message=message)

    mock_websocket.send_text.assert_awaited_once_with(message)
