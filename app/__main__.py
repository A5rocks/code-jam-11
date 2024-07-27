import asyncio
import contextlib
import os
from enum import IntEnum

import discord
import dotenv
from async_database import open_database
from database import AbstractDatabase, MessagePriority, UserProfile
from discord import app_commands
from discord.ui import Button, View

from app.sender import send as send_implementation

dotenv.load_dotenv()
TOKEN = os.environ["TOKEN"]
PRIORITY_COST: dict[MessagePriority, int] = {MessagePriority.BOTTOM: 500, MessagePriority.MIDDLE: 2500}
# PRIORITY_COST[current priority] -> cost to upgrade
CPS_COST: dict[float, int] = {0.1: 1, 1: 10, 5: 25, 10: 50}


# CPS_COST[current_cps] -> cost to upgrade
# status codes below
class StatusCode(IntEnum):
    """Status code to determine upgrade behavior."""

    SUCCESS = 30
    NOT_ENOUGH_COINS = 33
    NOT_ENOUGH_COINS_BEFORE_COMPLETION = 34
    MAXIMUM_REACHED = 35
    MAXIMUM_REACHED_BEFORE_COMPLETION = 36


CPS_PIPELINE: list[float] = [*list(CPS_COST.keys()), 2000]
PRIORITY_PIPELINE: list[MessagePriority] = [*list(PRIORITY_COST.keys()), MessagePriority.TOP]

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
        new_profile, status_code = await self._upgrade_cps(interaction)
        await self._handle_status_code(interaction, status_code)
        await interaction.client.database.update_profile(interaction.guild, interaction.user, new_profile)
        await interaction.edit_original_response(embed=await self.create_embed(interaction), view=self)

    @discord.ui.button(
        label="Upgrade Priority",
        style=discord.ButtonStyle.blurple,
        custom_id="upgradepersistent:priority",
    )
    async def priority_upgrade(self, interaction: Interaction, button: Button) -> None:
        """Upgrade a user's priority."""
        button.label = "Priority Selected"
        await interaction.response.defer()
        new_profile, status_code = await self._upgrade_priority(interaction)
        await self._handle_status_code(interaction, status_code)
        await interaction.client.database.update_profile(interaction.guild, interaction.user, new_profile)
        await interaction.edit_original_response(embed=await self.create_embed(interaction), view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="upgradepersistent:cancel")
    async def cancel(self, interaction: Interaction, button: Button) -> None:
        """Cancel the upgrade process."""
        button.label = "Cancelled"
        await interaction.response.defer()
        message = await interaction.original_response()
        await interaction.edit_original_response(embed=message.embeds[0], view=self)

    @discord.ui.button(
        label="CPS Upgrade 10x", style=discord.ButtonStyle.gray, row=1, custom_id="upgradepersistent:cps10x"
    )
    async def cps_upgrade_ten(self, interaction: Interaction, button: Button) -> None:
        """Upgrade CPS ten times."""
        button.label = "CPS 10x Selected"
        await interaction.response.defer()
        new_profile, status_code = await self._upgrade_cps(interaction, 10)
        await self._handle_status_code(interaction, status_code)
        await interaction.client.database.update_profile(interaction.guild, interaction.user, new_profile)
        await interaction.edit_original_response(embed=await self.create_embed(interaction), view=self)

    @staticmethod
    async def create_embed(interaction: Interaction) -> discord.Embed:
        """Create a custom embed to accompany the edited message upon upgrade."""
        profile: UserProfile = await interaction.client.database.get_profile(interaction.guild, interaction.user)
        priority_cost: int = PRIORITY_COST[profile.priority]
        cps_cost: int = CPS_COST[profile.cps]
        embed = discord.Embed(title="Upgrade menu", description="Select an upgrade to obtain")
        embed.add_field(
            name="Better CPS", value=f"Increase the amount of characters you can send per second\nCosts {cps_cost}"
        )
        embed.add_field(name="Higher Priority", value=f"Increase the priority of your messages\nCosts {priority_cost}")
        return embed

    async def _upgrade_priority(self, interaction: Interaction) -> tuple[UserProfile, StatusCode]:
        """Upgrade the priority of the user."""
        profile: UserProfile = await interaction.client.database.get_profile(interaction.guild, interaction.user)
        priority_cost: int = PRIORITY_COST[profile.priority]
        if profile.coins < priority_cost:
            return (profile, StatusCode.NOT_ENOUGH_COINS)
        if profile.priority == MessagePriority.TOP:
            return (profile, StatusCode.MAXIMUM_REACHED)
        new_coins: int = profile.coins - priority_cost
        new_priority: MessagePriority = PRIORITY_PIPELINE[PRIORITY_PIPELINE.index(profile.priority) + 1]
        new_profile: UserProfile = UserProfile(coins=new_coins, priority=new_priority)
        return (new_profile, StatusCode.SUCCESS)

    async def _upgrade_cps(self, interaction: Interaction, iterations: int = 1) -> tuple[UserProfile, StatusCode]:
        """Upgrade the cps of the user."""
        profile: UserProfile = await interaction.client.database.get_profile(interaction.guild, interaction.user)
        cps_cost: int = CPS_COST[profile.cps]
        reloop = False
        new_coins = profile.coins
        new_cps = profile.cps
        for var in range(iterations):
            if profile.coins < cps_cost and not reloop:
                return profile, StatusCode.NOT_ENOUGH_COINS
            if profile.coins < cps_cost and reloop:
                await interaction.followup.send(
                    f"Upgraded {var + 1} times before running out of coins.", ephemeral=True
                )
                return (
                    UserProfile(coins=new_coins, cps=new_cps, priority=profile.priority),
                    StatusCode.NOT_ENOUGH_COINS_BEFORE_COMPLETION,
                )
            if profile.cps == CPS_PIPELINE[-1] and not reloop:  # replace with number that should be the maximum
                return profile, StatusCode.MAXIMUM_REACHED
            if profile.cps == CPS_PIPELINE[-1] and reloop:
                await interaction.followup.send(
                    f"Upgraded {var + 1} times before reaching maximum upgrade", ephemeral=True
                )
                return (
                    UserProfile(coins=new_coins, cps=new_cps, priority=profile.priority),
                    StatusCode.MAXIMUM_REACHED_BEFORE_COMPLETION,
                )

            new_coins = new_coins - cps_cost
            new_cps = CPS_PIPELINE[CPS_PIPELINE.index(profile.cps) + 1]
            cps_cost: int = CPS_COST[new_cps]
            reloop = True

        return UserProfile(coins=new_coins, cps=new_cps, priority=profile.priority), StatusCode.SUCCESS

    async def _handle_status_code(self, interaction: Interaction, status_code: StatusCode) -> None:
        """Send an ephemeral message to the user upon completion of an upgrade, depending on status_code.

        Two of the status codes are handled by _upgrade_cps
        """
        if status_code == StatusCode.NOT_ENOUGH_COINS:
            await interaction.followup.send(
                "You do not have enough coins to proceed with this upgrade", ephemeral=True
            )
        elif status_code == StatusCode.MAXIMUM_REACHED:
            await interaction.followup.send("You already have the maximum upgrade for this category", ephemeral=True)
        elif status_code == StatusCode.SUCCESS:
            await interaction.followup.send("Your upgrade was successful!", ephemeral=True)


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
                message.guild
            ):
                return

            await message.delete()


