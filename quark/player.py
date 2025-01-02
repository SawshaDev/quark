from __future__ import annotations

import discord

import typing as t

from discord.types.voice import (
    GuildVoiceState as GuildVoiceState,
    GuildVoiceState as GuildVoiceStatePayload,
    VoiceServerUpdate as VoiceServerUpdate,
)

import logging

from .objects import Track, TrackStartEvent


from .node import Node, NodeManager


_log = logging.getLogger(__name__)




class Player(discord.VoiceProtocol):
    def __call__(
        self,
        client: discord.Client,
        channel: discord.VoiceChannel,
    ) -> t.Any:
        self.client = client

        self.channel = channel

        self._guild = (
            channel.guild
        )  # Defining guild for when needed to send packets

        return self

    def __init__(
        self,
        client: discord.Client,
        channel: discord.VoiceChannel,
        *,
        node: t.Optional[Node] = None,
    ) -> None:
        # Defining important variables

        self.client = client
        self.channel = channel
        self._guild = channel.guild

        self._node = node or NodeManager.get_node()

        self.last_update: int = 0
        self.connected: bool = False    
        self.position: int = 0
        self.ping: int = -1

        self._connected: bool = False


        self._voice_state = {}

        self._last_track: Track | None = None
        self._paused: bool = False
        self.current: Track | None = None


    def _update_state(self, state) -> None:
        _log.info("[Node:%s] Updating State %s", self._node._identifier, state)

        self.last_update = state["time"]
        self.position = state.get("position", 0)
        self.connected = state["connected"]
        self.ping = state.get("ping", -1)

        self.current = (
            Track.from_info(state.get("track")) if state.get("track") else None
        )



    async def _dispatch_update(self, data) -> None:
        if {"sessionId", "event"} != self._voice_state.keys():
            return

        state = data or self._voice_state
        

        data = {
            "token": state["event"]["token"],
            "endpoint": state["event"]["endpoint"],
            "sessionId": state["sessionId"]
        }

        await self._node._request(method="PATCH", path=f"sessions/{self._node._session_id}/players", guild_id=self._guild.id, data={"voice": data})
        self._connected = True

        _log.info("[Node:%s] Dispatched voice update to %s with the payload %s", self._node._identifier, state["event"]["endpoint"], data)

    async def on_voice_server_update(
        self, data: VoiceServerUpdate
    ) -> None:
        _log.info("voice server")
        self._voice_state.update({"event": data})

        await self._dispatch_update(self._voice_state)
    
    async def on_voice_state_update(self, data: GuildVoiceState) -> None:
        _log.info("voice state")

        channel_id = data["channel_id"]

        if not channel_id:
            await self._destroy()
            return
        
        self._connected =  True


        self._voice_state.update({"sessionId": data["session_id"]})

    def handle_event(self, event_data) -> None:
        if event_data["type"] == "TrackStartEvent":
            track = Track.from_info(event_data["track"])

            event =  TrackStartEvent(raw=event_data, track=track, player=self)

            self.client.dispatch("track_start", event)

            _log.info("Recieved and Dispatched track start")

            self._last_track = track


    async def play(self, track: Track | str) -> Track | t.Any:
        _log.info("play")
        data = await self._node.update_player(guild_id=self._guild.id, track=track)

        if data["track"]:
            self.current = Track.from_info(data["track"])

            return self.current
        
        return data

    async def connect(
        self,
        *,
        timeout: float,
        reconnect: bool,
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> None:
        await self._guild.change_voice_state(channel=self.channel, self_deaf=self_deaf, self_mute=self_mute)  # type: ignore

        self._node._players[self._guild.id] = self
    
    async def disconnect(self, **kwargs) -> None:
        await self._destroy()
        await self._guild.change_voice_state(channel=None)


    def invalidate(self):
        self._connected = False

        try:
            self.cleanup()
        except (AttributeError, KeyError):
            pass
    
    async def _destroy(self):
        assert self._guild

        self.invalidate()

        player: Player | None = self._node._players.pop(self._guild.id, None)

        if player:
    
            await self._node.destroy_player(self._guild.id)

        