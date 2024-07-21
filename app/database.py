import discord
import time
from discord import app_commands
from dataclasses import dataclass
import dataclasses
from enum import auto, StrEnum


class Priority(StrEnum):
    TOP = auto()
    MIDDLE = auto()
    BOTTOM = auto()


@dataclass
class UserProfile:
    member: discord.Member
    guild: discord.Guild
    priority: Priority = Priority.BOTTOM
    coins: int = 0
    cps: float = 0.1


class Database:
    def __init__(self):
        self.enabled: dict[discord.Guild, list[discord.TextChannel]] = {}
        self.activeProfiles: dict[discord.Guild, list[UserProfile]] = {}

    def enable_channel(self, channel: discord.TextChannel):
        """
        Enables the game in a channel

        Parameters
        ----------

        channel (discord.TextChannel): The channel that the game is to be enabled in 
        """
        guild = channel.guild
        if guild not in self.enabled:
            self.enabled[guild] = []
        self.enabled[guild].append(channel)

    def disable_channel(self, channel: discord.TextChannel):
        """
        Disables the game in a channel

        Parameters
        ----------

        channel (discord.TextChannel): The channel that the game is to be disabled in 
        """
        guild = channel.guild
        if guild in self.enabled:
            self.enabled[guild].remove(channel)
        else:
            raise KeyError

    def get_enabled_channels(self, guild):
        """
        Get all the channels that the game is in enabled in

        Parameters
        ----------

        guild (discord.Guild): The guild to check all enabled channels in
        """
        self.enabled.get(guild, [])

    def get_active_profiles(self, guild):
        """
        Get all the profiles that the game is in enabled in

        Parameters
        ----------

        guild (discord.Guild): The guild to check all enabled profiles in
        """
        self.activeProfiles.get(guild, [])

    def add_profile(self, member: discord.Member):
        """
        Add a profile to a specific guild

        Parameters
        ----------

        member (discord.Member): The member whose profile should be added

        """
        guild = member.guild
        if guild not in self.activeProfiles:
            self.activeProfiles[guild] = []
        self.activeProfiles[guild].append(UserProfile(member, guild))

    def remove_profile(self, member: discord.Member):
        """
        Remove a profile from a specific guild

        Parameters
        ----------

        member (discord.Member): The member whose profile should be removed


        
        """
        guild = member.guild
        profile = self.convert_member_to_user_profile(guild, user)
        if guild in self.activeProfiles:
            self.activeProfiles[guild].remove(profile)
        else:
            raise KeyError

    def get_profile(self, guild, user):
        """
        Get a profile from a specific guild, if the user object does not have the guild already attached to it

        Parameters
        ----------

        guild (discord.Guild): The guild that will be checked
        user (discord.User): The user whose profile that will be returned

        """
        if guild in self.activeProfiles:
            return self.convert_member_to_user_profile(guild, user)
        else:
            raise KeyError
        
    def update_profile(self,guild: discord.Guild, member: discord.Member, *, priority: (Priority | None)=None, coins: (int | None)=None, cps: (float | None)=None):
        """
        Updates a specific profile with new values

        Supported values are:
        priority (Priority): The priority of the profile
        coins (int): The amount of coins in the profile
        cps (float): The cps that the profile has

        If this is not passed in a value of None is used and the profile is not changed
        """
        
        profile = self.convert_member_to_user_profile(guild, member)
        for attribute, argument in {'priority': priority, 'coins': coins, 'cps': cps}: 
            if argument is not None: profile.__setattr__(attribute, argument)
    
    def convert_member_to_user_profile(self, guild: discord.Guild, member: discord.Member) -> (UserProfile | None):
        """
        Helper method to convert a discord.Member or discord.User object to a UserProfile

        This method goes through all active profiles in the guild and checks if the member matches the profile's member field
        
        Parameters
        ----------

        guild (discord.Guild): The guild in which the profiles are being looked up
        member (discord.Member): The member that this method is trying to match

        Returns
        ----------

        UserProfile if there is an existing profile for the member
        None if there is not an existing profile
        """

        for profile in self.activeProfiles[guild]:
            if profile.member.id == member.id: return profile
        return None
        