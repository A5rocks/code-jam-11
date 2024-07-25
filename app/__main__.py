import os

import discord
import dotenv
from database import Database
from discord import app_commands
from discord.ui import Button, View

dotenv.load_dotenv()
TOKEN = os.environ["TOKEN"]


class UpgradeView(View):
    """A discord.View subclass to handle user interactions with the update screen."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Upgrade CPS", style=discord.ButtonStyle.blurple, custom_id="upgradepersistent:cps")
    async def cps_upgrade(self, interaction: discord.Interaction, button: Button) -> None:
        """Upgrade a user's CPS."""
        button.label = "CPS Selected"
        await interaction.response.defer()
        message = await interaction.original_response()
        await interaction.edit_original_response(embed=message.embeds[0], view=self)

    @discord.ui.button(
        label="Upgrade Priority",
        style=discord.ButtonStyle.blurple,
        custom_id="upgradepersistent:priority",
    )
    async def priority_upgrade(self, interaction: discord.Interaction, button: Button) -> None:
        """Upgrade a user's priority."""
        button.label = "Priority Selected"
        await interaction.response.defer()
        message = await interaction.original_response()
        await interaction.edit_original_response(embed=message.embeds[0], view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="upgradepersistent:cancel")
    async def cancel(self, interaction: discord.Interaction, button: Button) -> None:
        """Cancel the upgrade process."""
        button.label = "Cancelled"
        await interaction.response.defer()
        message = await interaction.original_response()
        await interaction.edit_original_response(embed=message.embeds[0], view=self)


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
        self.add_view(UpgradeView())
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
    embed = discord.Embed(title="Upgrade menu", description="Select an upgrade to obtain")
    embed.add_field(name="Better CPS", value="Increase the amount of characters you can send per second\nCosts [cost]")
    embed.add_field(name="Higher Priority", value="Increase the priority of your messages\nCosts [cost]")
    view = UpgradeView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


config = Config(
    name="config", description="Configures the game", default_permissions=discord.Permissions(manage_guild=True)
)
client.tree.add_command(config)

if __name__ == "__main__":
    client.run(TOKEN)
