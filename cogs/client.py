from discord.ext import commands
from discord import app_commands
import discord

from bot import Bot
from cogs.utils import mongo


@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
class Client(commands.GroupCog, group_name='client'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.category_name = 'Clients'

    @app_commands.command()
    async def onboarding(
        self, interaction: discord.Interaction, client: str
    ) -> None:
        """Add a new client to the database"""
        client_info = {
            '_id': interaction.channel_id,
            'name': client
        }
        _client = mongo.Client()
        await _client.create(client_info)

        client_category = discord.utils.get(
            interaction.guild.categories, name=self.category_name
        )
        await interaction.channel.move(category=client_category, end=True)

        content = (
            f'Client \'{client}\' has been setted up '
            'successfully, welcome to Bitacora!'
        )
        await interaction.response.send_message(content)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Client(bot))
