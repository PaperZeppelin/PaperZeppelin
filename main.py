import PaperZeppelin
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import datetime, time
import traceback


load_dotenv()

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


print("PaperZeppelin is starting")
client.run(client._get_variable("TOKEN", exit=True))
