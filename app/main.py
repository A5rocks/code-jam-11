import math
import os
import typing
from enum import Enum, auto

import discord
import dotenv
from discord import app_commands
from discord.ui import Button, View

from .async_database import open_database
from .database import AbstractDatabase, MessagePriority, UserProfile
from .sender import send as send_implementation

dotenv.load_dotenv()
TOKEN = os.environ["TOKEN"]
PRIORITY_COST: dict[MessagePriority, int] = {
    MessagePriority.BOTTOM: 500,
    MessagePriority.MIDDLE: 2500,
    MessagePriority.TOP: -1,
}
MAXIMUM_CPS = 20000
PRIORITY_PIPELINE: list[MessagePriority] = list(PRIORITY_COST.keys())


# PRIORITY_COST[current priority] -> cost to upgrade
class StatusCode(Enum):
    """Status code to determine upgrade behavior."""

    SUCCESS = auto()
    NOT_ENOUGH_COINS = auto()
    NOT_ENOUGH_COINS_BEFORE_COMPLETION = auto()
    MAXIMUM_REACHED = auto()
    MAXIMUM_REACHED_BEFORE_COMPLETION = auto()


def get_cps_cost(cur_cps: float) -> int:
    """Get the cost to upgrade with the current cps."""
    if cur_cps == MAXIMUM_CPS:
        return -1
    cur_cps /= 10  # we store cps as e.g `11` instead of `1.1` for precision reasons
    cost = cur_cps * (math.pow(1.5, cur_cps / 30) - cur_cps / 5 + 30 - (20 / cur_cps) * math.sin(0.7 * cur_cps)) / 10
    return math.ceil(cost)


Interaction: typing.TypeAlias = "discord.Interaction[DiscordClient]"


