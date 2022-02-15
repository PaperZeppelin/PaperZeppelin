import datetime
from io import StringIO
import typing
import discord
from discord import activity
from discord import message
from discord import Member
from discord import member
from discord import permissions
from discord.abc import User
from discord.client import Client
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.errors import Forbidden
from discord.ext.commands.core import command, has_any_role, has_permissions
from discord.ext.commands.errors import CommandNotFound, MissingPermissions
import json
import functools


class Mod(commands.Cog):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client

    def staff_or_permission(self, ctx, member, permissions):
        getter = functools.partial(discord.utils.get, ctx.author.roles)
        staff = any(
            getter(id=item) is not None
            if isinstance(item, int)
            else getter(name=item) is not None
            for item in self.client.guild_cache[ctx.guild.id]["mod_roles"]
        )
        return staff or permissions

    def can_interact(self, issuer: Member, target: Member):
        # return issuer.roles[0].position > target.roles[0].position
        return (
            issuer.roles[len(issuer.roles) - 1].position
            > target.roles[len(target.roles) - 1].position
            or issuer.id == issuer.guild.owner.id
        )

    @commands.command(name="ban")
    @commands.guild_only()
    @commands.bot_has_guild_permissions(ban_members=True)
    async def ban_command(self, ctx: commands.Context, *inputs):
        """Ban a user from the server"""
        if not self.staff_or_permission(
            ctx, ctx.author, ctx.author.guild_permissions.ban_members
        ):
            await ctx.channel.send(f"🔒 You are not allowed to use this command")
            return
        if len(inputs) == 0:

            await ctx.channel.send(
                "Missing required arguement `member`\nCommand usage: `{}ban [member] <reason>`".format(
                    self.client.guild_cache[ctx.guild.id]["prefix"]
                )
            )
            return

        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            if len(ctx.message.mentions) > 0 and len(ctx.message.mentions) < 2:
                member = ctx.message.mentions[0]
            elif ctx.guild.get_member(int(inputs[0])) is not None:
                member = ctx.guild.get_member(int(inputs[0]))
        except ValueError:
            await ctx.channel.send(f"Could not parse the `member` arguement")
            return

        reason = None

        if len(inputs) > 1:
            reason = " ".join(inputs[1:])

        if member.id == ctx.author.id:
            await ctx.channel.send(f"You cannot ban yourself!")
            return

        if member.id == ctx.guild.owner_id:
            await ctx.channel.send("You cannot ban the owner of the server!")
            return

        if member.id == self.client.user.id:
            await ctx.channel.send(
                "I am unable to ban myself (I do not have a higher role than myself)\nIf you want me gone, you can manually kick/ban me or run `{}leave`".format(
                    self.client.guild_cache[ctx.guild.id]["prefix"]
                )
            )
            return

        # or ctx.author.id == ctx.guild.owner_id
        try:
            if (
                not self.staff_or_permission(
                    ctx, member, member.guild_permissions.ban_members
                )
                or ctx.author.id == ctx.guild.owner_id
            ):
                await ctx.guild.ban(user=member, reason=reason, delete_message_days=0)
                await self.client.pg_con.execute(
                    "INSERT INTO infractions (guild_id, user_id, mod_id, type, reason) VALUES ($1, $2, $3,'BAN', $4)",
                    ctx.guild.id,
                    member.id,
                    ctx.author.id,
                    reason,
                )
                self.client.guild_cache[ctx.guild.id]["infractions"].append(
                    {
                        "id": await self.client.pg_con.fetchval(
                            "SELECT last_value FROM infractions_id_seq"
                        ),
                        "time": datetime.datetime.now().replace(tzinfo=None),
                        "guild_id": ctx.guild.id,
                        "user_id": member.id,
                        "mod_id": ctx.author.id,
                        "type": "BAN",
                        "reason": reason,
                    }
                )
                await ctx.channel.send(
                    f"Banned `{member.name}#{member.discriminator}`{f' for reason: {reason}' if reason is not None else ''}"
                )
                return
            else:
                await ctx.channel.send(
                    f"You cannot ban {member.name}#{member.discriminator} as they are a moderator"
                )
                return
        except Forbidden:
            await ctx.channel.send(
                f"I cannot ban {member.name}#{member.discriminator} as they have a higher role then me"
            )
            return

    @commands.group(name="clean")
    @commands.guild_only()
    async def clean_base_command(self, ctx: commands.Context):
        if not self.staff_or_permission(
            ctx, ctx.author, ctx.author.guild_permissions.manage_messages
        ):
            raise MissingPermissions
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @clean_base_command.command(name="cleanban")
    @commands.guild_only()
    @commands.bot_has_guild_permissions(ban_members=True)
    async def ban_command_clean(self, ctx: commands.Context, *inputs):
        """Like the ban command but deletes messages (default is 1 day)"""
        if not self.staff_or_permission(
            ctx, ctx.author, ctx.author.guild_permissions.ban_members
        ):
            raise MissingPermissions
        if len(inputs) == 0:
            await ctx.channel.send(
                "Missing required arguement `member`\nCommand usage: `{}ban [member] <reason>`".format(
                    self.client.guild_cache[ctx.guild.id]["prefix"]
                )
            )
            return

        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            if len(ctx.message.mentions) > 0 and len(ctx.message.mentions) < 2:
                member = ctx.message.mentions[0]
            elif ctx.guild.get_member(int(inputs[0])) is not None:
                member = ctx.guild.get_member(int(inputs[0]))
        except ValueError:
            await ctx.channel.send(f"Could not parse the `member` arguement")
            return

        reason = None
        days = 1

        try:
            if inputs[1][-1] == "d" or inputs[1][-1] == "D":
                temp_days = int(inputs[1][0:-1])
                days = temp_days
            else:
                days = int(inputs[1])
        except ValueError:
            days = 1

        if len(inputs) > 2:
            reason = " ".join(inputs[2:])

        if member.id == ctx.author.id:
            await ctx.channel.send(f"You cannot ban yourself!")
            return

        if member.id == ctx.guild.owner_id:
            await ctx.channel.send("You cannot ban the owner of the server!")
            return

        if member.id == self.client.user.id:

            await ctx.channel.send(
                "I am unable to ban myself (I do not have a higher role than myself)\nIf you want me gone, you can manually kick/ban me or run `{}leave`".format(
                    self.client.guild_cache[ctx.guild.id]["prefix"]
                )
            )
            return

        # or ctx.author.id == ctx.guild.owner_id
        try:
            if (
                not self.staff_or_permission(
                    ctx, member, member.guild_permissions.ban_members
                )
                or ctx.author.id == ctx.guild.owner_id
            ):
                await ctx.guild.ban(
                    user=member, reason=reason, delete_message_days=days
                )
                await self.client.pg_con.execute(
                    "INSERT INTO infractions (guild_id, user_id, mod_id, type, reason) VALUES ($1, $2, $3,'CLEANBAN', $4)",
                    ctx.guild.id,
                    member.id,
                    ctx.author.id,
                    reason,
                )
                self.client.guild_cache[ctx.guild.id]["infractions"].append(
                    {
                        "id": await self.client.pg_con.fetchval(
                            "SELECT last_value FROM infractions_id_seq"
                        ),
                        "time": datetime.datetime.now().replace(tzinfo=None),
                        "guild_id": ctx.guild.id,
                        "user_id": member.id,
                        "mod_id": ctx.author.id,
                        "type": "CLEANBAN",
                        "reason": reason,
                    }
                )
                await ctx.channel.send(
                    f"Banned `{member.name}#{member.discriminator}`{f' for reason: {reason}' if reason is not None else ''} and deleted their message history for the past {days} days"
                )
                return
            else:
                await ctx.channel.send(
                    f"You cannot ban {member.name}#{member.discriminator} as they are a moderator"
                )
                return
        except Forbidden:
            await ctx.channel.send(
                f"I cannot ban {member.name}#{member.discriminator} as they have a higher role then me"
            )
            return

    @commands.command(name="kick")
    @commands.guild_only()
    @commands.bot_has_guild_permissions(kick_members=True)
    async def kick_command(self, ctx: commands.Context, *inputs):
        """Kick a user from the server"""
        if not self.staff_or_permission(
            ctx, ctx.author, ctx.author.guild_permissions.kick_members
        ):
            await ctx.channel.send(f"🔒 You are not allowed to use this command")
            return
        if len(inputs) == 0:
            await ctx.channel.send(
                "Missing required arguement `member`\nCommand usage: `{}kick [member] <reason>`".format(
                    self.client.guild_cache[ctx.guild.id]["prefix"]
                )
            )
            return

        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            if len(ctx.message.mentions) > 0 and len(ctx.message.mentions) < 2:
                member = ctx.message.mentions[0]
            elif ctx.guild.get_member(int(inputs[0])) is not None:
                member = ctx.guild.get_member(int(inputs[0]))
        except ValueError:
            await ctx.channel.send(f"Could not parse the `member` arguement")
            return

        reason = None

        if len(inputs) > 1:
            reason = " ".join(inputs[1:])

        if member.id == ctx.author.id:
            await ctx.channel.send(f"You cannot kick yourself!")
            return

        if member.id == ctx.guild.owner_id:
            await ctx.channel.send("You cannot kick the owner of the server!")
            return

        if member.id == self.client.user.id:
            await ctx.channel.send(
                "I am unable to kick myself (I do not have a higher role than myself)\nIf you want me gone, you can manually kick/ban me or run `{}leave`".format(
                    self.client.guild_cache[ctx.guild.id]["prefix"]
                )
            )
            return

        # or ctx.author.id == ctx.guild.owner_id
        try:
            if (
                not self.staff_or_permission(
                    ctx, member, member.guild_permissions.kick_members
                )
                or ctx.author.id == ctx.guild.owner_id
            ):
                await ctx.guild.kick(user=member, reason=reason)
                await self.client.pg_con.execute(
                    "INSERT INTO infractions (guild_id, user_id, mod_id, type, reason) VALUES ($1, $2, $3,'KICK', $4)",
                    ctx.guild.id,
                    member.id,
                    ctx.author.id,
                    reason,
                )
                self.client.guild_cache[ctx.guild.id]["infractions"].append(
                    {
                        "id": await self.client.pg_con.fetchval(
                            "SELECT last_value FROM infractions_id_seq"
                        ),
                        "time": datetime.datetime.now().replace(tzinfo=None),
                        "guild_id": ctx.guild.id,
                        "user_id": member.id,
                        "mod_id": ctx.author.id,
                        "type": "KICK",
                        "reason": reason,
                    }
                )
                await ctx.channel.send(
                    f"Kicked `{member.name}#{member.discriminator}`{f' for reason: {reason}' if reason is not None else ''}"
                )
                return
            else:
                await ctx.channel.send(
                    f"You cannot kick {member.name}#{member.discriminator} as they are a moderator"
                )
                return
        except Forbidden:
            await ctx.channel.send(
                f"I cannot kick {member.name}#{member.discriminator} as they have a higher role then me"
            )
            return

    @commands.group(name="infractions", aliases=["inf"])
    @commands.guild_only()
    async def infractions(self, ctx: commands.Context):
        """Manage infractions"""
        if (
            self.staff_or_permission(
                ctx, ctx.author, ctx.author.guild_permissions.view_audit_log
            )
            and ctx.invoked_subcommand is None
        ):
            infractions = self.client.guild_cache[ctx.guild.id]["infractions"]
            f = StringIO()
            f.write(
                f"\nID  |User               |Moderator          |Time                              |TYPE      |Reason \n{'-' * 96}\n"
            )
            for infraction in infractions[
                0 : (len(infractions) if len(infractions) < 100 else 100)
            ]:
                f.write(
                    f"{infraction['id']}{' '* (4- len(str(infraction['id'])))}|{infraction['user_id']}{' '* (19- len(str(infraction['user_id'])))}|{infraction['mod_id']}{' '* (19- len(str(infraction['mod_id'])))}|{infraction['time'].isoformat()}+00:00{' '* (34- len(str(infraction['time'].isoformat()+'+00:00')))}|{infraction['type']}{' '* (10- len(str(infraction['type'])))}|{infraction['reason'] if infraction['reason'] is not None else ''}\n"
                )
            f.write(
                f"\n\n\nGenerated by {self.client.user.name} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            f.seek(0)
            expand = (
                "\n*Make sure to click expand!*" if f.getvalue().count("\n") > 5 else ""
            )
            await ctx.send(
                content=f"🔍 Here are the infractions I've found{expand}",
                file=discord.File(f, "infractions.md"),
            )
            return
        else:
            if ctx.invoked_subcommand is None:
                raise MissingPermissions(missing_permissions=["VIEW_AUDIT_LOG"])

    @infractions.command(name="dump")
    @commands.guild_only()
    async def dump(self, ctx: commands.Context):
        """Dump all infractions into a file"""
        if self.staff_or_permission(
            ctx, ctx.author, ctx.author.guild_permissions.view_audit_log
        ):
            infractions = self.client.guild_cache[ctx.guild.id]["infractions"]
            f = StringIO()
            f.write(str(infractions))
            f.write(
                f"\n\n\nGenerated by {self.client.user.name} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            f.seek(0)
            await ctx.send(
                content="Dumping all the infractions",
                file=discord.File(f, "infractions.json"),
            )
            return
        else:
            raise MissingPermissions(missing_permissions=["VIEW_AUDIT_LOG"])

    @infractions.command(name="search")
    @commands.guild_only()
    async def dump(
        self, ctx: commands.Context, user: typing.Union[discord.User, discord.Member]
    ):
        """Get all infractions from a user"""
        if (
            self.staff_or_permission(
                ctx, ctx.author, ctx.author.guild_permissions.view_audit_log
            )
            and ctx.invoked_subcommand is None
        ):
            infractions = self.client.guild_cache[ctx.guild.id]["infractions"]
            f = StringIO()
            f.write(
                f"\nID  |User               |Moderator          |Time                              |TYPE      |Reason \n{'-' * 96}\n"
            )
            for infraction in infractions[
                0 : (len(infractions) if len(infractions) < 100 else 100)
            ]:
                if infraction["user_id"] == user.id or infraction["mod_id"] == user.id:
                    f.write(
                        f"{infraction['id']}{' '* (4- len(str(infraction['id'])))}|{infraction['user_id']}{' '* (19- len(str(infraction['user_id'])))}|{infraction['mod_id']}{' '* (19- len(str(infraction['mod_id'])))}|{infraction['time'].isoformat()}+00:00{' '* (34- len(str(infraction['time'].isoformat()+'+00:00')))}|{infraction['type']}{' '* (10- len(str(infraction['type'])))}|{infraction['reason'] if infraction['reason'] is not None else ''}\n"
                    )
            f.write(
                f"\n\n\nGenerated by {self.client.user.name} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            f.seek(0)
            expand = (
                "\n*Make sure to click expand!*" if f.getvalue().count("\n") > 5 else ""
            )
            await ctx.send(
                content=f"🔍 Here are the infractions I've found{expand}",
                file=discord.File(f, "infractions.md"),
            )
            return
        else:
            if ctx.invoked_subcommand is None:
                raise MissingPermissions(missing_permissions=["VIEW_AUDIT_LOG"])

    @commands.command(name="mkick")
    @commands.guild_only()
    async def mkick(
        self,
        ctx: commands.Context,
        members: commands.Greedy[typing.Union[discord.Member, discord.User]],
        *,
        reason,
    ):
        """Kick multiple user from the server"""
        await ctx.send(members)
        print(self.can_interact(ctx.author, members[0]))
        # if (not self.staff_or_permission(ctx, ctx.author, ctx.author.guild_permissions.kick_members)):
        #     await ctx.channel.send(f"🔒 You are not allowed to use this command")
        #     return
        # if(len(members) == 0):
        #     await ctx.channel.send(f"Missing required arguement `member`\nCommand usage: `{self.client.guild_cache[ctx.guild.id]["prefix"]}kick [member] <reason>`")
        #     return

        # time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def setup(client: Bot):
    client.add_cog(Mod(client=client))
