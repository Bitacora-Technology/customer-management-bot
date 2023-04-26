from discord.ext import commands
from discord import app_commands
import discord

from bot import Bot


class Onboarding(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot


async def setup(bot: Bot) -> None:
    await bot.add_cog(Onboarding(bot))
