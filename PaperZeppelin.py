import json
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
    if message.guild.id in client.guild_cache:
        return commands.when_mentioned_or(
            client.guild_cache[message.guild.id]["prefix"]
        )(client, message)


intents = discord.Intents(
    guild_messages=True, members=True, typing=False, guilds=True, bans=True
)
client = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
)
client.remove_command("help")

client.guild_cache = dict()
client.user_messages = 0
client.self_messages = 0
client.bot_messages = 0


@client.event
async def on_ready():
    client.before_activity = "`3` the chats go by"
    client.status = discord.Status.idle
    await client.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(
            type=discord.ActivityType.watching, name="the chats go by"
        ),
    )
    client.start_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    now = time.perf_counter()
    for guild in client.guilds:
        print(
            "caching guild {guild_id} : {guild_name}".format(
                guild_id=guild.id, guild_name=guild.name
            )
        )
        prefix = await client.pg_con.fetchval(
            "SELECT prefix FROM guilds WHERE id = $1", guild.id
        )
        verification_level = await client.pg_con.fetchval(
            "SELECT verification_level FROM guilds WHERE id = $1", guild.id
        )
        mod_roles = []
        for record in await client.pg_con.fetch(
            "SELECT role_id FROM mod_roles WHERE guild_id = $1", guild.id
        ):
            mod_roles.append(record.get("role_id"))
        infractions = []
        for inf in await client.pg_con.fetch(
            "SELECT * FROM infractions WHERE guild_id = $1", guild.id
        ):
            if id is not None:
                infractions.append(
                    {
                        "id": inf.get("id"),
                        "time": inf.get("time"),
                        "guild_id": inf.get("guild_id"),
                        "user_id": inf.get("user_id"),
                        "mod_id": inf.get("mod_id"),
                        "type": inf.get("type"),
                        "reason": inf.get("reason"),
                    }
                )
        log_fetch = await client.pg_con.fetchrow(
            "SELECT * FROM logging WHERE guild_id = $1", guild.id
        )
        loggers = {"command": log_fetch.get("command")}
        client.guild_cache[guild.id] = {
            "prefix": prefix,
            "mod_roles": mod_roles,
            "infractions": infractions,
            "verification_level": verification_level,
            "loggers": loggers,
        }
        print(
            "cached guild {guild_id} : {guild_name}".format(
                guild_id=guild.id, guild_name=guild.name
            )
        )
    print("cached in {time}".format(time=time.perf_counter() - now))
    print(client.guild_cache)


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
    await client.pg_con.execute(
        "INSERT INTO guilds (id, prefix) VALUES ($1, '-')", guild.id
    )
    await client.pg_con.execute("INSERT INTO logging (guild_id) VALUES ($1)", guild.id)
    # Infractions + mod_roles do not need to be built on guild_join


for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
            client.load_extension(f"cogs.{filename[:-3]}")


async def create_db_pool():
    if os.getenv("DATABASE_URL") is None:
        client.pg_con = await asyncpg.create_pool(
            database=os.getenv("PGDATABASE"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            host=os.getenv("PGHOST"),
            port=os.getenv("PGPORT"),
        )
    else:
        client.pg_con = await asyncpg.create_pool(dsn=os.getenv("DATABASE_URL"))


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
                await client.pg_con.execute(
                    "UPDATE logging SET command = NULL WHERE guild_id = $1",
                    ctx.guild.id,
                )
    return True


print("PaperZeppelin is starting")
client.loop.run_until_complete(create_db_pool())
client.run(os.getenv("TOKEN"))
