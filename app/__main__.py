import os

import discord
import dotenv
from database import Database
from discord import app_commands

dotenv.load_dotenv()
TOKEN = os.environ["TOKEN"]


class DiscordClient(discord.Client):
    """Custom subclass of discord.py's Client for application commands."""

    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)
        self.database = Database()

    async def setup_hook(self) -> None:
        """Run async setup code before our bot connects.

        Right now this just synchronizes our application commands with Discord.
        """
        await self.tree.sync()


client = DiscordClient(intents=discord.Intents.default())


class Config(app_commands.Group):
    """Custom subclass of AppCommandGroup for config commands."""

    @app_commands.command()
    async def enable(self, interaction: discord.Interaction) -> None:
        """Enable the game on the current channel."""
        if interaction.channel in client.database.get_enabled_channels(interaction.guild):
            await interaction.response.send_message("The game is already enabled on this channel")
        else:
            client.database.enable_channel(interaction.channel)
            await interaction.response.send_message("Enabled the game on this channel")

    @app_commands.command()
    async def disable(self, interaction: discord.Interaction) -> None:
        """Disable the game on the current channel."""
        if interaction.channel not in client.database.get_enabled_channels(interaction.guild):
            await interaction.response.send_message("The game is already disabled on this channel")
        else:
            client.database.disable_channel(interaction.channel)
            await interaction.response.send_message("Disabled the game on this channel")

    @app_commands.command()
    async def reset(self, interaction: discord.Interaction) -> None:
        """Reset access to the game for all channels."""
        for channel in client.database.get_enabled_channels(interaction.guild):
            client.database.disable_channel(channel)
        await interaction.response.send_message("Resetted all channels access")


@client.event
async def on_message(message: discord.Message) -> None:
    """Check every message to see if it should be deleted from an enabled channel."""
    if message.guild:
        if message.author == client.user or message.channel not in client.database.get_enabled_channels(message.guild):
            return

        await message.delete()


@client.tree.command()
@app_commands.describe(what="what to repeat")
async def repeat(interaction: discord.Interaction, what: str) -> None:
    """Repeats what someone says."""
    await interaction.response.send_message(
        f"Repeating after you: {what}",
        allowed_mentions=discord.AllowedMentions.none(),
    )


@client.tree.command()
@app_commands.describe(message="The message to send")
async def send(interaction: discord.Interaction, message: str) -> None:
    """Send a message to the current channel."""
    await interaction.response.send_message(message)


@client.tree.command()
async def upgrade(interaction: discord.Interaction) -> None:
    """Upgrade."""
    await interaction.response.send_message("Upgraded")


@client.tree.command(description="Check out your stats or another user's")
@app_commands.describe(user="The user to check the stats of. Defaults to you")
async def profile(interaction: discord.Interaction, user: discord.Member = None) -> None:
    """Send a user their profile's stats."""
    user = user or interaction.user

    if user.bot:
        await interaction.response.send_message("Bots cannot play the game :(")
        return

    profile = client.database.get_profile(interaction.guild, user)
    await interaction.response.send_message(
        f"""test stats for {user.display_name}:
        coins: {profile.coins}
        cps: {profile.cps}
        priority: {profile.priority}"""
    )


config = Config(
    name="config", description="Configures the game", default_permissions=discord.Permissions(manage_guild=True)
)
client.tree.add_command(config)

if __name__ == "__main__":
    client.run(TOKEN)
