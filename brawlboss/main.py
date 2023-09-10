#!/usr/bin/env python3
"""main.py
Description of main.py.
"""
import logging
import os
import socket

import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import database
import helper
import brawlstars
from logger import logger

club_tag = os.getenv('BRAWLSTARS_CLUB_TAG')
guild_id = os.getenv('DISCORD_GUILD_ID')

db = database.BrawlBossDatabase()
guild = discord.Object(id=guild_id)


async def club_to_database():
    """Returns club members as Player"""
    async with brawlstars.BrawlStarsApiAsync() as api:
        data = await api.get_club(club_tag)

    if data:
        club = await db.upsert_club(data)
        return club
    else:
        logger.warning(f'Could not get data from api')


async def player_of_the_week():
    """Get the player with the most wins in the last 7 days"""
    pass


async def player_exists(tag):
    """Returns club members as Player"""
    if not tag.startswith('#'):
        tag = f'#{tag}'
    async with brawlstars.BrawlStarsApiAsync() as api:
        data = await api.get_players(tag)

    return True if data else False


async def members_to_players(club):
    members = club.get('members')
    players = []
    if members:
        for i, member in enumerate(members):
            logger.info(f'Getting more data for {member["name"]} ({member["tag"]}) | {i + 1}/{len(members)}')
            player, new_player = await player_to_database(member['tag'])
            if player:
                players.append(player)
    return players


async def player_to_database(tag):
    async with brawlstars.BrawlStarsApiAsync() as api:
        data = await api.get_players(tag)
    if data:
        player, new_player = await db.upsert_player(data)
        return player, new_player
    else:
        logger.warning(f'Could not get player data from api')


async def battles_to_database(player):
    # Get battle logs from api
    async with brawlstars.BrawlStarsApiAsync() as api:
        data = await api.get_players_battle_log(player['tag'])

    # Add battles from log if returned any
    if data:
        for i, battle in enumerate(data['items']):
            await db.upsert_battle(battle)
    else:
        logger.warning(f'Could not get data from api')


async def update():
    try:
        # Get data from brawl stars and put in mongodb
        club, new_club = await club_to_database()
        members = club.get('members')

        # Iterate over members
        if members:
            for i, member in enumerate(members):
                logger.info(f'Getting more data for {member["name"]} ({member["tag"]}) | {i + 1}/{len(members)}')
                player, new_player = await player_to_database(member['tag'])
                if player:
                    logger.info(f'Getting logs for {player["name"]} ({player["tag"]}) | {i + 1}/{len(members)}')
                    await battles_to_database(player)

    except Exception as e:
        logger.error(e)


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self) -> None:
        # synced = await self.tree.sync()
        synced = await self.tree.sync(guild=guild)
        for s in synced:
            logger.debug(s)
        logger.info(f'Synced slash commands for {self.user}')


bot = Bot()


@tasks.loop(minutes=15)
async def update_database():
    logger.info(f'Updating database')
    await update()

    next_update_dt = datetime.now() + timedelta(minutes=30)
    logger.info(f'Next database update: {next_update_dt.strftime("%Y-%m-%d %H:%M:%S")}')


@bot.event
async def on_ready():
    print(f"I'm alive! {bot.user} (ID: {bot.user.id})")
    # Test api connection
    async with brawlstars.BrawlStarsApiAsync() as api:
        data = await api.get_events()
        if data:
            logger.info('API connection successful')
        else:
            logger.warning(f'API returned {data}')
    # Test database connection
    db_conn = await db.test_connection()
    if db_conn:
        logger.info('Database connection successful')
    else:
        logger.warning(f'Failed to connect to database')

    # Update database from api
    update_database.start()


@bot.hybrid_command(name='ping', description='Play some ping pong')
@app_commands.guilds(guild)
async def ping(ctx):
    """Says hello!"""
    await ctx.send(f'pong')


@bot.hybrid_command(name='profile',
                    description='Get Brawl Stars profile of you or another member',
                    with_app_command=True)
@app_commands.guilds(guild)
async def profile(ctx, member: discord.Member = None):
    if member:
        user = member.id
    else:
        user = ctx.author.id
    player = await db.player_from_discord_id(user)
    message = f'Sorry, no player found for <@{user}>'
    if player:
        wins, losses, total = await db.battle_count(player['tag'])
        star_player = await db.star_player_count(player['tag'])
        message = helper.player_to_profile_message(player, victories=wins, defeats=losses, starPlayer=star_player)

    await ctx.send(message)


@bot.hybrid_command(name='rankings',
                    description='Get the club rankings for the last seven days')
@app_commands.guilds(guild)
async def rankings(ctx):
    rankings_list = await db.club_rankings(club_tag)
    message = helper.rankings_message(rankings_list)
    await ctx.send(message)


@bot.hybrid_command(name='link',
                    description='Link your Discord profile with a Brawl Stars account',
                    with_app_command=True)
@app_commands.describe(tag='#PLAYERTAG')
@app_commands.guilds(guild)
async def link(ctx, tag: str):
    user_id = ctx.author.id
    message = f'No Brawl Stars account exists for `{tag}`'
    # Check if account exists
    if not tag.startswith('#'):
        tag = f'#{tag}'
    exists = await player_exists(tag)
    if exists:
        doc = await db.upsert_discord({'_id': user_id, 'tag': tag})
        if doc:
            message = f'Brawl Stars account `{tag}` was successfully linked to <@{user_id}>'
        else:
            message = f"Sorry, couldn't link `{tag}` to your Discord ID"
    await ctx.send(message)



@bot.hybrid_command(name='slap',
                    description='Slap someone who deserves it',
                    with_app_command=True)
@app_commands.describe(member='The person to slap')
@app_commands.guilds(guild)
async def slap(ctx, member: discord.Member):
    """Says when a member joined."""
    author = ctx.message.author
    sender = f"<@{author.id}>"
    receiver = f"<@{member.id}>"
    message = f'> {helper.random_slap(sender, receiver)}'
    await ctx.send(f'> {helper.random_slap(sender, receiver)}')


@bot.hybrid_command(name='engage',
                    description='Have some fun with another member',
                    with_app_command=True)
@app_commands.describe(member='The member to engage with')
@app_commands.guilds(guild)
async def engage(ctx, member: discord.Member):
    """Says when a member joined."""
    author = ctx.message.author
    sender = f"<@{author.id}>"
    receiver = f"<@{member.id}>"
    await ctx.send(f'> {helper.random_engage(sender, receiver)}')


if __name__ == '__main__':
    logger.info(f'Bot IP: {helper.public_ip()}')
    print(os.getenv('DISCORD_TOKEN'))
    bot.run(os.getenv('DISCORD_TOKEN'), log_handler=None)
