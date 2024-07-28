import collections
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum, auto


class MessagePriority(StrEnum):
    """Enum to determine a user's priority."""

    TOP = auto()
    MIDDLE = auto()
    BOTTOM = auto()


@dataclass(frozen=True)
class UserProfile:
    """Class to hold user data such as their priority, amount of coins, and characters per second."""

    priority: MessagePriority = MessagePriority.BOTTOM
    coins: int = 0
    cps: float = 0.1


class AbstractDatabase(ABC):
    """An abstract database class to have database implementation."""

    @abstractmethod
    async def enable_channel(self, guild_id: int, channel_id: int) -> None:
        """Enable the game in a channel.

        Arguments:
        ---------
        guild_id (int): The guild that the game is to be enabled in
        channel_id (int): The channel that the game is to be enabled in

        """

    @abstractmethod
    async def disable_channel(self, guild_id: int, channel_id: int) -> None:
        """Disable the game in a channel.

        Arguments:
        ---------
        guild_id (int): The guild that the game is to be disabled in
        channel_id (int): The channel that the game is to be disabled in

        """

    @abstractmethod
    async def get_channels(self, guild_id: int) -> list[int]:
        """Get all the channels that the game is in enabled in.

        Arguments:
        ---------
        guild_id (int): The guild to get all enabled channels in

        """

    @abstractmethod
    async def remove_profile(self, guild_id: int, user_id: int) -> None:
        """Remove a profile from a specific guild.

        Arguments:
        ---------
        guild_id (int): The guild that the user is in
        user_id (int): This user whose profile is to be removed

        """

    @abstractmethod
    async def get_profile(self, guild_id: int, user_id: int) -> UserProfile:
        """Get a profile from a specific guild, if the user object does not have the guild already attached to it.

        Arguments:
        ---------
        guild_id (int): The guild that will be checked
        user_id (int): The user whose profile that will be returned

        """

    @abstractmethod
    async def update_profile(self, guild_id: int, user_id: int, new_profile: UserProfile) -> None:
        """Replace a profile with a new profile with updated values.

        Arguments:
        ---------
        guild_id (int): The guild in which the profile is in
        user_id (int): The user whose profile will be updated
        new_profile (UserProfile): The new profile with updated values that is to be inserted.

        If this is not passed in a value of None is used and the profile is not changed

        """


class Database(AbstractDatabase):
    """Class to store user profile and channel data."""

    def __init__(self) -> None:
        self.enabled: dict[int, list[int]] = collections.defaultdict(list)
        self.activeProfiles: dict[int, dict[int, UserProfile]] = collections.defaultdict(
            lambda: collections.defaultdict(UserProfile),
        )

    async def enable_channel(self, guild_id: int, channel_id: int) -> None:
        """Enable the game in a channel.

        Arguments:
        ---------
        guild_id (int): The guild that the game is to be enabled in
        channel_id (int): The channel that the game is to be enabled in

        """
        self.enabled[guild_id].append(channel_id)

    async def disable_channel(self, guild_id: int, channel_id: int) -> None:
        """Disable the game in a channel.

        Arguments:
        ---------
        guild_id (int): The guild that the game is to be disabled in
        channel_id (int): The channel that the game is to be disabled in

        """
        self.enabled[guild_id].remove(channel_id)

    async def get_channels(self, guild_id: int) -> list[int]:
        """Get all the channels that the game is in enabled in.

        Arguments:
        ---------
        guild_id (int): The guild to get all enabled channels in

        """
        return self.enabled[guild_id]

    async def remove_profile(self, guild_id: int, user_id: int) -> None:
        """Remove a profile from a specific guild.

        Arguments:
        ---------
        guild_id (int): The guild that the user is in
        user_id (int): This user whose profile is to be removed

        """
        self.activeProfiles[guild_id].pop(user_id, None)

    async def get_profile(self, guild_id: int, user_id: int) -> UserProfile:
        """Get a profile from a specific guild, if the user object does not have the guild already attached to it.

        Arguments:
        ---------
        guild_id (int): The guild that will be checked
        user_id (int): The user whose profile that will be returned

        """
        return self.activeProfiles[guild_id][user_id]

    async def update_profile(self, guild_id: int, user_id: int, new_profile: UserProfile) -> None:
        """Replace a profile with a new profile with updated values.

        Arguments:
        ---------
        guild_id (int): The guild in which the profile is in
        user_id (int): The user whose profile will be updated
        new_profile (UserProfile): The new profile with updated values that is to be inserted.

        If this is not passed in a value of None is used and the profile is not changed

        """
        self.activeProfiles[guild_id][user_id] = new_profile
