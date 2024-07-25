import os

import discord
import dotenv
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

    async def setup_hook(self) -> None:
        """Run async setup code before our bot connects.

        Right now this just synchronizes our application commands with Discord.
        """
        self.add_view(UpgradeView())
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


@client.tree.command()
async def enable(interaction: discord.Interaction) -> None:
    """Enable the game on the current channel."""
    await interaction.response.send_message("Enabling the game on this channel")


@client.tree.command()
@app_commands.describe(message="The message to send")
async def message(interaction: discord.Interaction, message: str) -> None:
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


if __name__ == "__main__":
    client.run(TOKEN)
