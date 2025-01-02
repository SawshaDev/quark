from __future__ import annotations

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING, Union
import urllib.parse

from aiohttp import ClientSession, ClientWebSocketResponse

import discord


import secrets
from asyncio import Task, create_task, gather
from urllib.parse import quote

import re

from quark.objects import Track

from .websocket import Websocket

if TYPE_CHECKING:
    from .player import Player


_log = logging.getLogger(__name__)

URL_RE = r = re.compile("^https://")


class NodeManager:
    _nodes: Dict[str, Node] = {}

    @classmethod        
    async def create_node(
        cls,
        *,
        client: discord.Client,
        host: str,
        port: int,
        password: str,
        identifier: Optional[str] = None,
    ) -> Node:
        if identifier is None:
            identifier = secrets.token_urlsafe(8)

        if identifier in cls._nodes.keys():
            raise Exception("Node already exists")

        node = Node(
            client=client,
            host=host,
            port=port,
            password=password,
            identifier=identifier,
        )

        await node.connect()

        cls._nodes[identifier] = node

        _log.info(cls._nodes)

        return node

    @classmethod
    def get_node(
        cls, *, identifier: str | None = None
    ) -> Node:
        if identifier:
            return cls._nodes[identifier]

        nodes = [n for n in cls._nodes.values()]

        return sorted(nodes, key=lambda node: len(node._players))[0]


class Node:
    def __init__(
        self,
        *,
        client: discord.Client | None,
        host: str,
        port: int,
        password: str,
        identifier: str,
    ):
        self._client = client

        self._host = host
        self._port = port
        self._password = password
        self._identifier = identifier

        self._uri = f"http://{self._host}:{self._port}"

        self._session = ClientSession()  # Doesn't have to be defined in async function, apparently.

        self._ws = Websocket(self)

        self._players: Dict[int, Player] = {}

        self._session_id: Optional[str] = None

    async def connect(self, *, reconnect: bool = False):
        _log.debug("Attempting Websocket connection")

        await self._ws._connect()

    async def fetch_tracks(self, query: str, *, search: Optional[str] = None) -> Track | list[Track] | None:
        if not URL_RE.match(query):
            query = f"{search if search else 'ytsearch'}:{query}"
        
        data: Dict[Any, Any] = await self._request("GET", "loadtracks", query={"identifier": query})



        if data["loadType"] == "track":
            return [Track.from_info(data["data"])]
        elif data["loadType"] == "search":
            return [Track.from_info(track) for track in data["data"]]

    async def update_player(self, *, guild_id: int, track: Optional[Union[Track, str]] = None):
        data = {}

        if track is not None:
            if isinstance(track, Track):
                data["encodedTrack"] = track.id

        return await self._request("PATCH", f"sessions/{self._session_id}/players", guild_id=guild_id, data=data)

    async def destroy_player(self, guild_id: int) -> None:
        await self._request("DELETE", f"sessions/{self._session_id}/players", guild_id=guild_id)
        
            
    def get_player(self, guild_id: int) -> Optional[Player]:
        return self._players.get(guild_id)
        

    async def _request(
        self, /, method: str, path: str, guild_id: Optional[int] = None , query: Optional[Dict[Any, Any]] = None, data: Optional[Union[dict, str]] = None 
    ) -> Any:
        uri: str = (
            f"{self._uri}/v4/"
            f"{path}"
            f'{f"/{guild_id}" if guild_id else ""}'
        )


        request = await self._session.request( method, uri, headers={"Authorization": self._password}, json = data or {}, params=query if query else "")


        if request.status == 200:
            json: Dict[Any, Any] = await request.json()

            return json


    