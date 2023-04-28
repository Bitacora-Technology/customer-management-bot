from discord.ext import commands
from discord import app_commands
from typing import Optional
import discord

from bot import Bot
from cogs.utils import mongo


def simple_request_embed(info: dict) -> discord.Embed:
    embed = discord.Embed(
        title=info['name'], description=info['description'], color=12718096
    )
    return embed


class AddPriorityView(discord.ui.View):
    def __init__(self, info: dict) -> None:
        super().__init__(timeout=600)
        self.request_info = info
        self.board_command = '</requests board:1101120797424234587>'

    async def on_timeout(self) -> None:
        await self.message.delete()

    async def add_request(self) -> None:
        self.request_info['priority'] = self.priority

        customer = mongo.Customer(self.interaction.channel_id)
        customer_info = await customer.check()

        requests = customer_info.get('requests', [])
        requests.append(self.request_info)
        await customer.update({'requests': requests})

        name = self.request_info.get('name')
        content = (
            f'The request \'{name}\' has been added to the board, '
            f'you can check it using the command {self.board_command}'
        )
        await self.interaction.response.edit_message(
            content=content, embed=None, view=None
        )

    @discord.ui.button(
        label='High priority', style=discord.ButtonStyle.primary
    )
    async def high_priority(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        self.interaction = interaction
        self.priority = 0
        await self.add_request()

    @discord.ui.button(
        label='Medium priority', style=discord.ButtonStyle.primary
    )
    async def medium_priority(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        self.interaction = interaction
        self.priority = 1
        await self.add_request()

    @discord.ui.button(
        label='Low priority', style=discord.ButtonStyle.primary
    )
    async def low_priority(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        self.interaction = interaction
        self.priority = 2
        await self.add_request()


class AddRequestModal(discord.ui.Modal):
    def __init__(self) -> None:
        super().__init__(title='Add request')

    name = discord.ui.TextInput(label='Name')

    description = discord.ui.TextInput(
        label='Description', style=discord.TextStyle.long
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        request_info = {
            'name': self.name.value,
            'description': self.description.value
        }

        embed = simple_request_embed(request_info)
        embed.set_footer(
            text='Select the priority to add the request to the board'
        )

        view = AddPriorityView(request_info)
        view.message = await interaction.channel.send(
            embed=embed, view=view
        )

        await interaction.response.defer()


class SelectRequestView(discord.ui.View):
    def __init__(self, action: str) -> None:
        super().__init__(timeout=600)


class Requests(commands.GroupCog, group_name='requests'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.not_customer = 'Customer has not been onboarded yet'

    async def customer_exists(self, channel_id: int) -> Optional[dict]:
        customer = mongo.Customer(channel_id)
        customer_info = await customer.check()
        return customer_info

    @app_commands.command()
    async def board(self, interaction: discord.Interaction) -> None:
        """Check the status of your requests board"""
        customer_info = await self.customer_exists(interaction.channel_id)

        if bool(customer_info) is False:
            await interaction.response.send_message(self.not_customer)
            return

    @app_commands.command()
    async def add(self, interaction: discord.Interaction) -> None:
        """Add a new request to the board"""
        customer_info = await self.customer_exists(interaction.channel_id)

        if bool(customer_info) is False:
            await interaction.response.send_message(self.not_customer)
            return

        modal = AddRequestModal()
        await interaction.response.send_modal(modal)

    @app_commands.command()
    async def update(self, interaction: discord.Interaction) -> None:
        """Update an existing request from the board"""
        customer_info = await self.customer_exists(interaction.channel_id)

        if bool(customer_info) is False:
            await interaction.response.send_message(self.not_customer)
            return

    @app_commands.command()
    async def remove(self, interaction: discord.Interaction) -> None:
        """Remove an existing request from the board"""
        customer_info = await self.customer_exists(interaction.channel_id)

        if bool(customer_info) is False:
            await interaction.response.send_message(self.not_customer)
            return


async def setup(bot: Bot) -> None:
    await bot.add_cog(Requests(bot))
