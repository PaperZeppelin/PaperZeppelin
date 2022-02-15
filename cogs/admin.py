import datetime
from io import StringIO
import discord
from discord import activity
from discord import message
from discord import permissions
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.errors import Forbidden
from discord.ext.commands.context import Context
from discord.ext.commands.core import command
from discord.ext.commands.errors import BadArgument, CommandNotFound
import json
from utils import MessageUtils

configure_help = f"""
```diff
! [configure|config|cfg]

  prefix{' ' * 6}Change the guild prefix
  mod_roles{' ' * 3}Set mod roles for the server
```
"""


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
        member_permissions = ctx.message.author.guild_permissions
        if ctx.invoked_subcommand is None and member_permissions.administrator:
            await ctx.channel.send(configure_help)
            return

    @configure.command(name="prefix", invoke_without_command=True)
    async def prefix(self, ctx: commands.Context, *inputs):
        """Change the prefix"""
        prefix = self.client.guild_cache[ctx.guild.id]["prefix"]
        if len(inputs) == 0:
            await ctx.send(f"The current server prefix is `{prefix}`")
            return
        if len(inputs) == 1:
            member_permissions = ctx.message.author.guild_permissions
            if member_permissions.administrator:
                if len(inputs[0]) > 25:
                    await ctx.channel.send(f"Please use a shorter prefix")
                    return
                if isinstance(inputs[0], str):
                    await self.client.pg_con.execute(
                        "UPDATE guilds SET prefix = $1 WHERE id = $2",
                        inputs[0],
                        ctx.guild.id,
                    )
                    self.client.guild_cache[ctx.guild.id] = {"prefix": inputs[0]}
                    await ctx.channel.send(
                        f"Succesfully set the prefix to `{inputs[0]}`"
                    )
                    return
                else:
                    await ctx.channel.send(f"I couldn't parse {inputs[0]}")
                    return

    @configure.group(name="mod_roles", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def mod_roles(self, ctx: commands.Context):
        """Manage mod roles"""
        member_permissions = ctx.message.author.guild_permissions
        if ctx.invoked_subcommand is None and member_permissions.administrator:
            mod_roles_desc = ""
            for role_id in self.client.guild_cache[ctx.guild.id]["mod_roles"]:
                mod_roles_desc += f"<@&{role_id}>\n"
            await ctx.channel.send(
                embed=Embed(title="Current mod roles", description=mod_roles_desc)
            )
            return

    @mod_roles.command(name="add")
    @commands.has_permissions(administrator=True)
    async def mod_roles_add(self, ctx: commands.Context, inputs):
        """Add a mod role"""
        if len(ctx.message.role_mentions) > 0:
            if (
                int(ctx.message.role_mentions[0].id)
                in self.client.guild_cache[ctx.guild.id]["mod_roles"]
            ):
                await ctx.channel.send(
                    f"❌ `{ctx.message.role_mentions[0].name}` is already a mod role!"
                )
                return
            self.client.guild_cache[ctx.guild.id]["mod_roles"].append(
                int(ctx.message.role_mentions[0].id)
            )
            await self.client.pg_con.execute(
                "INSERT INTO mod_roles (guild_id, role_id) VALUES ($1, $2)",
                ctx.guild.id,
                ctx.message.role_mentions[0].id,
            )
            await ctx.channel.send(
                f":white_check_mark:  `{str(ctx.message.role_mentions[0].name)}` is now a mod role."
            )
            return
        elif ctx.guild.get_role(int(inputs)) is not None:
            if (
                int(ctx.guild.get_role(int(inputs)).id)
                in self.client.guild_cache[ctx.guild.id]["mod_roles"]
            ):
                await ctx.channel.send(
                    f"❌ `{ctx.guild.get_role(int(inputs)).name}` is already a mod role!"
                )
                return
            self.client.guild_cache[ctx.guild.id]["mod_roles"].append(int(inputs))
            await self.client.pg_con.execute(
                "INSERT INTO mod_roles (guild_id, role_id) VALUES ($1, $2)",
                ctx.guild.id,
                int(inputs),
            )
            await ctx.channel.send(
                f":white_check_mark:  `{ctx.guild.get_role(int(inputs)).name}` is now a mod role."
            )
            return

        await ctx.channel.send(f"🔒 You do not have access to this command")
        return

    @mod_roles.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def mod_roles_remove(self, ctx: commands.Context, inputs):
        """Remove a mod role"""
        if len(ctx.message.role_mentions) > 0:
            if (
                int(ctx.message.role_mentions[0].id)
                in self.client.guild_cache[ctx.guild.id]["mod_roles"]
            ):
                self.client.guild_cache[ctx.guild.id]["mod_roles"].remove(
                    int(ctx.message.role_mentions[0].id)
                )
                await self.client.pg_con.execute(
                    "DELETE FROM mod_roles WHERE role_id = $1",
                    ctx.message.role_mentions[0].id,
                )
                await ctx.channel.send(
                    f":white_check_mark:  `{str(ctx.message.role_mentions[0].name)}` is no longer a mod role."
                )
                return
            await ctx.channel.send(
                f"❌ `{ctx.message.role_mentions[0].name}` was not a mod role so I cannot remove it"
            )
            return
        elif ctx.guild.get_role(int(inputs)) is not None:
            if (
                int(ctx.guild.get_role(int(inputs)).id)
                in self.client.guild_cache[ctx.guild.id]["mod_roles"]
            ):
                self.client.guild_cache[ctx.guild.id]["mod_roles"].remove(int(inputs))
                await self.client.pg_con.execute(
                    "DELETE FROM mod_roles WHERE role_id = $1", int(inputs)
                )
                await ctx.channel.send(
                    f":white_check_mark: `{ctx.guild.get_role(int(inputs)).name}` is no longer a mod role."
                )
                return

            await ctx.channel.send(
                f"❌ `{ctx.guild.get_role(int(inputs)).name}` was not a mod role so I cannot remove it"
            )
            return

        await ctx.channel.send(f"🔒 You do not have access to this command")
        return

    @commands.group(name="leave")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx: Context):
        """Force the bot to leave the server"""
        if ctx.invoked_subcommand is None:
            member_permissions = ctx.message.author.guild_permissions
            if member_permissions.administrator:
                await ctx.channel.send(
                    f"It's been an honour serving {ctx.guild.name}, but alas, my time as come"
                )
                await ctx.guild.leave()
            else:
                await ctx.channel.send(f"Only server admins can use this command!")

    @leave.command(name="hard")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def hard(self, ctx: Context):
        """Force the bot to leave the server AND delete all data"""
        member_permissions = ctx.message.author.guild_permissions
        if member_permissions.administrator:
            await ctx.send(
                f"It's been an honour serving {ctx.guild.name}, but alas, my time as come"
            )
            message = await ctx.send("Deleting data stored...")
            await message.edit(
                content=message.content + "\n```\nDeleting settings\n```"
            )
            await self.client.pg_con.execute(
                "DELETE FROM guilds WHERE id = $1", ctx.guild.id
            )
            await self.client.pg_con.execute(
                "DELETE FROM mod_roles WHERE guild_id = $1", ctx.guild.id
            )
            await message.edit(
                content=message.content + "\n```\nDeleting infractions\n```"
            )
            await self.client.pg_con.execute(
                "DELETE FROM infractions WHERE guild_id = $1", ctx.guild.id
            )
            await message.edit(content="Deleted all data")
            await ctx.send("Leaving guild...")
            await ctx.guild.leave()
        else:
            await ctx.channel.send(f"Only server admins can use this command!")

    @configure.group(name="verification")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def verification(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                content=MessageUtils.build(
                    type="verification_level",
                    level=self.client.guild_cache[ctx.guild.id]["verification_level"],
                    prefix=ctx.prefix,
                )
            )

    @verification.command(name="set")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def set_verification_level(self, ctx: commands.Context, level: int):
        if level < 0 or level > 1:
            raise BadArgument("Could not parse the `level` arguement")
        self.client.guild_cache[ctx.guild.id]["verification_level"] = level
        await ctx.send(
            "Set the servers verification level to {level}".format(level=level)
        )
        await self.client.pg_con.execute(
            "UPDATE guilds SET verification_level = $1 WHERE id = $2",
            level,
            ctx.guild.id,
        )


def setup(client: Bot):
    client.add_cog(Admin(client=client))
