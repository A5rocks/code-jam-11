import contextlib
import typing

import aiosqlite
import discord
from database import UserProfile

db_path = "demo.db"


class AsyncDatabase:
    """Class to store user profile and channel data asynchronously."""

    def __init__(self, connection: aiosqlite.Connection) -> None:
        self.connection = connection

    async def enable_channel(self, channel: discord.TextChannel) -> None:
        """Enable the game in a channel.

        Arguments:
        ---------
        channel (discord.TextChannel): The channel that the game is to be enabled in

        """
        await self.connection.execute(
            "INSERT INTO Guilds(id, channel) VALUES (?,?)",
            (channel.guild.id, channel.id),
        )
        await self.connection.commit()

    async def disable_channel(self, channel: discord.TextChannel) -> None:
        """Disable the game in a channel.

        Arguments:
        ---------
        channel (discord.TextChannel): The channel that the game is to be disabled in

        """
        await self.connection.execute("DELETE FROM Guilds WHERE id=? AND channel=?", (channel.guild.id, channel.id))
        await self.connection.commit()

    async def get_channels(self, guild: discord.Guild) -> list[discord.TextChannel]:
        """Get all the channels that the game is enabled in for a guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild to check all enabled channels in

        """
        async with (
            self.connection.execute("SELECT channel FROM Guilds WHERE guild_id = ?", (guild.id)) as cursor,
        ):
            return [discord.Client.get_channel(row[0]) for row in cursor]

    async def get_active_profiles(self, guild: discord.Guild) -> list[UserProfile]:
        """Get all the profiles that the game is enabled in.

        Arguments:
        ---------
        guild (discord.Guild): The guild to check all enabled profiles in

        """
        async with (
            self.connection.execute("SELECT coins, cps FROM Users WHERE guild_id = ?", (guild.id)) as cursor,
        ):
            return [UserProfile(coins=row[0], cps=row[1]) for row in cursor]

    async def add_profile(self, guild: discord.Guild, user: discord.User, user_profile: UserProfile) -> None:
        """Add a profile to a specific guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the user is in
        user (discord.User): The discord user to be added
        user_profile (UserProfile): The UserProfile data to be added

        """
        await self.connection.execute(
            "INSERT INTO Users(user_id, guild_id, cps, coins) VALUES (?,?,?,?)",
            (user.id, guild.id, user_profile.cps, user_profile.coins),
        )
        await self.connection.commit()

    async def remove_profile(self, guild: discord.Guild, user: discord.User) -> None:
        """Remove a profile from a specific guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the user is in
        user (discord.User): This user whose profile is to be removed

        """
        await self.connection.execute("DELETE FROM Users WHERE user_id=? AND guild_id=?", (user.id, guild.id))
        await self.connection.commit()

    async def get_profile(self, guild: discord.Guild, user: discord.User) -> UserProfile | None:
        """Get a profile from a specific guild, if the user object does not have the guild already attached to it.

        Arguments:
        ---------
        guild (discord.Guild): The guild that will be checked
        user (discord.User): The user whose profile that will be returned

        """
        async with (
            self.connection.execute(
                "SELECT coins, cps FROM Users WHERE guild_id = ? AND user_id = ?", (guild.id, user.id)
            ) as cursor,
        ):
            async for row in cursor:
                return UserProfile(coins=row[0], cps=row[1])

        return None

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
        new_profile (UserProfile): The new profile with updated values that is to be inserted

        """
        await self.connection.execute(
            """UPDATE Users
                            SET cps = ?, coins = ?
                            WHERE user_id = ? AND guild_id= ?""",
            (new_profile.cps, new_profile.coins, user.id, guild.id),
        )
        await self.connection.commit()


@contextlib.asynccontextmanager
async def open_database(path: str) -> typing.Generator[AsyncDatabase]:
    """Open a database through a shared connection.

    Arguments:
    ---------
    path (str): The path of the database to open

    """
    async with aiosqlite.connect(path) as db:
        # initialize tables if needed
        await db.execute("""CREATE TABLE IF NOT EXISTS Guilds (
                            id int,
                            channel int) STRICT""")
        await db.commit()
        await db.execute("""CREATE TABLE IF NOT EXISTS Users (
                            user_id int,
                            guild_id int,
                            cps float,
                            coins int) STRICT""")
        await db.commit()

        yield AsyncDatabase(db)
