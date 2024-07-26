import contextlib
import typing

import aiosqlite
import discord
from database import AbstractDatabase, UserProfile


class AsyncDatabase(AbstractDatabase):
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

    async def disable_channel(self, guild: discord.Guild, channel_id: int) -> None:
        """Disable the game in a channel.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the game is to be disabled in
        channel_id (int): The channel that the game is to be disabled in

        """
        await self.connection.execute("DELETE FROM Guilds WHERE id=? AND channel=?", (guild.id, channel_id))
        await self.connection.commit()

    async def get_channels(self, guild: discord.Guild) -> list[int]:
        """Get all the channels that the game is enabled in for a guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild to check all enabled channels in

        """
        async with (
            self.connection.execute("SELECT channel FROM Guilds WHERE id = ?", (guild.id,)) as cursor,
        ):
            return [row[0] async for row in cursor]

    async def add_profile(
        self, guild: discord.Guild, user: discord.User, user_profile: UserProfile | None = None
    ) -> None:
        """Add a profile to a specific guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the user is in
        user (discord.User): The discord user to be added
        user_profile (UserProfile | None): The UserProfile data to be added, if None, a new instance is created

        """
        if user_profile is None:
            user_profile = UserProfile()

        await self.connection.execute(
            "INSERT INTO Users(user_id, guild_id, cps, coins) VALUES (?,?,?,?)",
            (user.id, guild.id, int(user_profile.cps * 10), user_profile.coins),
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

    async def get_profile(self, guild: discord.Guild, user: discord.User) -> UserProfile:
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
                return UserProfile(coins=row[0], cps=row[1] / 10)

        return UserProfile()

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
            (int(new_profile.cps * 10), new_profile.coins, user.id, guild.id),
        )
        await self.connection.commit()


@contextlib.asynccontextmanager
async def open_database(path: str) -> typing.AsyncIterator[AsyncDatabase]:
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
                            cps int,
                            coins int) STRICT""")
        await db.commit()

        yield AsyncDatabase(db)
