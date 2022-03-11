from discord.ext import commands
import os
import asyncpg
import sys
import typing
import discord
import time

class Client(commands.Bot):
    def __init__(self, **options):
        try:
            import config
            self.config_file = True
            self.config = config
            print("Found config file")
        except ModuleNotFoundError:
            print("Config file not found")
            self.config_file = False
            if os.getenv("TOKEN") is None:
                print("Environment Variable's are not valid")
                sys.exit(-1)
        intents = discord.Intents(
            guild_messages=True, members=True, typing=False, guilds=True, bans=True, message_content=True
        )
        self.guild_cache = dict()
        super().__init__(
            command_prefix=self._get_prefix,
            intents=intents,
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="the chats go by"
            ),
        )
        self.db = self.loop.run_until_complete(self._create_db_pool())
        self.user_messages = 0
        self.self_messages = 0
        self.bot_messages = 0
        self.remove_command("help")

    async def _get_prefix(self, _c, message: discord.Message):
        return commands.when_mentioned_or(self.guild_cache[message.guild.id]['prefix'])(self, message)

    def _get_variable(self, key: str, *, fail_fast: bool = False, exit: bool = False) -> typing.Any:
        if self.config_file:
            try:
                attr = getattr(self.config, key)
                if attr:
                    return attr
            except AttributeError:
                pass
        env = os.getenv(key)
        if env:
            return env
        if fail_fast:
            self.logger.error(f'Could not find {key} as a variable, returning None')
        if exit:
            sys.exit(-1)
        return None

    async def _create_db_pool(self) -> asyncpg.Pool:
        if self._get_variable("DATABASE_URL") is None:
            return await asyncpg.create_pool(
                database=self._get_variable("PGDATABASE", fail_fast=True, exit=True),
                user=self._get_variable("PGUSER", fail_fast=True, exit=True),
                password=self._get_variable("PGPASSWORD", fail_fast=True, exit=True),
                host=self._get_variable("PGHOST", fail_fast=True, exit=True),
                port=self._get_variable("PGPORT"),
            )
        else:
            return await asyncpg.create_pool(dsn=self._get_variable("DATABASE_URL", fail_fast=True, exit=True))

    async def cache_guilds(self):
        now = time.perf_counter()
        for guild in self.guilds:
            print(
                "caching guild {guild_id} : {guild_name}".format(
                    guild_id=guild.id, guild_name=guild.name
                )
            )
            prefix = await self.db.fetchval(
                "SELECT prefix FROM guilds WHERE id = $1", guild.id
            )
            verification_level = await self.db.fetchval(
                "SELECT verification_level FROM guilds WHERE id = $1", guild.id
            )
            mod_roles = []
            for record in await self.db.fetch(
                "SELECT role_id FROM mod_roles WHERE guild_id = $1", guild.id
            ):
                mod_roles.append(record.get("role_id"))
                infractions = []
            for inf in await self.db.fetch(
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
            log_fetch = await self.db.fetchrow(
                "SELECT * FROM logging WHERE guild_id = $1", guild.id
            )
            loggers = {"command": log_fetch.get("command")}
            self.guild_cache[guild.id] = {
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
        print(self.guild_cache)

