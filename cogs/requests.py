from discord.ext import commands
from discord import app_commands
import discord

from bot import Bot


class Requests(commands.GroupCog, group_name='requests'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @app_commands.command()
    async def board(self, interaction: discord.Interaction) -> None:
        """Check the status of your requests board"""

    @app_commands.command()
    async def add(self, interaction: discord.Interaction) -> None:
        """Add a new request to the board"""

    @app_commands.command()
    async def update(self, interaction: discord.Interaction) -> None:
        """Update an existing request from the board"""

    @app_commands.command()
    async def remove(self, interaction: discord.Interaction) -> None:
        """Remove an existing request from the board"""


async def setup(bot: Bot) -> None:
    await bot.add_cog(Requests(bot))
