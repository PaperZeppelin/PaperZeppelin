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
from PaperZeppelin import Client
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.errors import Forbidden
from discord.ext.commands.core import command, has_any_role, has_permissions
from discord.ext.commands.errors import CommandNotFound, MissingPermissions
import json
import functools
from cogs.core import MissingArgument

from utils import message_utils

class BanFlags(commands.FlagConverter, prefix='--', delimiter=' '):
    days: typing.Optional[int] = 0

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

    @commands.command(name="test")
    async def test_c(self, ctx: commands.Context, flags: BanFlags, p: typing.Optional[int]):
        await ctx.send(flags)

    @commands.command(name="ban")
    @commands.guild_only()
    @commands.bot_has_guild_permissions(ban_members=True)
    async def ban_command(self, ctx: commands.Context, members: commands.Greedy[typing.Union[discord.Member, discord.User]], reason: typing.Optional[str],*, flags: BanFlags):
        """ban_help"""
        if not self.staff_or_permission(ctx, ctx.author, ctx.author.guild_permissions.ban_members):
            await ctx.channel.send(message_utils.build('no_staff_or_perm'))
            return
        if len(members) == 0:
            raise MissingArgument("members")
        failed = list()
        passed = list()
        total = len(members)
        for member in members:
            if member.id == ctx.author.id:
                failed.append(member)
                continue
            if member.id == ctx.guild.owner_id:
                failed.append(member)
                continue
            if member.id == self.client.user.id:
                failed.append(member)
                continue
            try:
                if isinstance(member, discord.Member):
                    if (self.staff_or_permission(ctx, member, member.guild_permissions.ban_members) or  not (ctx.author.id == ctx.guild.owner_id)):
                        failed.append(member)
                        continue
                await ctx.guild.ban(user=member, reason=reason, delete_message_days=flags.deletedays)
                await self.client.db.execute(
                    "INSERT INTO infractions (guild_id, user_id, mod_id, type, reason) VALUES ($1, $2, $3,'BAN', $4)",
                    ctx.guild.id,
                    member.id,
                    ctx.author.id,
                    reason,
                )
                self.client.guild_cache[ctx.guild.id]["infractions"].append(
                    {
                        "id": await self.client.db.fetchval(
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
                passed.append(member)
            except Forbidden:
                failed.append(member)
                continue
            except discord.HTTPException:
                failed.append(member)
        if len(passed) == total:
            if total == 1:
                await ctx.send(message_utils.build('ban_passed_single', user=members[0], reason=reason))
            elif total > 1:
                await ctx.send(message_utils.build('ban_passed_all', number=total, reason=reason))
        else:
            if len(failed) == total:
                if total == 1:
                    await ctx.send(message_utils.build('ban_failed_single', user=members[0]))
                elif total > 1:
                    await ctx.send(message_utils.build('ban_failed_all'))
            else:
                f = StringIO()
                for user in failed:
                    f.write(f'{user} - {user.id}\n') 
                f.seek(0)
                await ctx.send(message_utils.build('ban_failed_multiple', number=len(passed), reason=reason), files=[discord.File(f)])

    @commands.command(name="kick")
    @commands.guild_only()
    @commands.bot_has_guild_permissions(kick_members=True)
    async def kick_command(self, ctx: commands.Context, members: commands.Greedy[typing.Union[discord.Member, discord.User]], reason: typing.Optional[str]):
        """kick_help"""
        if not self.staff_or_permission(ctx, ctx.author, ctx.author.guild_permissions.kick_members):
            await ctx.channel.send(message_utils.build('no_staff_or_perm'))
            return
        if len(members) == 0:
            raise MissingArgument("members")
        failed = list()
        passed = list()
        total = len(members)
        for member in members:
            if member.id == ctx.author.id:
                failed.append(member)
                continue
            if member.id == ctx.guild.owner_id:
                failed.append(member)
                continue
            if member.id == self.client.user.id:
                failed.append(member)
                continue
            try:
                if isinstance(member, discord.Member):
                    if (self.staff_or_permission(ctx, member, member.guild_permissions.ban_members) or  not (ctx.author.id == ctx.guild.owner_id)):
                        failed.append(member)
                        continue
                await ctx.guild.kick(user=member, reason=reason)
                await self.client.db.execute(
                    "INSERT INTO infractions (guild_id, user_id, mod_id, type, reason) VALUES ($1, $2, $3,'KICk', $4)",
                    ctx.guild.id,
                    member.id,
                    ctx.author.id,
                    reason,
                )
                self.client.guild_cache[ctx.guild.id]["infractions"].append(
                    {
                        "id": await self.client.db.fetchval(
                            "SELECT last_value FROM infractions_id_seq"
                        ),
                        "time": datetime.datetime.now().replace(tzinfo=None),
                        "guild_id": ctx.guild.id,
                        "user_id": member.id,
                        "mod_id": ctx.author.id,
                        "type": "KICk",
                        "reason": reason,
                    }
                )
                passed.append(member)
            except Forbidden:
                failed.append(member)
                continue
            except discord.HTTPException:
                failed.append(member)
        if len(passed) == total:
            if total == 1:
                await ctx.send(message_utils.build('kick_passed_single', user=members[0], reason=reason))
            elif total > 1:
                await ctx.send(message_utils.build('kick_passed_all', number=total, reason=reason))
        else:
            if len(failed) == total:
                if total == 1:
                    await ctx.send(message_utils.build('kick_failed_single', user=members[0]))
                elif total > 1:
                    await ctx.send(message_utils.build('kick_failed_all'))
            else:
                f = StringIO()
                for user in failed:
                    f.write(f'{user} - {user.id}\n') 
                f.seek(0)
                await ctx.send(message_utils.build('kick_failed_multiple', number=len(passed), reason=reason), files=[discord.File(f)])

    @commands.group(name="infractions", aliases=["inf"])
    @commands.guild_only()
    async def infractions(self, ctx: commands.Context):
        """inf_help"""
        if not self.staff_or_permission(ctx, ctx.author, ctx.author.guild_permissions.view_audit_log):
            await ctx.channel.send(message_utils.build('no_staff_or_perm'))
            return

        if ctx.invoked_subcommand is not None:
            return
        infractions = self.client.guild_cache[ctx.guild.id]["infractions"]
        f = StringIO()
        f.write(f"\nID  |User               |Moderator          |Time                              |TYPE      |Reason \n{'-' * 96}\n")
        for infraction in infractions[0 : (len(infractions) if len(infractions) < 100 else 100)]:
            f.write(f"{infraction['id']}{' '* (4- len(str(infraction['id'])))}|{infraction['user_id']}{' '* (19- len(str(infraction['user_id'])))}|{infraction['mod_id']}{' '* (19- len(str(infraction['mod_id'])))}|{infraction['time'].isoformat()}+00:00{' '* (34- len(str(infraction['time'].isoformat()+'+00:00')))}|{infraction['type']}{' '* (10- len(str(infraction['type'])))}|{infraction['reason'] if infraction['reason'] is not None else ''}\n")
        f.write(message_utils.build("inf_generated_by", user=self.client.user.name, time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        f.seek(0)
        expand = message_utils.build("inf_expand") if f.getvalue().count("\n") > 5 else ""
        await ctx.send(content=message_utils.build("inf_message", expand=expand), file=discord.File(f, "infractions.md"))
        return


    @infractions.command(name="dump")
    @commands.guild_only()
    async def dump(self, ctx: commands.Context):
        """inf_dump"""
        if not self.staff_or_permission(ctx, ctx.author, ctx.author.guild_permissions.view_audit_log):
            await ctx.channel.send(message_utils.build('no_staff_or_perm'))
            return
        infractions = self.client.guild_cache[ctx.guild.id]["infractions"]
        f = StringIO()
        to_dump = {
            "public": infractions
        }
        f.write(json.dumps(to_dump, sort_keys=True, indent=4, default=str))
        f.seek(0)
        await ctx.send(content=message_utils.build("inf_dumping") + "\n*" + message_utils.build("inf_generated_by", user=self.client.user.name, time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')).replace("\n", "") + "*", file=discord.File(f, "infractions.json"))
        return
        
    @infractions.command(name="search")
    @commands.guild_only()
    async def searchdump(self, ctx: commands.Context, user: typing.Union[discord.User, discord.Member]):
        """inf_search_dump"""
        if not self.staff_or_permission(ctx, ctx.author, ctx.author.guild_permissions.view_audit_log):
            await ctx.channel.send(message_utils.build('no_staff_or_perm'))
            return

        infractions = self.client.guild_cache[ctx.guild.id]["infractions"]
        f = StringIO()
        f.write(f"\nID  |User               |Moderator          |Time                              |TYPE      |Reason \n{'-' * 96}\n")
        for infraction in infractions:
            if infraction["user_id"] == user.id or infraction["mod_id"] == user.id:
                f.write(f"{infraction['id']}{' '* (4- len(str(infraction['id'])))}|{infraction['user_id']}{' '* (19- len(str(infraction['user_id'])))}|{infraction['mod_id']}{' '* (19- len(str(infraction['mod_id'])))}|{infraction['time'].isoformat()}+00:00{' '* (34- len(str(infraction['time'].isoformat()+'+00:00')))}|{infraction['type']}{' '* (10- len(str(infraction['type'])))}|{infraction['reason'] if infraction['reason'] is not None else ''}\n")
        f.write(message_utils.build("inf_generated_by", user=self.client.user.name, time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        f.seek(0)
        expand = message_utils.build("inf_expand") if f.getvalue().count("\n") > 5 else ""
        await ctx.send(content=message_utils.build("inf_message", expand=expand), file=discord.File(f, "infractions.md"))
        return
        

async def setup(client: Bot):
    await client.add_cog(Mod(client=client))
