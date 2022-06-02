import typing

from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands.context import Context

import discord
from PaperZeppelin import Client


class Admin(commands.Cog):
    def __init__(self, client: Client) -> None:
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
        """Changes the prefix

        By default the prefix is '-'. The bot will always register commands that use an @ as a prefix."""
        prefix = self.client.guild_cache[ctx.guild.id]["prefix"]
        if not new:
            await ctx.send("The current server prefix is `{}`".format(prefix))
            return
        if len(new) > 25:
            await ctx.channel.send("Please use a shorter prefix")
            return
        await self.client.db.execute(
            "UPDATE guilds SET prefix = $1 WHERE id = $2", new, ctx.guild.id
        )
        self.client.guild_cache[ctx.guild.id] = {"prefix": new}
        await ctx.channel.send("Succesfully set the prefix to `{}`".format(new))

    @configure.group(name="mod_roles", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def mod_roles(self, ctx: commands.Context):
        """Manage mod roles

        Mod roles are used by the bot to calculate an users permissions when they run a command in the Mod category.
        If a user does not meet the criteria of having the appropraite permission for the command OR having a mod role, the command fails.

        This command is a ROOT command. Use either `configure mod_roles add` or `remove` to modify the mod roles list.
        Run this command without `add` or `remove` to view the current mod roles"""
        if ctx.invoked_subcommand is None:
            mod_roles_desc = ""
            for role_id in self.client.guild_cache[ctx.guild.id]["mod_roles"]:
                mod_roles_desc += f"<@&{role_id}>\n"
            await ctx.channel.send(
                embed=Embed(
                    title="Current mod roles",
                    description=mod_roles_desc,
                )
            )
            return

    @mod_roles.command(name="add")
    @commands.has_permissions(administrator=True)
    async def mod_roles_add(self, ctx: commands.Context, role: discord.Role):
        """Add a mod role"""
        id = role.id
        if id in self.client.guild_cache[ctx.guild.id]["mod_roles"]:
            await ctx.send("`{}` is already a mod role".format(role.name))
            return
        self.client.guild_cache[ctx.guild.id]["mod_roles"].append(id)
        await self.client.db.execute(
            "INSERT INTO mod_roles (guild_id, role_id) VALUES ($1, $2)",
            ctx.guild.id,
            id,
        )
        await ctx.channel.send("Added `{}` as a mod role!".format(role.name))
        return

    @mod_roles.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def mod_roles_remove(self, ctx: commands.Context, role: discord.Role):
        """Remove a mod role"""
        id = role.id
        if not id in self.client.guild_cache[ctx.guild.id]["mod_roles"]:
            await ctx.send("{} is not a mod role".format(role.name))
            return
        self.client.guild_cache[ctx.guild.id]["mod_roles"].remove(id)
        await self.client.db.execute("DELETE FROM mod_roles WHERE role_id = $1", id)
        await ctx.channel.send("Removed the mod role {}".format(role.name))
        return

    @configure.command(name="mute_role")
    @commands.has_permissions(administrator=True)
    async def mute_role(
        self, ctx: commands.Context, role: typing.Optional[discord.Role]
    ):
        """Configure the mute role

        Unlike other bots, PaperZepelin does not automatically change channel overrides
        to support the new mute role. This choice is intentional, giving you more control
        over how your server operates.

        The command requires an optional `role` arguement. Run the command without the arguement to view the current mute role configured"""
        if role is None:
            c: typing.Union[discord.Role, None] = self.client.guild_cache[ctx.guild.id][
                "mute_role"
            ]
            if c is None:
                await ctx.send(
                    "No mute role has been set up in the server. Considering using `{}` to set up one".format(
                        self.client.get_command_signature("cfg mute_role")
                    )
                )
            else:
                await ctx.send(
                    "The current mute role is {}".format(c.mention),
                    allowed_mentions=discord.AllowedMentions(roles=False),
                )
        else:
            if ctx.guild.me.top_role.position <= role.position:
                t = [
                    "The desired mute role, `{}` could not be added to the servers configuration".format(
                        role.name
                    ),
                    "Reason: Target role above bot role",
                ]
                return await ctx.send("\n".join(t))
            if role.is_integration():
                t = [
                    "The desired mute role, `{}` could not be added to the servers configuration".format(
                        role.name
                    ),
                    "Reason: Target role is owned by another intergration",
                ]
                return await ctx.send("\n".join(t))
            c: typing.Union[discord.Role, None] = self.client.guild_cache[ctx.guild.id][
                "mute_role"
            ]
            await self.client.db.execute(
                "UPDATE guilds SET mute_role=$1 WHERE id = $2", role.id, ctx.guild.id
            )
            self.client.guild_cache[ctx.guild.id]["mute_role"] = role
            await ctx.send(
                "`{}` has been set as the server's mute role".format(role.name)
            )

    @commands.group(name="leave")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx: Context):
        """Force the bot to leave the server"""
        if ctx.invoked_subcommand is None:
            await ctx.channel.send("Goodbye.")
            await ctx.guild.leave()
            return

    @leave.command(name="hard")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def hard(self, ctx: Context):
        """This command forces the bot to leave the server AND deletes data stored

        Use cases
        ---------
        NOTE: These are all recommended, you can use this command whenever you wish.

        * You didn't mean to add the bot and/or you do not intend to add the bot back ever.
        * The server configuration is totally broken or you want to reset it, you intend to add the bot back once command execution is complete.

        Peristant data
        --------------
        These types of data are still stored by the bot

        * Global blacklists, if a user in the guild or the server is blacklisted
        * Global tags, non guild or user only tags are still kept by the bot. Create a guild-only tag if you want them to be deleted.
        """
        message = await ctx.send("Deleting data.")
        await self.client.db.execute("DELETE FROM guilds WHERE id = $1", ctx.guild.id)
        await self.client.db.execute(
            "DELETE FROM mod_roles WHERE guild_id = $1", ctx.guild.id
        )
        await self.client.db.execute(
            "DELETE FROM infractions WHERE guild_id = $1", ctx.guild.id
        )
        await message.edit("Data deleted.")
        await ctx.send("Goodbye.")
        await ctx.guild.leave()


async def setup(client: Client):
    await client.add_cog(Admin(client=client))
