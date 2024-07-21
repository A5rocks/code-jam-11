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

    def enable_channel(self, guild, channel):
        if guild not in self.enabled:
            self.enabled[guild] = []
        self.enabled[guild].append(channel)

    def disable_channel(self, guild, channel):
        if guild in self.enabled:
            self.enabled[guild].remove(channel)
        else:
            raise KeyError

    def get_enabled_channels(self, guild):
        self.enabled.get(guild, [])

    def get_active_profiles(self, guild):
        self.activeProfiles.get(guild, [])

    def add_profile(self, guild, user):
        if guild not in self.activeProfiles:
            self.activeProfiles[guild] = []
        self.activeProfiles[guild].append(UserProfile(user, guild))

    def remove_profile(self, guild, user):
        profile = self.convert_member_to_user_profile(guild, user)
        if guild in self.activeProfiles:
            self.activeProfiles[guild].remove(profile)
        else:
            raise KeyError

    def get_profile(self, guild, user):
        if guild in self.activeProfiles:
            return self.convert_member_to_user_profile(guild, user)
        else:
            raise KeyError
        
    def update_profile(self, guild, user, *, priority=None, coins=None, cps=None):
        profile = self.convert_member_to_user_profile(guild, user)
        for attribute, argument in {'priority': priority, 'coins': coins, 'cps': cps}: 
            if argument is not None: profile.__setattr__(attribute, argument)
    
    def convert_member_to_user_profile(self, guild, member):
        for profile in self.activeProfiles[guild]:
            if profile.member.id == member.id: return profile
        return None