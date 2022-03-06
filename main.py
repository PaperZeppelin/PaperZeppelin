import json
import PaperZeppelin
import os
import discord
from discord import activity
from discord.enums import Status
from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.ext.commands.context import Context
from discord.integrations import _integration_factory
from discord.interactions import Interaction
from discord.message import Message
from dotenv import load_dotenv
import datetime, time
import asyncpg
import aiohttp
from enums.Permissions import Permissions
from utils import BitUtils
from utils import MessageUtils


load_dotenv()


async def get_prefix(client, message):
    return commands.when_mentioned_or(client.guild_cache[message.guild.id]['prefix'])(client, message)



client = PaperZeppelin.Client()

@client.event
async def on_ready():
    client.start_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    await client.cache_guilds()


@client.event
async def on_guild_join(guild):
    # Build cache
    client.guild_cache[guild.id] = {
        "prefix": "-",
        "mod_roles": [],
        "infractions": [],
        "verification_level": 0,
        "logging": {"command": None},
    }

    # Handle database
    await client.db.execute(
        "INSERT INTO guilds (id, prefix) VALUES ($1, '-')", guild.id
    )
    await client.db.execute("INSERT INTO logging (guild_id) VALUES ($1)", guild.id)
    # Infractions + mod_roles do not need to be built on guild_join


for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")



@client.check_once
async def log_command(ctx: commands.Context):
    if ctx.guild:
        if client.guild_cache[ctx.guild.id]["loggers"]["command"]:
            try:
                channel = client.get_channel(
                    client.guild_cache[ctx.guild.id]["loggers"]["command"]
                )
                if not channel:
                    channel = await client.fetch_channel(
                        client.guild_cache[ctx.guild.id]["loggers"]["command"]
                    )
                await channel.send(
                    embeds=[
                        discord.Embed(
                            colour=0x2F3136,
                            title="Command executed!",
                            timestamp=datetime.datetime.utcfromtimestamp(
                                time.time()
                            ).replace(tzinfo=datetime.timezone.utc),
                        )
                        .set_thumbnail(url=ctx.author.avatar.url)
                        .add_field(
                            name="User",
                            value="`{u}#{d}`, {id}".format(
                                u=ctx.author.name,
                                d=ctx.author.discriminator,
                                id=ctx.author.id,
                            ),
                            inline=True,
                        )
                        .add_field(
                            name="Command ran",
                            value="`{c}`".format(c=ctx.message.clean_content),
                            inline=True,
                        )
                    ]
                )
            except:
                client.guild_cache[ctx.guild.id]["loggers"]["command"] = None
                await client.db.execute(
                    "UPDATE logging SET command = NULL WHERE guild_id = $1",
                    ctx.guild.id,
                )
    return True


print("PaperZeppelin is starting")
client.run(os.getenv("TOKEN"))
