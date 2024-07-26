import os

import discord
import dotenv
from database import Database, MessagePriority, UserProfile
from discord import app_commands
from discord.ui import Button, View

dotenv.load_dotenv()
TOKEN = os.environ["TOKEN"]
PRIOTIY_COST: dict[MessagePriority, int] = {MessagePriority.BOTTOM: 500, MessagePriority.MIDDLE: 2500}
# PRIORITY_COST[current priority] -> cost to upgrade
CPS_COST: dict[float, int] = {0.1: 1, 1: 10, 5: 25, 10: 50}
# CPS_COST[current_cps] -> cost to upgrade


class UpgradeView(View):
    """A discord.View subclass to handle user interactions with the update screen."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Upgrade CPS", style=discord.ButtonStyle.blurple, custom_id="upgradepersistent:cps")
    async def cps_upgrade(self, interaction: discord.Interaction, button: Button) -> None:
        """Upgrade a user's CPS."""
        button.label = "CPS Selected"
        await interaction.response.defer()
        await interaction.edit_original_response(embed=await self._create_embed(interaction), view=self)

    @discord.ui.button(
        label="Upgrade Priority",
        style=discord.ButtonStyle.blurple,
        custom_id="upgradepersistent:priority",
    )
    async def priority_upgrade(self, interaction: discord.Interaction, button: Button) -> None:
        """Upgrade a user's priority."""
        button.label = "Priority Selected"
        await interaction.response.defer()
        await interaction.edit_original_response(embed=await self._create_embed(interaction), view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="upgradepersistent:cancel")
    async def cancel(self, interaction: discord.Interaction, button: Button) -> None:
        """Cancel the upgrade process."""
        button.label = "Cancelled"
        await interaction.response.defer()
        message = await interaction.original_response()
        await interaction.edit_original_response(embed=message.embeds[0], view=self)

    async def _create_embed(self, interaction: discord.Interaction) -> discord.Embed:
        """Create a custom embed to accompany the edited message upon upgrade."""
        profile: UserProfile = await client.database.get_profile(interaction.guild, interaction.user)
        priority_cost = PRIOTIY_COST[profile.priority]
        cps_cost = CPS_COST[profile.cps]
        embed = discord.Embed(title="Upgrade menu", description="Select an upgrade to obtain")
        embed.add_field(
            name="Better CPS", value=f"Increase the amount of characters you can send per second\nCosts {cps_cost}"
        )
        embed.add_field(name="Higher Priority", value=f"Increase the priority of your messages\nCosts {priority_cost}")
        return embed


class DiscordClient(discord.Client):
    """Custom subclass of discord.py's Client for application commands."""

    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)
        self.database = Database()

    async def setup_hook(self) -> None:
        """Run async setup code before our bot connects.

        Synchronizes our application commands with Discord and sets up the bot's description.
        """
        self.add_view(UpgradeView())
        await self.tree.sync()

        await (await self.application_info()).edit(
            description=(
                "Enable a channel with </config enable:1266082362345656333>"
                "and use </send:1266082362345656332> to send messages!"
            )
        )


client = DiscordClient(intents=discord.Intents.default())
type Interaction = discord.Interaction[DiscordClient]


class Config(app_commands.Group):
    """Custom subclass of AppCommandGroup for config commands."""

    @app_commands.command()
    async def enable(self, interaction: Interaction) -> None:
        """Enable the game on the current channel."""
        if interaction.channel in await interaction.client.database.get_channels(interaction.guild):
            await interaction.response.send_message("The game is already enabled on this channel")
        else:
            await interaction.client.database.enable_channel(interaction.channel)
            await interaction.response.send_message("Enabled the game on this channel")

    @app_commands.command()
    async def disable(self, interaction: Interaction) -> None:
        """Disable the game on the current channel."""
        if interaction.channel not in await interaction.client.database.get_channels(interaction.guild):
            await interaction.response.send_message("The game is already disabled on this channel")
        else:
            await interaction.client.database.disable_channel(interaction.channel)
            await interaction.response.send_message("Disabled the game on this channel")

    @app_commands.command()
    async def reset(self, interaction: Interaction) -> None:
        """Reset access to the game for all channels."""
        for channel in await interaction.client.database.get_channels(interaction.guild):
            await interaction.client.database.disable_channel(channel)
        await interaction.response.send_message("Resetted all channels access")


@client.event
async def on_message(message: discord.Message) -> None:
    """Check every message to see if it should be deleted from an enabled channel."""
    if message.guild:
        if message.author == client.user or message.channel not in await client.database.get_channels(message.guild):
            return

        await message.delete()


@client.tree.command()
@app_commands.describe(message="The message to send")
async def send(interaction: Interaction, message: str) -> None:
    """Send a message to the current channel."""
    await interaction.response.send_message(message)


@client.tree.command()
async def upgrade(interaction: Interaction) -> None:
    """Upgrade."""
    embed = discord.Embed(title="Upgrade menu", description="Select an upgrade to obtain")
    embed.add_field(name="Better CPS", value="Increase the amount of characters you can send per second\nCosts [cost]")
    embed.add_field(name="Higher Priority", value="Increase the priority of your messages\nCosts [cost]")
    view = UpgradeView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@client.tree.command(description="Check out your stats or another user's")
@app_commands.describe(user="The user to check the stats of. Defaults to you")
async def profile(interaction: discord.Interaction, user: discord.Member = None) -> None:
    """Send a user their profile's stats."""
    user = user or interaction.user

    if user.bot:
        await interaction.response.send_message("Bots cannot play the game :(")
        return

    profile = await client.database.get_profile(interaction.guild, user)

    embed = discord.Embed(title=f"{user.display_name}'{"s" if user.display_name[-1].lower() != "s" else "" } Profile")
    embed.add_field(name="Coins", value=profile.coins)
    embed.add_field(name="CPS", value=profile.cps)
    embed.add_field(name="Message Priority", value=profile.priority.capitalize())

    await interaction.response.send_message(embed=embed)


config = Config(
    name="config", description="Configures the game", default_permissions=discord.Permissions(manage_guild=True)
)
client.tree.add_command(config)

if __name__ == "__main__":
    client.run(TOKEN)