class UpgradeView(View):
    """A discord.View subclass to handle user interactions with the update screen."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Upgrade CPS", style=discord.ButtonStyle.blurple, custom_id="upgradepersistent:cps")
    async def cps_upgrade(self, interaction: Interaction, _: Button[typing.Self]) -> None:
        """Upgrade a user's CPS."""
        if not interaction.guild:
            await interaction.response.send_message("This needs to be used in a guild")
            return

        await interaction.response.defer()
        new_profile, status_code = await self._upgrade_cps(interaction)
        await self._handle_status_code(interaction, status_code)
        await interaction.client.database.update_profile(interaction.guild.id, interaction.user.id, new_profile)
        await interaction.edit_original_response(embed=await self.create_embed(interaction), view=self)

    @discord.ui.button(
        label="Upgrade Priority",
        style=discord.ButtonStyle.blurple,
        custom_id="upgradepersistent:priority",
    )
    async def priority_upgrade(self, interaction: Interaction, _: Button[typing.Self]) -> None:
        """Upgrade a user's priority."""
        if not interaction.guild:
            await interaction.response.send_message("This needs to be used in a guild")
            return

        await interaction.response.defer()
        new_profile, status_code = await self._upgrade_priority(interaction)
        await self._handle_status_code(interaction, status_code)
        await interaction.client.database.update_profile(interaction.guild.id, interaction.user.id, new_profile)
        await interaction.edit_original_response(embed=await self.create_embed(interaction), view=self)

    @discord.ui.button(
        label="CPS Upgrade 10x", style=discord.ButtonStyle.gray, row=1, custom_id="upgradepersistent:cps10x"
    )
    async def cps_upgrade_ten(self, interaction: Interaction, _: Button[typing.Self]) -> None:
        """Upgrade CPS ten times."""
        if not interaction.guild:
            await interaction.response.send_message("This needs to be used in a guild")
            return

        await interaction.response.defer()
        new_profile, status_code = await self._upgrade_cps(interaction, 10)
        await self._handle_status_code(interaction, status_code)
        await interaction.client.database.update_profile(interaction.guild.id, interaction.user.id, new_profile)
        await interaction.edit_original_response(embed=await self.create_embed(interaction), view=self)

    @staticmethod
    async def create_embed(interaction: Interaction) -> discord.Embed:
        """Create a custom embed to accompany the edited message upon upgrade."""
        if not interaction.guild:
            raise AssertionError

        profile: UserProfile = await interaction.client.database.get_profile(interaction.guild.id, interaction.user.id)
        priority_cost = PRIORITY_COST[profile.priority]
        cps_cost = get_cps_cost(profile.cps)
        embed = discord.Embed(title="Upgrade menu", description="Select an upgrade to obtain")
        if cps_cost != -1:
            embed.add_field(
                name="Better CPS", value=f"Increase the amount of characters you can send per second\nCosts {cps_cost}"
            )
        else:
            embed.add_field(
                name="Better CPS", value="Increase the amount of characters you can send per second\nMAXED OUT"
            )
        if priority_cost != -1:
            embed.add_field(
                name="Higher Priority", value=f"Increase the priority of your messages\nCosts {priority_cost}"
            )
        else:
            embed.add_field(name="Higher Priority", value="Increase the priority of your messages\nMAXED OUT")

        return embed

    async def _upgrade_priority(self, interaction: Interaction) -> tuple[UserProfile, StatusCode]:
        """Upgrade the priority of the user."""
        if not interaction.guild:
            raise AssertionError

        profile = await interaction.client.database.get_profile(interaction.guild.id, interaction.user.id)
        priority_cost = PRIORITY_COST[profile.priority]
        if profile.coins < priority_cost:
            return (profile, StatusCode.NOT_ENOUGH_COINS)
        if profile.priority == MessagePriority.TOP:
            return (profile, StatusCode.MAXIMUM_REACHED)
        new_coins = profile.coins - priority_cost
        new_priority = PRIORITY_PIPELINE[PRIORITY_PIPELINE.index(profile.priority) + 1]
        new_profile = UserProfile(coins=new_coins, priority=new_priority)
        return (new_profile, StatusCode.SUCCESS)

    async def _upgrade_cps(self, interaction: Interaction, iterations: int = 1) -> tuple[UserProfile, StatusCode]:
        """Upgrade the cps of the user."""
        if not interaction.guild:
            raise AssertionError

        profile = await interaction.client.database.get_profile(interaction.guild.id, interaction.user.id)
        cps_cost = get_cps_cost(profile.cps)
        reloop = False
        new_coins = profile.coins
        new_cps = profile.cps

        for var in range(iterations):
            if new_coins < cps_cost and not reloop:
                return profile, StatusCode.NOT_ENOUGH_COINS
            if new_coins < cps_cost and reloop:
                await interaction.followup.send(
                    f"Upgraded {var + 1} times before running out of coins.", ephemeral=True
                )
                return (
                    UserProfile(coins=new_coins, cps=new_cps, priority=profile.priority),
                    StatusCode.NOT_ENOUGH_COINS_BEFORE_COMPLETION,
                )
            if new_cps == MAXIMUM_CPS and not reloop:
                return profile, StatusCode.MAXIMUM_REACHED
            if new_cps == MAXIMUM_CPS and reloop:
                await interaction.followup.send(
                    f"Upgraded {var + 1} times before reaching maximum upgrade", ephemeral=True
                )
                return (
                    UserProfile(coins=new_coins, cps=new_cps, priority=profile.priority),
                    StatusCode.MAXIMUM_REACHED_BEFORE_COMPLETION,
                )

            new_coins -= cps_cost
            new_cps += 1
            cps_cost = get_cps_cost(new_cps)
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
                message.guild.id
            ):
                return

            await message.delete()


