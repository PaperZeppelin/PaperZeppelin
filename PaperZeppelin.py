from discord.ext import commands, tasks
import os
import asyncpg
import sys
import typing
import discord
import time
import traceback
from utils import message_utils

all_extentions = (
    'cogs.admin',
    'cogs.basic',
    'cogs.core',
    'cogs.discord',
    'cogs.events',
    'cogs.mod',
    'cogs.owner'
)

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
        self.user_messages = 0
        self.self_messages = 0
        self.bot_messages = 0
        self.remove_command("help")
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        message_utils.load()

    async def setup_hook(self) -> None:
        self.db = await self._create_db_pool()
        for extension in all_extentions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                print(f'Failed to load extension {extension}.')
                traceback.print_exc()

    async def _get_prefix(self, _c, message: discord.Message):
        return commands.when_mentioned_or(self.guild_cache[message.guild.id]['prefix'])(self, message)

    def get_command_signature(self, cmd: str, prefix: str = "-") -> str:
        command = self.get_command(cmd)
        if command is None:
            return "(command signature)"

        parent: Optional[Group[Any, ..., Any]] = command.parent  # type: ignore - the parent will be a Group
        entries = []
        while parent is not None:
            if not parent.signature or parent.invoke_without_command:
                entries.append(parent.name)
            else:
                entries.append(parent.name + ' ' + parent.signature)
            parent = parent.parent  # type: ignore
        parent_sig = ' '.join(reversed(entries))

        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            fmt = f'[{command.name}|{aliases}]'
            if parent_sig:
                fmt = parent_sig + ' ' + fmt
            alias = fmt
        else:
            alias = command.name if not parent_sig else parent_sig + ' ' + command.name
        return f"{prefix}{alias} {command.signature}"
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
            guild_data = await self.db.fetchrow("SELECT * FROM guilds WHERE id = $1", guild.id)
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
                "prefix": guild_data.get("prefix"),
                "mod_roles": mod_roles,
                "infractions": infractions,
                "verification_level": guild_data.get("verification_level"),
                "loggers": loggers,
                "mute_role": guild.get_role(guild_data.get("mute_role")),
            }
            print(
                "cached guild {guild_id} :: {guild_name}".format(
                    guild_id=guild.id, guild_name=guild.name
                )
            )
        print("cached in {time}".format(time=time.perf_counter() - now))
        print(self.guild_cache)

