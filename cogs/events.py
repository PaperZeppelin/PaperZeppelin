import datetime
import discord
from discord import activity
from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.errors import Forbidden
from discord.ext.commands.errors import (
    BadArgument,
    CommandNotFound,
    MemberNotFound,
    MissingPermissions,
)
import typing
from PaperZeppelin import Client

class Events(commands.Cog):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client

    @commands.Cog.listener()
    async def on_member_ban(
        self, guild: discord.Guild, user: typing.Union[discord.User, discord.Member]
    ):
        await self.client.db.execute(
            "INSERT INTO infractions (guild_id, user_id, type) VALUES ($1, $2, 'MANUAL BAN')",
            guild.id,
            user.id,
        )

    @commands.Cog.listener()
    async def on_member_unban(
        self, guild: discord.Guild, user: typing.Union[discord.User, discord.Member]
    ):
        await self.client.db.execute(
            "INSERT INTO infractions (guild_id, user_id, type) VALUES ($1, $2, 'MANUAL UNBAN')",
            guild.id,
            user.id,
        )


async def setup(client: Bot):
    await client.add_cog(Events(client=client))
