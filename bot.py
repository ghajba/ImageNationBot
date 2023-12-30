from typing import Optional
import os
import discord
from discord import app_commands

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

MY_GUILD = discord.Object(id=os.getenv('DISCORD_GUILD_ID'))  # replace with your guild id

address_map = {}


# see more examples at https://github.com/Rapptz/discord.py/tree/master/examples

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


group = app_commands.Group(name="wallet", description="description")


@group.command(description='Add a wallet to your list of wallets', name='add')
@app_commands.rename(address_or_handle='address')
@app_commands.describe(address_or_handle='Your Cardano wallet address or handle')
async def add_wallet(interaction: discord.Interaction, address_or_handle: str):
    if interaction.user.id not in address_map:
        address_map[interaction.user.id] = []
    address_map[interaction.user.id].append(address_or_handle)
    await interaction.response.send_message(f'Your wallet {address_or_handle} will be registered soon.', ephemeral=True)


@group.command(description='List your linked wallets', name='list')
async def list_wallets(interaction: discord.Interaction):
    addresses = '\t' + '\n\t'.join(address_map[interaction.user.id])
    await interaction.response.send_message(f'You have registered following addresses:\n{addresses}', ephemeral=True)


client.tree.add_command(group)


# This context menu command only works on members
@client.tree.context_menu(name='Show Join Date')
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(member.joined_at)}',
                                            ephemeral=True)


@client.tree.context_menu(name='Show Register Date')
async def show_register_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} registered at {discord.utils.format_dt(member.created_at)}',
                                            ephemeral=True)


client.run(TOKEN)
