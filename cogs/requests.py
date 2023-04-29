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


def view_requests_embed(requests: list) -> discord.Embed:
    embed = discord.Embed(title='Feature requests')
    priority_list = ['🔴', '🟡', '🟢']

    count = 1
    for request in requests:
        name = request.get('name')
        priority = request.get('priority')
        value = f'Priority: {priority_list[priority]}'
        embed.add_field(name=f'{count}. {name}', value=value, inline=False)
        count += 1

    return embed


class AddPriorityView(discord.ui.View):
    def __init__(self, info: dict) -> None:
        super().__init__(timeout=300)
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
        label='High', emoji='🔴', style=discord.ButtonStyle.secondary
    )
    async def high_priority(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        self.interaction = interaction
        self.priority = 0
        await self.add_request()

    @discord.ui.button(
        label='Medium', emoji='🟡', style=discord.ButtonStyle.secondary
    )
    async def medium_priority(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        self.interaction = interaction
        self.priority = 1
        await self.add_request()

    @discord.ui.button(
        label='Low', emoji='🟢', style=discord.ButtonStyle.secondary
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


class SelectRequestButton(discord.ui.Button):
    def __init__(self, index: int, action: str) -> None:
        self.action = action

        if self.action == 'update':
            style = discord.ButtonStyle.primary
        else:
            style = discord.ButtonStyle.danger

        super().__init__(label=index, style=style)


class SelectRequestView(discord.ui.View):
    def __init__(self, requests: list, action: str) -> None:
        super().__init__(timeout=600)
        for i in range(len(requests)):
            self.add_item(SelectRequestButton(i+1, action))

    async def on_timeout(self) -> None:
        await self.message.delete()


class Requests(commands.GroupCog, group_name='requests'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.not_customer = 'Customer has not been onboarded yet'
        self.no_requests = 'You don\'t have any request on the board'

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

        requests = customer_info.get('requests', [])
        if len(requests) == 0:
            await interaction.response.send_message(self.no_requests)
            return

        sublists = []
        sorted_requests = sorted(requests, key=lambda r: r.get('priority'))
        for i in range(0, len(requests), 25):
            sublist = sorted_requests[i:i+25]
            sublists.append(sublist)

        for request_list in sublists:
            embed = view_requests_embed(request_list)
            view = SelectRequestView(request_list, 'update')
            view.message = await interaction.channel.send(
                embed=embed, view=view
            )

    @app_commands.command()
    async def delete(self, interaction: discord.Interaction) -> None:
        """Delete an existing request from the board"""
        customer_info = await self.customer_exists(interaction.channel_id)

        if bool(customer_info) is False:
            await interaction.response.send_message(self.not_customer)
            return

        requests = customer_info.get('requests', [])
        if len(requests) == 0:
            await interaction.response.send_message(self.no_requests)
            return

        sublists = []
        sorted_requests = sorted(requests, key=lambda r: r.get('priority'))
        for i in range(0, len(requests), 25):
            sublist = sorted_requests[i:i+25]
            sublists.append(sublist)

        for request_list in sublists:
            embed = view_requests_embed(request_list)
            view = SelectRequestView(request_list, 'delete')
            view.message = await interaction.channel.send(
                embed=embed, view=view
            )


async def setup(bot: Bot) -> None:
    await bot.add_cog(Requests(bot))
