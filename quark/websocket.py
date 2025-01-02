from __future__ import annotations

import typing as t

from aiohttp import (
    ClientConnectorError,
    ClientWebSocketResponse,
    WSServerHandshakeError,
    WSMsgType,
)

import logging

import asyncio

from quark.errors import NodeRefused

if t.TYPE_CHECKING:
    from .node import Node


_log = logging.getLogger(__name__)


class Opcodes:
    READY = "ready"
    UPDATE = "playerUpdate"
    STATS = "stats"
    EVENT = "event"


class Websocket:
    def __init__(self, node: Node):
        self._node = node

        self._ws: t.Optional[ClientWebSocketResponse] = None

        self._loop = asyncio.get_event_loop()

        self._recv_task: t.Optional[asyncio.Task] = None
        self._is_destroyed: bool = False

    async def destroy(self):
        self._is_destroyed = True

    async def _connect(self) -> None:
        if self._is_destroyed:
            raise Exception(":p")

        headers = {
            "Authorization": self._node._password,
            "User-Id": str(self._node._client.user.id),  # type: ignore
            "Client-Name": "Quark/1.0.0",
        }

        try:
            self._ws = await self._node._session.ws_connect(f"{self._node._uri}/v4/websocket", headers=headers, )
        except WSServerHandshakeError as err:
            if err.status in (401, 403):
                _log.warning("Node Authentication was unsuccessful.")
            else:
                return

        except ClientConnectorError:
            raise NodeRefused("Node refused connection") from None
        else:
            _log.info("[Node %s] successfully connected to Lavalink", self._node._identifier, )

            self._recv_task = self._loop.create_task(self._recv())


    async def _recv(self):
        if self._ws is None:
            raise Exception("heh.")

        assert self._node._client is not None

        while True:
   
                recv = await self._ws.receive()

                if recv.type in (WSMsgType.CLOSING, WSMsgType.CLOSED):
                    close_code = recv.data
                    close_reason = recv.extra
                    #_log.debug("[Node:%s] Received close frame with code %s.", self._node._identifier, close_code)
                    break

                msg = recv.json()

                #_log.info("[Node:%s] Recieved Payload; %s", self._node._identifier, msg)

                if msg["op"] == Opcodes.READY:
                    self._node._session_id = msg["sessionId"]

                    self._node._client.dispatch("node_ready", self._node)

                if msg["op"] == Opcodes.UPDATE:
                    #_log.info("Player update event called!  %s", msg) 
                    
                    player = self._node.get_player(int(msg["guildId"]))

                    if player is None:
                        if msg["state"]["connected"]:
                            _log.info("Cannot find player! Discarding this event.")
                        
                        return

                    player._update_state(msg["state"])

                if msg["op"] == Opcodes.EVENT:
                    _log.info("recieved event data:  %s", msg)

                    player = self._node.get_player(int(msg["guildId"]))

                    if player is None:
                        _log.warning("Recieved event for unknown player! discarding")
                    else:
                        player.handle_event(msg)




        if not self._is_destroyed:
            self._loop.create_task(self._connect())
