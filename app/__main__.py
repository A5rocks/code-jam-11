import os

import discord
import dotenv
from discord import app_commands

dotenv.load_dotenv()
TOKEN = os.environ["TOKEN"]


class DiscordClient(discord.Client):
    """Custom subclass of discord.py's Client for application commands."""

    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        """Run async setup code before our bot connects.

        Right now this just synchronizes our application commands with Discord.
        """
        await self.tree.sync()


client = DiscordClient(intents=discord.Intents.default())


@client.tree.command()
@app_commands.describe(what="what to repeat")
async def repeat(interaction: discord.Interaction, what: str) -> None:
    """Repeats what someone says."""
    await interaction.response.send_message(
        f"Repeating after you: {what}",
        allowed_mentions=discord.AllowedMentions.none(),
    )


@client.tree.command(name="enable")
async def enable(interaction: discord.Interaction):
    """Enables the game on the current channel."""
    await interaction.response.send_message("Enabling the game on this channel")


@client.tree.command(name="message")
@app_commands.describe(message="The message to send")
async def message(interaction: discord.Interaction, message: str) -> None:
    """Sends a message to the current channel."""
    await interaction.response.send_message(message)


@client.tree.command(name="upgrade")
async def upgrade(interaction: discord.Interaction):
    """Successfully upgraded."""
    await interaction.response.send_message("Upgraded")


if __name__ == "__main__":
    client.run(TOKEN)
