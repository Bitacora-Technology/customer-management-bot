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
        self.already_customer = 'Customer has already been onboarded'
        self.not_customer = 'Customer has not been onboarded yet'
        self.category_name = 'Customers'

    async def customer_exists(self, channel_id: int) -> bool:
        customer = mongo.Customer(channel_id)
        customer_info = await customer.check()
        return bool(customer_info)

    @app_commands.command()
    @app_commands.describe(
        name='Customer name', stripe='Subscription identifier'
    )
    async def onboarding(
        self, interaction: discord.Interaction, name: str, stripe: str
    ) -> None:
        """Add a new customer to the database"""
        result = await self.customer_exists(interaction.channel_id)

        if result is True:
            await interaction.response.send_message(
                self.already_customer, ephemeral=True
            )
            return

        customer_info = {
            '_id': interaction.channel_id,
            'name': name,
            'stripe': stripe
        }
        customer = mongo.Customer()
        await customer.create(customer_info)

        customer_category = discord.utils.get(
            interaction.guild.categories, name=self.category_name
        )
        await interaction.channel.move(category=customer_category, end=True)
        await interaction.channel.edit(name=name)

        content = f'Customer \'{name}\' has been setted up successfully'
        await interaction.response.send_message(content, ephemeral=True)

    @app_commands.command()
    @app_commands.describe(
        name='Customer name', stripe='Subscription identifier'
    )
    async def update(
        self,
        interaction: discord.Interaction,
        name: str = None,
        stripe: str = None
    ) -> None:
        """Update an existing customer"""
        result = await self.customer_exists(interaction.channel_id)

        if result is False:
            await interaction.response.send_message(
                self.not_customer, ephemeral=True
            )
            return

        customer_info = {}

        if name:
            customer_info['name'] = name
            await interaction.channel.edit(name=name)
        if stripe:
            customer_info['stripe'] = stripe

        if customer_info == {}:
            content = 'Nothing has been specified'
        else:
            customer = mongo.Customer(interaction.channel_id)
            await customer.update(customer_info)

            updated_customer_info = await customer.check()
            name = updated_customer_info.get('name')

            content = f'Customer \'{name}\' has been updated successfully.'

        await interaction.response.send_message(content, ephemeral=True)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Customer(bot))
