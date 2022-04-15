import datetime
from io import StringIO
from multiprocessing import parent_process
import discord
from discord import activity
from discord import message
from discord import permissions
from discord.embeds import Embed
from discord.ext import commands
import PaperZeppelin
from discord.errors import Forbidden
from discord.ext.commands.context import Context
from discord.ext.commands.core import command
from discord.ext.commands.errors import BadArgument, CommandNotFound
import json
import typing

from utils import message_utils


class Admin(commands.Cog):
    def __init__(self, client) -> None:
        super().__init__()
        self.client = client

    @commands.group(
        name="configure", aliases=["cfg", "config"], invoke_without_command=True
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def configure(self, ctx: commands.Context):
        """cfg_help"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help("configure")
            return

    @configure.command(name="prefix", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx: commands.Context, new: typing.Optional[str]):
        """cfg_prefix"""
        prefix = self.client.guild_cache[ctx.guild.id]["prefix"]
        if not new:
            await ctx.send(message_utils.build("cfg_prefix_current", prefix=prefix))
            return
        if len(new) > 25:
            await ctx.channel.send(message_utils.build("cfg_prefix_too_long"))
            return
        await self.client.db.execute("UPDATE guilds SET prefix = $1 WHERE id = $2", new, ctx.guild.id)
        self.client.guild_cache[ctx.guild.id] = {"prefix": new}
        await ctx.channel.send(message_utils.build("cfg_prefix_success", new=new))

    @configure.group(name="mod_roles", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def mod_roles(self, ctx: commands.Context):
        """cfg_mod_roles"""
        if ctx.invoked_subcommand is None:
            mod_roles_desc = ""
            for role_id in self.client.guild_cache[ctx.guild.id]["mod_roles"]:
                mod_roles_desc += f"<@&{role_id}>\n"
            await ctx.channel.send(embed=Embed(title=message_utils.build("cfg_mod_roles_current_title"), description=mod_roles_desc))
            return

    @mod_roles.command(name="add")
    @commands.has_permissions(administrator=True)
    async def mod_roles_add(self, ctx: commands.Context, role: discord.Role):
        """cfg_mod_roles_add"""
        id = role.id
        if id in self.client.guild_cache[ctx.guild.id]["mod_roles"]:
            await ctx.send(message_utils.build("cfg_mod_roles_add_already", role=role.name))
            return
        self.client.guild_cache[ctx.guild.id]["mod_roles"].append(id)
        await self.client.db.execute("INSERT INTO mod_roles (guild_id, role_id) VALUES ($1, $2)", ctx.guild.id, id)
        await ctx.channel.send(message_utils.build("cfg_mod_roles_add_success", role=role.name))
        return

    @mod_roles.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def mod_roles_remove(self, ctx: commands.Context, role: discord.Role):
        """cfg_mod_roles_remove"""
        id = role.id
        if not id in self.client.guild_cache[ctx.guild.id]["mod_roles"]:
            await ctx.send(message_utils.build("cfg_mod_roles_remove_already"))
            return
        self.client.guild_cache[ctx.guild.id]["mod_roles"].remove(id)
        await self.client.db.execute("DELETE FROM mod_roles WHERE role_id = $1", id)
        await ctx.channel.send(message_utils.build("cfg_mod_roles_remove_success"))
        return

    @commands.group(name="leave")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx: Context):
        """leave_help"""
        if ctx.invoked_subcommand is None:
            await ctx.channel.send(message_utils.build("leave_success", guild=ctx.guild.name))
            await ctx.guild.leave()
            return

    @leave.command(name="hard")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def hard(self, ctx: Context):
        """leave_hard_help"""
        await ctx.send(message_utils.build("leave_success", guild=ctx.guild.name))
        message = await ctx.send(message_utils.build("leave_hard_deleting"))
        await message.edit(content=message.content + message_utils.build("leave_hard_settings"))
        await self.client.db.execute("DELETE FROM guilds WHERE id = $1", ctx.guild.id)
        await self.client.db.execute("DELETE FROM mod_roles WHERE guild_id = $1", ctx.guild.id)
        await message.edit(content=message.content + message_utils.build("leave_hard_inf"))
        await self.client.db.execute("DELETE FROM infractions WHERE guild_id = $1", ctx.guild.id)
        await message.edit(content=message_utils.build("leave_hard_done"))
        await ctx.send(message_utils.build("leave_hard_leaving"))
        await ctx.guild.leave()


async def setup(client: PaperZeppelin.Client):
    await client.add_cog(Admin(client=client))
