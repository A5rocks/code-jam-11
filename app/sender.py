from __future__ import annotations

import asyncio
import collections
import dataclasses
import heapq
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    import discord

    from __main__ import DiscordClient


MAX_MESSAGE_LENGTH = 2000


class Editable(Protocol):
    """Describes things that can be edited."""

    async def edit(self, *, content: str) -> object:
        """Tell the thing to edit itself with some new content."""


@dataclasses.dataclass
class Sender:
    """Storage for messages that are to be sent out slowly."""

    _queue: list[tuple[float, discord.User]] = dataclasses.field(init=False, default_factory=list)
    _started: bool = dataclasses.field(init=False, default=False)
    _buffers: dict[discord.User, str] = dataclasses.field(init=False, default_factory=dict)

    async def start(
        self,
        send: Callable[[str], Awaitable[Editable]],
        cps: Callable[[discord.User], Awaitable[float]],
    ) -> None:
        """Task to send out messages slowly.

        It is ok to start this task multiple times, though not across multiple threads.
        """
        # this is async-safe
        if self._started:
            return

        self._started = True
        loop = asyncio.get_running_loop()
        buffer = ""
        last: Editable | None = None
        last_send = loop.time() - 1

        while self._queue:
            when, who = heapq.heappop(self._queue)
            await asyncio.sleep(when - loop.time())

            char = self._buffers[who][0]  # should this split on graphenes instead?
            buffer += char

            if loop.time() >= last_send + 1:
                # send the new buffer
                last_send = loop.time()
                if last and len(buffer) <= MAX_MESSAGE_LENGTH:
                    await last.edit(content=buffer)
                elif last:
                    await last.edit(content=buffer[:MAX_MESSAGE_LENGTH])
                    if len(buffer) > 2 * MAX_MESSAGE_LENGTH:
                        # this is possible if there are many people sending messages
                        # (or high enough cps rates), but is a complicated case to deal with
                        # because of Discord's ratelimits. (which are 5/5s)
                        raise NotImplementedError
                    buffer = buffer[MAX_MESSAGE_LENGTH:]
                    last = None

                if last is None:
                    last = await send(buffer)

            new_cps = await cps(who)
            if len(self._buffers[who]) > 1:
                heapq.heappush(self._queue, (when + 1 / new_cps, who))
                self._buffers[who] = self._buffers[who][1:]
            else:
                del self._buffers[who]

        self._started = False

    def add_item(self, who: discord.User, cps: float, what: str) -> None:
        """Add a message to a queue to be sent."""
        loop = asyncio.get_running_loop()
        if who in self._buffers:
            self._buffers[who] = self._buffers[who] + what
        else:
            heapq.heappush(self._queue, (loop.time() + 1 / cps, who))
            self._buffers[who] = what


senders: dict[discord.TextChannel, Sender] = collections.defaultdict(Sender)


async def send(client: DiscordClient, where: discord.TextChannel, who: discord.User, what: str) -> None:
    """Add a message to a queue of messages to be sent, potentially starting a new queue."""

    async def cps(p: discord.User) -> float:
        profile = await client.database.get_profile(where.guild, p)
        return profile.cps

    senders[where].add_item(who, await cps(who), what)
    asyncio.create_task(senders[where].start(where.send, cps))  # noqa: RUF006
