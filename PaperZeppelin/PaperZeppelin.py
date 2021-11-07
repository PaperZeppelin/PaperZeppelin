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

# postgres://{user}:{password}@{hostname}:{port}/{database-name}
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

with open(f"logs.json", "r") as f:
    logs = json.load(f)

client.logs = logs

client.guild_cache = dict()
client.user_messages = 0
client.self_messages = 0
client.bot_messages = 0


def get_logs(guild_id: str):
    with open(f"logs.json", "r") as f:
        logs = json.load(f)
    return logs[guild_id]


def update_logs(logs):
    with open(f"logs.json", "w") as f:
        json.dump(logs, f, indent=4)


update_logs(client.logs)


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
    for guild in client.guilds:
        prefix = await client.pg_con.fetchval(
            "SELECT prefix FROM guilds WHERE id = $1", guild.id
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
        client.guild_cache[guild.id] = {
            "prefix": prefix,
            "mod_roles": mod_roles,
            "infractions": infractions,
        }
    print(client.guild_cache)


@client.event
async def on_guild_join(guild):
    # Build cache
    client.guild_cache[guild.id] = {"prefix": "-", "mod_roles": [], "infractions": []}

    # Dump logs
    client.logs[str(guild.id)] = [
        f"{datetime.datetime.utcnow().replace(microsecond=0).isoformat()}{' ' * 4}{client.user.id} ({client.user.name}#{client.user.discriminator}) has joined the server"
    ]
    update_logs(client.logs)
    with open(f"logs.json", "w") as f:
        json.dump(client.logs, f, indent=4)

    # Handle database
    await client.pg_con.execute(
        "INSERT INTO guilds (id, prefix) VALUES ($1, '-')", guild.id
    )
    # Infractions + mod_roles do not need to be built on guild_join


for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        try:
            client.load_extension(f"cogs.{filename[:-3]}")
        except commands.ExtensionFailed:
            pass


async def create_db_pool():
    client.pg_con = await asyncpg.create_pool(
        database=os.getenv("PG_DATABASE"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASS"),
        host="127.0.0.1",
    )


client.loop.run_until_complete(create_db_pool())
client.run(os.getenv("TOKEN"))
