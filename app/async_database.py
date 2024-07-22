import aiosqlite
import discord
from database import UserProfile


class AsyncDatabase:
    """Class to store user profile and channel data asynchronously."""

    db_path = "demo.db"

    async def setup(self) -> None:
        """Init for all asynchronous work for database."""
        async with aiosqlite.connect(self.db_path) as db:
            # initialize tables
            await db.execute("""CREATE TABLE IF NOT EXISTS Guilds (
                                id int,
                                channel int,
                                enabled bool)""")
            await db.commit()
            await db.execute("""CREATE TABLE IF NOT EXISTS Users (
                                user_id int,
                                guild_id int,
                                cps int,
                                coins int)""")
            await db.commit()

    async def add_guild(self, guild: discord.Guild) -> None:
        """Add a guild to the database.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the user is in

        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO Guilds(id, channel, enabled) VALUES (?,?,?)",
                (guild.id, 0, False),
            )
            await db.commit()

    async def enable_channel(self, channel: discord.TextChannel) -> None:
        """Enable the game in a channel.

        Arguments:
        ---------
        channel (discord.TextChannel): The channel that the game is to be enabled in

        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE Guilds
                                SET channel = ?, enabled= ?
                                WHERE id = ?""",
                (channel.id, True, channel.guild.id),
            )
        await db.commit()

    async def disable_channel(self, channel: discord.TextChannel) -> None:
        """Disable the game in a channel.

        Arguments:
        ---------
        channel (discord.TextChannel): The channel that the game is to be disabled in

        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE Guilds
                                SET channel = ?, enabled= ?
                                WHERE id = ?""",
                (channel.id, False, channel.guild.id),
            )
        await db.commit()

    async def get_active_profiles(self, guild: discord.Guild) -> list[UserProfile]:
        """Get all the profiles that the game is in enabled in.

        Arguments:
        ---------
        guild (discord.Guild): The guild to check all enabled profiles in

        """
        active_profiles: list[UserProfile] = []

        async with (
            aiosqlite.connect(self.db_path) as db,
            db.execute("SELECT * FROM Users WHERE guild_id = ?", (guild.id)) as cursor,
        ):
            async for row in cursor:
                active_profiles = [UserProfile(coins=row[3], cps=row[2]) for row in cursor]
        return active_profiles

    async def add_profile(self, guild: discord.Guild, user: discord.Member) -> None:
        """Add a profile to a specific guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the user is in
        user (discord.User): This user whose profile is to be added

        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO Users(user_id, guild_id, cps, coins) VALUES (?,?,?,?)",
                (user.id, guild.id, UserProfile().cps, UserProfile().coins),
            )
            await db.commit()

    async def remove_profile(self, guild: discord.Guild, user: discord.User) -> None:
        """Remove a profile from a specific guild.

        Arguments:
        ---------
        guild (discord.Guild): The guild that the user is in
        user (discord.User): This user whose profile is to be removed

        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM Users WHERE user_id=? AND guild_id=?", (user.id, guild.id))
            await db.commit()

    async def get_profile(self, guild: discord.Guild, user: discord.Member) -> UserProfile | None:
        """Get a profile from a specific guild, if the user object does not have the guild already attached to it.

        Arguments:
        ---------
        guild (discord.Guild): The guild that will be checked
        user (discord.User): The user whose profile that will be returned

        """
        async with (
            aiosqlite.connect(self.db_path) as db,
            db.execute("SELECT * FROM Users WHERE guild_id = ? AND user_id = ?", (guild.id, user.id)) as cursor,
        ):
            async for row in cursor:
                return UserProfile(coins=row[3], cps=row[2])

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
        new_profile (UserProfile): The new profile with updated values that is to be inserted.

        If this is not passed in a value of None is used and the profile is not changed

        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE Users
                                SET cps = ?, coins = ?
                                WHERE user_id = ? AND guild_id= ?""",
                (new_profile.cps, new_profile.coins, user.id, guild.id),
            )
        await db.commit()
