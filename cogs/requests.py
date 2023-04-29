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
    embed = discord.Embed(title='Requests board')
    priority_list = ['🔴', '🟡', '🟢']

    count = 1
    for request in requests:
        name = request.get('name')
        priority = request.get('priority')
        value = f'Priority: {priority_list[priority]}'
        embed.add_field(name=f'{count}. {name}', value=value, inline=False)
        count = 1

    return embed


class AddPriorityView(discord.ui.View):
    def __init__(self, info: dict) -> None:
        super().__init__(timeout=600)
        self.request_info = info
        self.added_request = 'The request \'{}\' has been added to the board'

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
        await self.interaction.response.edit_message(
            content=self.added_request.format(name),
            embed=None,
            view=None,
            delete_after=180
        )

    @discord.ui.button(label='High', emoji='🔴')
    async def high_priority(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        self.interaction = interaction
        self.priority = 0
        await self.add_request()

    @discord.ui.button(label='Medium', emoji='🟡')
    async def medium_priority(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        self.interaction = interaction
        self.priority = 1
        await self.add_request()

    @discord.ui.button(label='Low', emoji='🟢')
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


class UpdateInfoModal(discord.ui.Modal):
    def __init__(self, info: dict) -> None:
        super().__init__(title='Update request', timeout=None)
        self.request_info = info
        self.request_updated = 'The request \'{}\' has been updated'

        name = info.get('name')
        self.name = discord.ui.TextInput(label='Name', default=name)
        self.add_item(self.name)

        description = info.get('description')
        self.description = discord.ui.TextInput(
            label='Description',
            default=description,
            style=discord.TextStyle.long
        )
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        request_info = {
            'name': self.name.value,
            'description': self.description.value,
            'priority': self.request_info['priority']
        }

        customer = mongo.Customer(interaction.channel_id)
        customer_info = await customer.check()

        requests = customer_info.get('requests', [])
        try:
            requests.remove(self.request_info)
        except Exception:
            pass

        requests.append(request_info)
        await customer.update({'requests': requests})
        await interaction.response.edit_message(
            content=self.request_updated.format(self.name.value),
            embed=None,
            view=None,
            delete_after=180
        )


class UpdateRequestView(discord.ui.View):
    def __init__(self, info: dict) -> None:
        super().__init__(timeout=600)
        self.request_info = info

    async def on_timeout(self) -> None:
        await self.message.delete()

    @discord.ui.button(label='Information', style=discord.ButtonStyle.primary)
    async def information(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        modal = UpdateInfoModal(self.request_info)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Priority', style=discord.ButtonStyle.primary)
    async def priority(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        pass


class DeleteRequestView(discord.ui.View):
    def __init__(self, info: dict) -> None:
        super().__init__(timeout=600)
        self.request_info = info
        self.deleted_true = 'The request \'{}\' has been deleted'
        self.deleted_false = 'The request could not be deleted, try again'

    async def on_timeout(self) -> None:
        await self.message.delete()

    @discord.ui.button(
        label='Yes, I want to delete it',
        style=discord.ButtonStyle.danger
    )
    async def delete(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        customer = mongo.Customer(interaction.channel_id)
        customer_info = await customer.check()

        requests = customer_info.get('requests', [])
        try:
            requests.remove(self.request_info)
        except Exception:
            await interaction.response.edit_message(
                content=self.deleted_false,
                embed=None,
                view=None,
                delete_after=180
            )
            return

        name = self.request_info.get('name')
        await customer.update({'requests': requests})
        await interaction.response.edit_message(
            content=self.deleted_true.format(name),
            embed=None,
            view=None,
            delete_after=180
        )


class SelectRequestButton(discord.ui.Button):
    def __init__(self, index: int, action: str) -> None:
        self.action = action
        if self.action == 'update':
            style = discord.ButtonStyle.primary
        else:
            style = discord.ButtonStyle.danger
        super().__init__(label=index, style=style)
        self.not_found = 'The request was not found on the board'

    async def find_request(self, message: discord.Message) -> Optional[dict]:
        field = message.embeds[0].fields[self.label-1]
        name = ' '.join(field.name.split(' ')[1:])

        customer = mongo.Customer(message.channel.id)
        customer_info = await customer.check()

        requests = customer_info.get('requests', [])
        for request in requests:
            if request.get('name') == name:
                return request

    async def callback(self, interaction: discord.Interaction) -> None:
        request_info = await self.find_request(interaction.message)

        if request_info is None:
            await interaction.response.send_message(self.not_found)
            return

        embed = simple_request_embed(request_info)
        if self.action == 'update':
            embed.set_footer(
                text='Choose what you want to update'
            )
            view = UpdateRequestView(request_info)
        else:
            embed.set_footer(
                text='Once you have confirmed it cannot be restored'
            )
            view = DeleteRequestView(request_info)
        view.message = await interaction.response.edit_message(
            embed=embed, view=view
        )


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
        self.no_requests = 'You do not have any request on the board'

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

    async def send_board(
        self, interaction: discord.Interaction, action: str
    ) -> None:
        customer_info = await self.customer_exists(interaction.channel_id)

        if bool(customer_info) is False:
            await interaction.response.send_message(self.not_customer)
            return

        requests = customer_info.get('requests', [])
        if len(requests) == 0:
            await interaction.response.send_message(self.no_requests)
            return

        await interaction.response.send_message('\u200b', delete_after=0)

        sublists = []
        sorted_requests = sorted(requests, key=lambda r: r.get('priority'))
        for i in range(0, len(requests), 25):
            sublist = sorted_requests[i:i+25]
            sublists.append(sublist)

        for request_list in sublists:
            embed = view_requests_embed(request_list)
            view = SelectRequestView(request_list, action)
            view.message = await interaction.channel.send(
                embed=embed, view=view
            )

    @app_commands.command()
    async def update(self, interaction: discord.Interaction) -> None:
        """Update an existing request from the board"""
        await self.send_board(interaction, 'update')

    @app_commands.command()
    async def delete(self, interaction: discord.Interaction) -> None:
        """Delete an existing request from the board"""
        await self.send_board(interaction, 'delete')


async def setup(bot: Bot) -> None:
    await bot.add_cog(Requests(bot))
