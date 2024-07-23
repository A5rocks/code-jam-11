import collections
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
    user: discord.User


class Database:
    """Class to store user profile and channel data."""

    def __init__(self) -> None:
        self.enabled: dict[discord.Guild, set[discord.TextChannel]] = collections.defaultdict(set)
        self.activeProfiles: dict[discord.Guild, dict[discord.User, UserProfile]] = collections.defaultdict(
            lambda: collections.defaultdict(UserProfile),
        )

    def enable_channel(self, channel: discord.TextChannel) -> None:
        """Enable the game in a channel.

        Arguments:
        ---------
        channel (discord.TextChannel): The channel that the game is to be enabled in

        """
        guild = channel.guild
        self.enabled[guild].add(channel)

    def disable_channel(self, channel: discord.TextChannel) -> None:
        """Disable the game in a channel.

        Arguments:
        ---------
        channel (discord.TextChannel): The channel that the game is to be disabled in

        """
        guild = channel.guild
        self.enabled[guild].discard(channel)

    def get_enabled_channels(self, guild: discord.Guild) -> set[discord.TextChannel]:
        """Get all the channels that the game is in enabled in.

        Arguments:
        ---------
        guild (discord.Guild): The guild to check all enabled channels in

        """
        return self.enabled[guild]

    def get_active_profiles(self, guild: discord.Guild) -> dict[discord.User, UserProfile]:
        """Get all the profiles that the game is in enabled in.

        Arguments:
        ---------
        guild (discord.Guild): The guild to check all enabled profiles in

        """
        return self.activeProfiles[guild]

    def add_profile(self, guild: discord.Guild, user: discord.User) -> None:
        """Add a profile to a specific guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the user is in
        user (discord.User): This user whose profile is to be added

        """
        self.activeProfiles[guild][user] = UserProfile()

    def remove_profile(self, guild: discord.Guild, user: discord.User) -> None:
        """Remove a profile from a specific guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the user is in
        user (discord.User): This user whose profile is to be removed

        """
        self.activeProfiles[guild].pop(user, None)

    def get_profile(self, guild: discord.Guild, user: discord.User) -> UserProfile:
        """Get a profile from a specific guild, if the user object does not have the guild already attached to it.

        Arguments:
        ---------
        guild (discord.Guild): The guild that will be checked
        user (discord.User): The user whose profile that will be returned

        """
        return self.activeProfiles[guild][user]

    def update_profile(
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
