import os
import discord
from discord import app_commands
from discord.ext import tasks
import logging
import asyncio
import schedule

from dotenv import load_dotenv

from nft import valid_address

import database

from log_config import setup_logging

logger = setup_logging('bot', 'imagenationbot.log', logging.DEBUG)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', default=0))
MY_GUILD = discord.Object(id=GUILD_ID)

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
intents.members = True
intents.messages = True
client = MyClient(intents=intents)

group = app_commands.Group(name="wallet", description="description")


@group.command(description='Add a wallet to your list of wallets', name='add')
@app_commands.rename(address_or_handle='address')
@app_commands.describe(address_or_handle='Your Cardano wallet address or handle')
async def add_wallet(interaction: discord.Interaction, address_or_handle: str):
    address, stake = valid_address(address_or_handle)
    if not address:
        await interaction.response.send_message(f'Please provide a valid address or ADA handle', ephemeral=True)
        return
    database.add_address(interaction.user.id, address, stake)
    await interaction.response.send_message(f'Your wallet {address_or_handle} will be registered soon.', ephemeral=True)


@group.command(description='Remove a wallet from your list of wallets', name='remove')
@app_commands.rename(address_or_handle='address')
@app_commands.describe(address_or_handle='Your Cardano wallet address or handle')
async def remove_wallet(interaction: discord.Interaction, address_or_handle: str):
    address, stake = valid_address(address_or_handle)
    if address:
        database.remove_address(interaction.user.id, address, stake)
    await interaction.response.send_message(f'Your wallet {address_or_handle} will be removed soon.', ephemeral=True)


@group.command(description='List your linked wallets', name='list')
async def list_wallets(interaction: discord.Interaction):
    addresses = database.get_addresses(interaction.user.id)
    if not addresses:
        await interaction.response.send_message('You have no wallets registered')
        return
    else:
        addies = "\n".join(addresses)
    await interaction.response.send_message(f'You have registered following addresses:\n{addies}', ephemeral=True)


client.tree.add_command(group)


@client.tree.command()
async def show_members(interaction: discord.Interaction):
    logger.debug(client.get_guild(GUILD_ID).members)

    for m in client.get_guild(GUILD_ID).members:
        logger.debug(m.name, m.id)
    await interaction.response.send_message('members', ephemeral=True)


# This context menu command only works on members
@client.tree.context_menu(name='Show Join Date')
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human-readable representation in the official client
    await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(member.joined_at)}',
                                            ephemeral=True)


@client.tree.context_menu(name='Show Register Date')
async def show_register_date(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f'{member} registered at {discord.utils.format_dt(member.created_at)}',
                                            ephemeral=True)


async def update_roles():
    logger.info('updating roles...')
    # guild = client.get_guild(GUILD_ID)
    member_roles = database.get_all_roles()
    logger.debug('member_roles: {}'.format(member_roles))

    for guild in client.guilds:
        logger.info(f'updating roles for guild {guild.id}')
        managed_roles = database.get_managed_roles(guild.id)
        logger.debug('managed roles: {}'.format(managed_roles))
        for member in guild.members:
            if member.id in member_roles:
                roles = member_roles[member.id]
                for role_id in roles:
                    if role_id not in managed_roles:
                        continue
                    role = guild.get_role(role_id)
                    if role not in member.roles:
                        await member.add_roles(role)
                for role in member.roles:
                    if role.id not in roles and role.id in managed_roles:
                        logger.debug('removing', role.name, 'from', member.name)
                        await member.remove_roles(role)
            else:
                for role in member.roles:
                    if role.id in managed_roles:
                        logger.debug('removing', role.name, 'from', member.name)
                        await member.remove_roles(role)


def run_async(coro, *args):
    loop = asyncio.get_running_loop()
    loop.create_task(coro(*args))


schedule.every(15).minutes.do(run_async, update_roles)


@tasks.loop(seconds=1.0)
async def loop():
    schedule.run_pending()


@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user} (ID: {client.user.id})')
    logger.info('------')
    try:
        loop.start()
    except RuntimeError:
        # loop already started
        pass


client.run(TOKEN)
