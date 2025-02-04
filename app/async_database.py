import contextlib
import typing

import aiosqlite

from .database import AbstractDatabase, MessagePriority, UserProfile


class AsyncDatabase(AbstractDatabase):
    """Class to store user profile and channel data asynchronously."""

    def __init__(self, connection: aiosqlite.Connection) -> None:
        self.connection = connection

    async def enable_channel(self, guild_id: int, channel_id: int) -> None:
        """Enable the game in a channel.

        Arguments:
        ---------
        guild_id (int): The guild that the game is to be enabled in
        channel_id (int): The channel that the game is to be enabled in

        """
        await self.connection.execute(
            "INSERT INTO Guilds(id, channel) VALUES (?,?)",
            (guild_id, channel_id),
        )
        await self.connection.commit()

    async def disable_channel(self, guild_id: int, channel_id: int) -> None:
        """Disable the game in a channel.

        Arguments:
        ---------
        guild_id (int): The guild that the game is to be disabled in
        channel_id (int): The channel that the game is to be disabled in

        """
        await self.connection.execute("DELETE FROM Guilds WHERE id=? AND channel=?", (guild_id, channel_id))
        await self.connection.commit()

    async def get_channels(self, guild_id: int) -> list[int]:
        """Get all the channels that the game is in enabled in.

        Arguments:
        ---------
        guild_id (int): The guild to get all enabled channels in

        """
        async with (
            self.connection.execute("SELECT channel FROM Guilds WHERE id = ?", (guild_id,)) as cursor,
        ):
            return [row[0] async for row in cursor]

    async def remove_profile(self, guild_id: int, user_id: int) -> None:
        """Remove a profile from a specific guild.

        Arguments:
        ---------
        guild_id (int): The guild that the user is in
        user_id (int): This user whose profile is to be removed

        """
        await self.connection.execute("DELETE FROM Users WHERE user_id=? AND guild_id=?", (user_id, guild_id))
        await self.connection.commit()

    async def get_profile(self, guild_id: int, user_id: int) -> UserProfile:
        """Get a profile from a specific guild, if the user object does not have the guild already attached to it.

        Arguments:
        ---------
        guild_id (int): The guild that will be checked
        user_id (int): The user whose profile that will be returned

        """
        async with (
            self.connection.execute(
                "SELECT coins, cps, priority FROM Users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
            ) as cursor,
        ):
            async for row in cursor:
                return UserProfile(coins=row[0], cps=row[1], priority=MessagePriority(row[2]))

        return UserProfile()

    async def update_profile(self, guild_id: int, user_id: int, new_profile: UserProfile) -> None:
        """Replace a profile with a new profile with updated values.

        Arguments:
        ---------
        guild_id (int): The guild in which the profile is in
        user_id (int): The user whose profile will be updated
        new_profile (UserProfile): The new profile with updated values that is to be inserted.

        """
        await self.connection.execute(
            """INSERT INTO Users(user_id, guild_id, cps, coins, priority) VALUES (?1, ?2, ?3, ?4, ?5)
                    ON CONFLICT(user_id, guild_id) DO UPDATE
                            SET cps = ?3, coins = ?4, priority = ?5""",
            (user_id, guild_id, new_profile.cps, new_profile.coins, str(new_profile.priority)),
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
                            channel int,
                            PRIMARY KEY (id, channel)) STRICT""")
        await db.commit()
        await db.execute("""CREATE TABLE IF NOT EXISTS Users (
                            user_id int,
                            guild_id int,
                            cps int NOT NULL,
                            coins int NOT NULL,
                            priority text NOT NULL,
                            PRIMARY KEY (user_id, guild_id)) STRICT""")
        await db.commit()

        yield AsyncDatabase(db)