class Config(app_commands.Group):
    """Custom subclass of AppCommandGroup for config commands."""

    @app_commands.command()
    async def enable(self, interaction: Interaction) -> None:
        """Enable the game on the current channel."""
        if interaction.channel.id in await interaction.client.database.get_channels(interaction.guild):
            await interaction.response.send_message("The game is already enabled on this channel")
        else:
            await interaction.client.database.enable_channel(interaction.channel)
            await interaction.response.send_message("Enabled the game on this channel")

    @app_commands.command()
    async def disable(self, interaction: Interaction) -> None:
        """Disable the game on the current channel."""
        if interaction.channel.id not in await interaction.client.database.get_channels(interaction.guild):
            await interaction.response.send_message("The game is already disabled on this channel")
        else:
            await interaction.client.database.disable_channel(interaction.guild, interaction.channel.id)
            await interaction.response.send_message("Disabled the game on this channel")

    @app_commands.command()
    async def reset(self, interaction: Interaction) -> None:
        """Reset access to the game for all channels."""
        for channel_id in await interaction.client.database.get_channels(interaction.guild):
            await interaction.client.database.disable_channel(interaction.guild, channel_id)
        await interaction.response.send_message("Resetted all channels access")


@app_commands.describe(message="The message to send")
async def send(interaction: Interaction, message: str) -> None:
    """Send a message to the current channel."""
    if interaction.channel.id not in await interaction.client.database.get_channels(interaction.guild):
        await interaction.response.send_message("Game is not enabled in this channel!")
        return

    await send_implementation(interaction.client, interaction.channel, interaction.user, message)
    await interaction.response.send_message("Sent!", ephemeral=True)


async def upgrade(interaction: Interaction) -> None:
    """Upgrade."""
    view = UpgradeView()
    await interaction.response.send_message(embed=await view.create_embed(interaction), view=view, ephemeral=True)


@app_commands.describe(user="The user to check the stats of. Defaults to you")
async def profile(interaction: Interaction, user: discord.Member = None) -> None:
    """Send a user their profile's stats."""
    user = user or interaction.user

    if user.bot:
        await interaction.response.send_message("Bots cannot play the game :(")
        return

    profile = await interaction.client.database.get_profile(interaction.guild, user)

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
