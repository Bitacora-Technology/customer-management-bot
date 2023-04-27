from discord.ext import commands
from discord import app_commands
import discord

from bot import Bot
from cogs.utils import mongo


class Requests(commands.GroupCog, group_name='requests'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def customer_exists(self, channel_id: int) -> bool:
        customer = mongo.Customer(channel_id)
        customer_info = await customer.check()
        return bool(customer_info)

    @app_commands.command()
    async def board(self, interaction: discord.Interaction) -> None:
        """Check the status of your requests board"""
        result = await self.customer_exists(interaction.channel_id)

        if result is False:
            content = 'Customer was not found in the database'
            await interaction.response.send_message(content)
            return

    @app_commands.command()
    async def add(self, interaction: discord.Interaction) -> None:
        """Add a new request to the board"""
        result = await self.customer_exists(interaction.channel_id)

        if result is False:
            content = 'Customer was not found in the database'
            await interaction.response.send_message(content)
            return

    @app_commands.command()
    async def update(self, interaction: discord.Interaction) -> None:
        """Update an existing request from the board"""
        result = await self.customer_exists(interaction.channel_id)

        if result is False:
            content = 'Customer was not found in the database'
            await interaction.response.send_message(content)
            return

    @app_commands.command()
    async def remove(self, interaction: discord.Interaction) -> None:
        """Remove an existing request from the board"""
        result = await self.customer_exists(interaction.channel_id)

        if result is False:
            content = 'Customer was not found in the database'
            await interaction.response.send_message(content)
            return


async def setup(bot: Bot) -> None:
    await bot.add_cog(Requests(bot))