class Config(app_commands.Group):
    """Custom subclass of AppCommandGroup for config commands."""

    @app_commands.command()
    async def enable(self, interaction: Interaction) -> None:
        """Enable the game on the current channel."""
        if not interaction.guild or not interaction.channel:
            await interaction.response.send_message("This needs to be used in a guild")
            return

        if interaction.channel.id in await interaction.client.database.get_channels(interaction.guild.id):
            await interaction.response.send_message("The game is already enabled on this channel", ephemeral=True)
        else:
            await interaction.client.database.enable_channel(interaction.guild.id, interaction.channel.id)
            await interaction.response.send_message("Enabled the game on this channel")

    @app_commands.command()
    async def disable(self, interaction: Interaction) -> None:
        """Disable the game on the current channel."""
        if not interaction.guild or not interaction.channel:
            await interaction.response.send_message("This needs to be used in a guild")
            return

        if interaction.channel.id not in await interaction.client.database.get_channels(interaction.guild.id):
            await interaction.response.send_message("The game is already disabled on this channel")
        else:
            await interaction.client.database.disable_channel(interaction.guild.id, interaction.channel.id)
            await interaction.response.send_message("Disabled the game on this channel")

    @app_commands.command()
    async def reset(self, interaction: Interaction) -> None:
        """Reset access to the game for all channels."""
        if not interaction.guild:
            await interaction.response.send_message("This needs to be used in a guild")
            return

        for channel_id in await interaction.client.database.get_channels(interaction.guild.id):
            await interaction.client.database.disable_channel(interaction.guild.id, channel_id)
        await interaction.response.send_message("Resetted all channels access")


@app_commands.describe(message="The message to send")
async def send(interaction: Interaction, message: str) -> None:
    """Send a message to the current channel."""
    if not interaction.guild:
        await interaction.response.send_message("This needs to be used in a guild")
        return

    if not isinstance(interaction.channel, discord.abc.Messageable):
        await interaction.response.send_message("This isn't possible")
        return

    if interaction.channel.id not in await interaction.client.database.get_channels(interaction.guild.id):
        await interaction.response.send_message("Game is not enabled in this channel!")
        return

    async def cps(user_id: int) -> float:
        if not interaction.guild:
            raise AssertionError

        profile = await interaction.client.database.get_profile(interaction.guild.id, user_id)
        return profile.cps / 10

    async def add_coin(user_id: int) -> None:
        if not interaction.guild:
            raise AssertionError

        profile = await interaction.client.database.get_profile(interaction.guild.id, user_id)
        await interaction.client.database.update_profile(
            interaction.guild.id,
            user_id,
            UserProfile(priority=profile.priority, coins=profile.coins + 1, cps=profile.cps),
        )

    if await send_implementation(
        interaction.channel.id, interaction.user.id, message, interaction.channel.send, cps, add_coin
    ):
        await interaction.response.send_message("That is too much text to send at once.", ephemeral=True)
        return

    await interaction.response.send_message("Sent!", ephemeral=True)


async def upgrade(interaction: Interaction) -> None:
    """Upgrade."""
    if not interaction.guild:
        await interaction.response.send_message("This needs to be used in a guild")
        return

    view = UpgradeView()
    await interaction.response.send_message(embed=await view.create_embed(interaction), view=view, ephemeral=True)


@app_commands.describe(user="The user to check the stats of. Defaults to you")
async def profile(interaction: Interaction, user: discord.User | None = None) -> None:
    """Send a user their profile's stats."""
    if not interaction.guild or not interaction.channel:
        await interaction.response.send_message("This needs to be used in a guild")
        return

    person = user or interaction.user

    if person.bot and interaction.channel.id in await interaction.client.database.get_channels(interaction.guild.id):
        await interaction.response.send_message("Bots cannot play the game :(", ephemeral=True)
        return
    if person.bot:
        await interaction.response.send_message("Bots cannot play the game :(")
        return

    profile = await interaction.client.database.get_profile(interaction.guild.id, person.id)

    embed = discord.Embed(
        title=f"{person.display_name}'{"s" if person.display_name[-1].lower() != "s" else ""} Profile"
    )
    embed.add_field(name="Coins", value=profile.coins)
    embed.add_field(name="CPS", value=profile.cps / 10)
    embed.add_field(name="Message Priority", value=profile.priority.capitalize())

    if interaction.channel.id in await interaction.client.database.get_channels(interaction.guild.id):
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
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
