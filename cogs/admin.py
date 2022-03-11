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
from utils import MessageUtils
import typing



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
        """Configure bot settings"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help("configure")
            return

    @configure.command(name="prefix", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx: commands.Context, new: typing.Optional[str]):
        """Change the prefix"""
        prefix = self.client.guild_cache[ctx.guild.id]["prefix"]
        if not new:
            await ctx.send(f"The current server prefix is `{prefix}`")
            return
        if len(new) > 25:
            await ctx.channel.send(f"Please use a shorter prefix")
            return
        await self.client.db.execute("UPDATE guilds SET prefix = $1 WHERE id = $2", new, ctx.guild.id)
        self.client.guild_cache[ctx.guild.id] = {"prefix": new}
        await ctx.channel.send(f"Succesfully set the prefix to `{new}`")

    @configure.group(name="mod_roles", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def mod_roles(self, ctx: commands.Context):
        """Manage mod roles"""
        if ctx.invoked_subcommand is None:
            mod_roles_desc = ""
            for role_id in self.client.guild_cache[ctx.guild.id]["mod_roles"]:
                mod_roles_desc += f"<@&{role_id}>\n"
            await ctx.channel.send(embed=Embed(title="Current mod roles", description=mod_roles_desc))
            return

    @mod_roles.command(name="add")
    @commands.has_permissions(administrator=True)
    async def mod_roles_add(self, ctx: commands.Context, role: discord.Role):
        """Add a mod role"""
        id = role.id
        if id in self.client.guild_cache[ctx.guild.id]["mod_roles"]:
            await ctx.send(f"❗ {role.name} is already a mod role!")
            return
        self.client.guild_cache[ctx.guild.id]["mod_roles"].append(id)
        await self.client.db.execute("INSERT INTO mod_roles (guild_id, role_id) VALUES ($1, $2)", ctx.guild.id, id)
        await ctx.channel.send(f":white_check_mark: `{role.name}` is now a mod role.")
        return

    @mod_roles.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def mod_roles_remove(self, ctx: commands.Context, role: discord.Role):
        """Remove a mod role"""
        id = role.id
        if not id in self.client.guild_cache[ctx.guild.id]["mod_roles"]:
            await ctx.send(f"❗ {role.name} is not a mod role!")
            return
        self.client.guild_cache[ctx.guild.id]["mod_roles"].remove(id)
        await self.client.db.execute("DELETE FROM mod_roles WHERE role_id = $1", id)
        await ctx.channel.send(f":white_check_mark: Removed `{role.name}` from mod roles.")
        return

    @commands.group(name="leave")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx: Context):
        """Force the bot to leave the server"""
        if ctx.invoked_subcommand is None:
            await ctx.channel.send(f"It's been an honour serving {ctx.guild.name}, but alas, my time as come")
            await ctx.guild.leave()
            return

    @leave.command(name="hard")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def hard(self, ctx: Context):
        """Force the bot to leave the server AND delete all data"""
        await ctx.send(f"It's been an honour serving {ctx.guild.name}, but alas, my time as come")
        message = await ctx.send("Deleting stored data...")
        await message.edit(content=message.content + "\n```\nDeleting settings\n```")
        await self.client.db.execute("DELETE FROM guilds WHERE id = $1", ctx.guild.id)
        await self.client.db.execute("DELETE FROM mod_roles WHERE guild_id = $1", ctx.guild.id)
        await message.edit(content=message.content + "\n```\nDeleting infractions\n```")
        await self.client.db.execute("DELETE FROM infractions WHERE guild_id = $1", ctx.guild.id)
        await message.edit(content="Deleted all data")
        await ctx.send("Leaving guild...")
        await ctx.guild.leave()


def setup(client: PaperZeppelin.Client):
    client.add_cog(Admin(client=client))
