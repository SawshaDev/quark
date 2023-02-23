# MIT License

# Copyright (c) 2023 SawshaDev

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations
import os

from typing import TYPE_CHECKING, Callable, Any, Optional

import discord

if TYPE_CHECKING:
    from .websocket import Websocket


class Node:
    def __init__(
        self,
        bot: discord.Client,
        host: str,
        port: int,
        password: str,
        https: bool,
        heartbeat: float,
        region: str,
        identifier: str,
        dumps: Callable[[Any], str],
        resume_key: Optional[str],
    ):
        self.bot = bot
        self.host = host
        self.port = port
        self.pasword = password
        self.https = https
        self.heartbeat = heartbeat
        self.region = region
        self.identifier = identifier
        self.dumps = dumps
        self.resume_key = resume_key or str(os.urandom(8).hex())