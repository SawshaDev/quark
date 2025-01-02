from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Optional, Dict, List

if TYPE_CHECKING:
    from .player import Player

class Track:
    def __init__(
        self,
        *,
        id: str,
        identifier: str,
        seekable: bool,
        length: int,
        author: str,
        stream: bool,
        position: int,
        title: str,
        uri: Optional[str] = None,
        artwork: Optional[str] = None,
        isrc: Optional[str] = None,
        source: str,
    ) -> None:
        self.id = id
        self.identifier = identifier

        self.seekable = seekable
        self.length = length

        self.author = author
        self.stream = stream
        self.position = position
        self.title = title
        self.source = source
        
        self.uri: Optional[str] = uri
        self.artwork: Optional[str] = artwork
        self.isrc:  Optional[str] = isrc

    @classmethod
    def from_data(cls, *, track: str, info) -> Track:
        return cls(
            id=track,
            title=info["title"],
            author=info["author"],
            identifier=info["identifier"],
            uri=info["uri"],
            source=info["sourceName"],
            stream=info["isStream"],
            seekable=info["isSeekable"],
            position=info["position"],
            length=info["length"],
            artwork=info.get("artworkUrl"),
            isrc=info.get("isrc"),
        )

    @classmethod
    def from_info(cls, data) -> Track:
        print(data)
        return cls.from_data(track=data["encoded"], info=data["info"])

class TrackStartEvent:
    def __init__(self, *, raw, track: Track, player: Player, ) -> None:
        self.track = track
        self.raw = raw
        self.player = player
        