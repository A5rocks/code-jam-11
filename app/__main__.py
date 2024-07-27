import asyncio
import contextlib
import os

import discord
import dotenv
from async_database import open_database
from database import AbstractDatabase, MessagePriority, UserProfile
from discord import app_commands
from discord.ui import Button, View
from sender import send as send_implementation

dotenv.load_dotenv()
TOKEN = os.environ["TOKEN"]
PRIOTIY_COST: dict[MessagePriority, int] = {MessagePriority.BOTTOM: 500, MessagePriority.MIDDLE: 2500}
# PRIORITY_COST[current priority] -> cost to upgrade
CPS_COST: dict[float, int] = {0.1: 1, 1: 10, 5: 25, 10: 50}
# CPS_COST[current_cps] -> cost to upgrade

type Interaction = discord.Interaction[DiscordClient]


class UpgradeView(View):
    """A discord.View subclass to handle user interactions with the update screen."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Upgrade CPS", style=discord.ButtonStyle.blurple, custom_id="upgradepersistent:cps")
    async def cps_upgrade(self, interaction: Interaction, button: Button) -> None:
        """Upgrade a user's CPS."""
        button.label = "CPS Selected"
        await interaction.response.defer()
        await interaction.edit_original_response(embed=await self._create_embed(interaction), view=self)

    @discord.ui.button(
        label="Upgrade Priority",
        style=discord.ButtonStyle.blurple,
        custom_id="upgradepersistent:priority",
    )
    async def priority_upgrade(self, interaction: Interaction, button: Button) -> None:
        """Upgrade a user's priority."""
        button.label = "Priority Selected"
        await interaction.response.defer()
        await interaction.edit_original_response(embed=await self._create_embed(interaction), view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="upgradepersistent:cancel")
    async def cancel(self, interaction: Interaction, button: Button) -> None:
        """Cancel the upgrade process."""
        button.label = "Cancelled"
        await interaction.response.defer()
        message = await interaction.original_response()
        await interaction.edit_original_response(embed=message.embeds[0], view=self)

    async def _create_embed(self, interaction: Interaction) -> discord.Embed:
        """Create a custom embed to accompany the edited message upon upgrade."""
        profile: UserProfile = await interaction.client.database.get_profile(interaction.guild.id, interaction.user.id)
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

    def __init__(self, *, intents: discord.Intents, db: AbstractDatabase) -> None:
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)
        self.database = db

    async def setup_hook(self) -> None:
        """Run async setup code before our bot connects.

        Synchronizes our application commands with Discord and sets up the bot's description.
        """
        self.add_view(UpgradeView())
        app_commands = await self.tree.sync()

        command_id_map = {cmd.name: cmd.id for cmd in app_commands}
        await (await self.application_info()).edit(
            description=(
                f"Enable a channel with </config enable:{command_id_map["config"]}> "
                f"and use </send:{command_id_map["send"]}> to send messages!"
            )
        )

    async def on_message(self, message: discord.Message) -> None:
        """Check every message to see if it should be deleted from an enabled channel."""
        if message.guild:
            if message.author == self.user or message.channel.id not in await self.database.get_channels(
                message.guild.id
            ):
                return

            await message.delete()


class Config(app_commands.Group):
    """Custom subclass of AppCommandGroup for config commands."""

    @app_commands.command()
    async def enable(self, interaction: Interaction) -> None:
        """Enable the game on the current channel."""
        if interaction.channel.id in await interaction.client.database.get_channels(interaction.guild.id):
            await interaction.response.send_message("The game is already enabled on this channel")
        else:
            await interaction.client.database.enable_channel(interaction.guild.id, interaction.channel.id)
            await interaction.response.send_message("Enabled the game on this channel")

    @app_commands.command()
    async def disable(self, interaction: Interaction) -> None:
        """Disable the game on the current channel."""
        if interaction.channel.id not in await interaction.client.database.get_channels(interaction.guild.id):
            await interaction.response.send_message("The game is already disabled on this channel")
        else:
            await interaction.client.database.disable_channel(interaction.guild.id, interaction.channel.id)
            await interaction.response.send_message("Disabled the game on this channel")

    @app_commands.command()
    async def reset(self, interaction: Interaction) -> None:
        """Reset access to the game for all channels."""
        for channel_id in await interaction.client.database.get_channels(interaction.guild.id):
            await interaction.client.database.disable_channel(interaction.guild.id, channel_id)
        await interaction.response.send_message("Resetted all channels access")


@app_commands.describe(message="The message to send")
async def send(interaction: Interaction, message: str) -> None:
    """Send a message to the current channel."""
    if interaction.channel.id not in await interaction.client.database.get_channels(interaction.guild.id):
        await interaction.response.send_message("Game is not enabled in this channel!")
        return

    async def cps(user_id: int) -> float:
        profile = await interaction.client.database.get_profile(interaction.guild.id, user_id)
        return profile.cps

    if await send_implementation(interaction.channel.id, interaction.user.id, message, interaction.channel.send, cps):
        await interaction.response.send_message("That is too much text to send at once.", ephemeral=True)
        return

    await interaction.response.send_message("Sent!", ephemeral=True)


async def upgrade(interaction: Interaction) -> None:
    """Upgrade."""
    embed = discord.Embed(title="Upgrade menu", description="Select an upgrade to obtain")
    embed.add_field(name="Better CPS", value="Increase the amount of characters you can send per second\nCosts [cost]")
    embed.add_field(name="Higher Priority", value="Increase the priority of your messages\nCosts [cost]")
    view = UpgradeView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@app_commands.describe(user="The user to check the stats of. Defaults to you")
async def profile(interaction: discord.Interaction, user: discord.Member = None) -> None:
    """Send a user their profile's stats."""
    user = user or interaction.user

    if user.bot:
        await interaction.response.send_message("Bots cannot play the game :(")
        return

    profile = await interaction.client.database.get_profile(interaction.guild.id, user.id)

    embed = discord.Embed(title=f"{user.display_name}'{"s" if user.display_name[-1].lower() != "s" else "" } Profile")
    embed.add_field(name="Coins", value=profile.coins)
    embed.add_field(name="CPS", value=profile.cps)
    embed.add_field(name="Message Priority", value=profile.priority.capitalize())

    await interaction.response.send_message(embed=embed)


config = Config(
    name="config", description="Configures the game", default_permissions=discord.Permissions(manage_guild=True)
)


async def main() -> None:
    """Async entrypoint for the bot."""
    async with open_database("bot.db") as db:
        client = DiscordClient(intents=discord.Intents.default(), db=db)

        client.tree.command()(send)
        client.tree.command()(upgrade)
        client.tree.command(description="Check out your stats or another user's")(profile)
        client.tree.add_command(config)
        discord.utils.setup_logging()

        async with client:
            await client.start(TOKEN)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
