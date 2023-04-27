from discord.ext import commands
from discord import app_commands
import discord

from bot import Bot
from cogs.utils import mongo


class Client(commands.GroupCog, group_name='client'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot


async def setup(bot: Bot) -> None:
    await bot.add_cog(Client(bot))
