from __future__ import annotations

import asyncio
import collections
import dataclasses
import heapq
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


MAX_MESSAGE_LENGTH = 2000
MAX_QUEUE_TIME = 300


class Editable(Protocol):
    """Describes things that can be edited."""

    async def edit(self, *, content: str) -> object:
        """Tell the thing to edit itself with some new content."""


@dataclasses.dataclass
class Sender:
    """Storage for messages that are to be sent out slowly."""

    _queue: list[tuple[float, int]] = dataclasses.field(init=False, default_factory=list)
    _started: bool = dataclasses.field(init=False, default=False)
    _buffers: dict[int, str] = dataclasses.field(init=False, default_factory=dict)

    async def start(
        self,
        send: Callable[[str], Awaitable[Editable]],
        cps: Callable[[int], Awaitable[float]],
        add_coin: Callable[[int], Awaitable[None]],
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
            await add_coin(who)
            if len(self._buffers[who]) > 1:
                heapq.heappush(self._queue, (when + 1 / new_cps, who))
                self._buffers[who] = self._buffers[who][1:]
            else:
                del self._buffers[who]

        self._started = False

    def add_item(self, who: int, cps: float, what: str) -> bool:
        """Add a message to a queue to be sent."""
        loop = asyncio.get_running_loop()

        if (len(self._buffers.get(who, "")) + len(what)) / cps > MAX_QUEUE_TIME:
            return True
        if who in self._buffers:
            self._buffers[who] = self._buffers[who] + what
        else:
            heapq.heappush(self._queue, (loop.time() + 1 / cps, who))
            self._buffers[who] = what
        return False


senders: dict[int, Sender] = collections.defaultdict(Sender)


async def send(  # noqa: PLR0913; the alternative is worse
    channel_id: int,
    who: int,
    what: str,
    send: Callable[[str], Awaitable[Editable]],
    cps: Callable[[int], Awaitable[float]],
    add_coin: Callable[[int], Awaitable[None]],
) -> bool:
    """Add a message to a queue of messages to be sent, potentially starting a new queue."""
    if senders[channel_id].add_item(who, await cps(who), f"{what}\n") is True:
        return True

    asyncio.create_task(senders[channel_id].start(send, cps, add_coin))  # noqa: RUF006
    return False
