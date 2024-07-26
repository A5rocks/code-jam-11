import collections
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum, auto

import discord


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
    async def enable_channel(self, channel: discord.TextChannel) -> None:
        """Enable the game in a channel.

        Arguments:
        ---------
        channel (discord.TextChannel): The channel that the game is to be enabled in

        """

    @abstractmethod
    async def disable_channel(self, guild: discord.Guild, channel_id: int) -> None:
        """Disable the game in a channel.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the game is to be disabled in
        channel_id (int): The channel that the game is to be disabled in

        """

    @abstractmethod
    async def get_channels(self, guild: discord.Guild) -> list[int]:
        """Get all the channels that the game is in enabled in.

        Arguments:
        ---------
        guild (discord.Guild): The guild to check all enabled channels in

        """

    @abstractmethod
    async def add_profile(self, guild: discord.Guild, user: discord.User, user_profile: UserProfile) -> None:
        """Add a profile to a specific guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the user is in
        user (discord.User): This user whose profile is to be added
        user_profile (UserProfile | None): The UserProfile to be added, if None, a new instance is created

        """

    @abstractmethod
    async def remove_profile(self, guild: discord.Guild, user: discord.User) -> None:
        """Remove a profile from a specific guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the user is in
        user (discord.User): This user whose profile is to be removed

        """

    @abstractmethod
    async def get_profile(self, guild: discord.Guild, user: discord.User) -> UserProfile:
        """Get a profile from a specific guild, if the user object does not have the guild already attached to it.

        Arguments:
        ---------
        guild (discord.Guild): The guild that will be checked
        user (discord.User): The user whose profile that will be returned

        """

    @abstractmethod
    async def update_profile(self, guild: discord.Guild, user: discord.User, new_profile: UserProfile) -> None:
        """Replace a profile with a new profile with updated values.

        Arguments:
        ---------
        guild (discord.Guild): The guild in which the profile is in
        user (discord.User): The user whose profile will be updated
        new_profile (UserProfile): The new profile with updated values that is to be inserted.

        If this is not passed in a value of None is used and the profile is not changed

        """


class Database(AbstractDatabase):
    """Class to store user profile and channel data."""

    def __init__(self) -> None:
        self.enabled: dict[discord.Guild, list[int]] = collections.defaultdict(list)
        self.activeProfiles: dict[discord.Guild, dict[discord.User, UserProfile]] = collections.defaultdict(
            lambda: collections.defaultdict(UserProfile),
        )

    async def enable_channel(self, channel: discord.TextChannel) -> None:
        """Enable the game in a channel.

        Arguments:
        ---------
        channel (discord.TextChannel): The channel that the game is to be enabled in

        """
        guild = channel.guild
        self.enabled[guild].append(channel.id)

    async def disable_channel(self, guild: discord.Guild, channel_id: int) -> None:
        """Disable the game in a channel.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the game is to be disabled in
        channel_id (int): The channel that the game is to be disabled in

        """
        # TODO: use IDs for everything in this database
        self.enabled[guild].remove(channel_id)

    async def get_channels(self, guild: discord.Guild) -> list[int]:
        """Get all the channels that the game is in enabled in.

        Arguments:
        ---------
        guild (discord.Guild): The guild to check all enabled channels in

        """
        return self.enabled[guild]

    async def add_profile(
        self, guild: discord.Guild, user: discord.User, user_profile: UserProfile | None = None
    ) -> None:
        """Add a profile to a specific guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the user is in
        user (discord.User): This user whose profile is to be added
        user_profile (UserProfile | None): The UserProfile to be added, if None, a new instance is created

        """
        if user_profile is None:
            user_profile = UserProfile()

        self.activeProfiles[guild][user] = user_profile

    async def remove_profile(self, guild: discord.Guild, user: discord.User) -> None:
        """Remove a profile from a specific guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the user is in
        user (discord.User): This user whose profile is to be removed

        """
        self.activeProfiles[guild].pop(user, None)

    async def get_profile(self, guild: discord.Guild, user: discord.User) -> UserProfile:
        """Get a profile from a specific guild, if the user object does not have the guild already attached to it.

        Arguments:
        ---------
        guild (discord.Guild): The guild that will be checked
        user (discord.User): The user whose profile that will be returned

        """
        return self.activeProfiles[guild][user]

    async def update_profile(
        self,
        guild: discord.Guild,
        user: discord.User,
        new_profile: UserProfile,
    ) -> None:
        """Replace a profile with a new profile with updated values.

        Arguments:
        ---------
        guild (discord.Guild): The guild in which the profile is in
        user (discord.User): The user whose profile will be updated
        new_profile (UserProfile): The new profile with updated values that is to be inserted.

        If this is not passed in a value of None is used and the profile is not changed

        """
        self.activeProfiles[guild][user] = new_profile
