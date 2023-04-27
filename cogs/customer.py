from discord.ext import commands
from discord import app_commands
import discord

from bot import Bot
from cogs.utils import mongo


@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
class Customer(commands.GroupCog, group_name='customer'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.category_name = 'Customers'

    @app_commands.command()
    async def onboarding(
        self, interaction: discord.Interaction, name: str
    ) -> None:
        """Add a new customer to the database"""
        customer_info = {
            '_id': interaction.channel_id,
            'name': name
        }
        customer = mongo.Customer()
        await customer.create(customer_info)

        customer_category = discord.utils.get(
            interaction.guild.categories, name=self.category_name
        )
        await interaction.channel.move(category=customer_category, end=True)

        await interaction.channel.edit(name=name)

        content = (
            f'Customer \'{name}\' has been setted up '
            'successfully, welcome to Bitacora!'
        )
        await interaction.response.send_message(content)

    @app_commands.command()
    async def update(
        self, interaction: discord.Interaction, name: str
    ) -> None:
        """Update an existing customer"""
        customer = mongo.customer(interaction.channel_id)
        await customer.update({'name': name})

        await interaction.channel.edit(name=name)

        content = f'Customer \'{name}\' has been updated successfully.'
        await interaction.response.send_message(content)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Customer(bot))
