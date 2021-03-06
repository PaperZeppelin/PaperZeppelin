import datetime
import functools
import json
import typing
from io import StringIO

from discord.errors import Forbidden
from discord.ext import commands, tasks
from discord.ext.commands.bot import Bot

import discord
from PaperZeppelin import Client
from cogs.core import MissingArgument
from convertors.convertors import TimeConverter
from discord import Member


class BanFlags(commands.FlagConverter, prefix="--", delimiter=" "):
    days: typing.Optional[int] = 0


class Mod(commands.Cog):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client
        self.mutes.start()

    @tasks.loop()
    async def mutes(self):
        next_task = await self.client.db.fetchrow(
            "SELECT * FROM mutes WHERE NOT expired ORDER BY expires_at LIMIT 1"
        )
        if next_task is None:
            self.mutes.cancel()
            return
        await discord.utils.sleep_until(next_task.get("expires_at"))
        await self.unmute(
            self.client.get_guild(next_task.get("guild")), next_task.get("user_id")
        )
        await self.client.db.execute(
            "UPDATE mutes SET expired = true WHERE id = $1", next_task.get("id")
        )

    async def unmute(self, guild: discord.Guild, user: int):
        """Unmutes a user; requires the user, guild and role to be cached"""
        if guild is None:
            return
        mute_role: typing.Union[discord.Role, None] = self.client.guild_cache[guild.id][
            "mute_role"
        ]
        if mute_role is None:
            return
        try:
            await guild.get_member(user).remove_roles(mute_role, reason="User unmuted")
        except:
            pass
        await self.log_inf(guild.id, user, "UNMUTE", "Mute expired")

    async def log_inf(
        self,
        guild: int,
        user: int,
        inf_type: str,
        reason: str,
        mod: int = 893799613855838231,
    ):
        await self.client.db.execute(
            "INSERT INTO infractions (guild_id, user_id, mod_id, type, reason) VALUES ($1, $2, $3,$4, $5)",
            guild,
            user,
            mod,
            inf_type,
            reason,
        )
        self.client.guild_cache[guild]["infractions"].append(
            {
                "id": await self.client.db.fetchval(
                    "SELECT last_value FROM infractions_id_seq"
                ),
                "time": datetime.datetime.now().replace(tzinfo=None),
                "guild_id": guild,
                "user_id": user,
                "mod_id": mod,
                "type": inf_type,
                "reason": reason,
            }
        )

    @staticmethod
    def is_staff_perms(**permissions: bool):
        async def predicate(ctx):
            try:
                getter = functools.partial(discord.utils.get, ctx.author.roles)
                staff = any(
                    getter(id=item) is not None
                    if isinstance(item, int)
                    else getter(name=item) is not None
                    for item in ctx.bot.guild_cache[ctx.guild.id]["mod_roles"]
                )
                return staff or (
                    await commands.has_guild_permissions(**permissions).predicate(ctx)
                )
            except AttributeError:
                return await commands.has_guild_permissions(**permissions).predicate(
                    ctx
                )

        return commands.check(predicate)

    @staticmethod
    def is_staff():
        async def predicate(ctx):
            try:
                getter = functools.partial(discord.utils.get, ctx.author.roles)
                staff = any(
                    getter(id=item) is not None
                    if isinstance(item, int)
                    else getter(name=item) is not None
                    for item in ctx.bot.guild_cache[ctx.guild.id]["mod_roles"]
                )
                return staff
            except AttributeError:
                return False

        return commands.check(predicate)

    def staff(self, ctx, member) -> bool:
        getter = functools.partial(discord.utils.get, member.roles)
        staffb = any(
            getter(id=item) is not None
            if isinstance(item, int)
            else getter(name=item) is not None
            for item in self.client.guild_cache[ctx.guild.id]["mod_roles"]
        )
        return staffb

    def staff_or_permission(self, ctx, member, permissions):
        staff = self.staff(ctx, member)
        return staff or permissions

    def can_interact(self, issuer: Member, target: Member):
        return (
            issuer.roles[len(issuer.roles) - 1].position
            > target.roles[len(target.roles) - 1].position
            or issuer.id == issuer.guild.owner.id
        )

    @commands.command(name="test")
    @is_staff_perms(view_audit_log=True)
    async def test_c(
        self, ctx: commands.Context, time: TimeConverter, p: typing.Optional[int]
    ):
        await ctx.send(time)

    @commands.command(name="ban")
    @commands.guild_only()
    @commands.bot_has_guild_permissions(ban_members=True)
    @is_staff_perms(ban_members=True)
    async def ban_command(
        self,
        ctx: commands.Context,
        members: commands.Greedy[typing.Union[discord.Member, discord.User]],
        reason: typing.Optional[str],
        *,
        flags: BanFlags,
    ):
        """Ban a user(s) from the server"""
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
                    if self.staff_or_permission(
                        ctx, member, member.guild_permissions.ban_members
                    ) or not (ctx.author.id == ctx.guild.owner_id):
                        failed.append(member)
                        continue
                await ctx.guild.ban(
                    user=member, reason=reason, delete_message_days=flags.deletedays
                )
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
                await ctx.send(
                    "??? Banned {} for reason: `{}`".format(members[0], reason)
                )
            elif total > 1:
                await ctx.send(
                    "??? Banned all {} users for reason: `{}`".format(total, reason)
                )
        else:
            if len(failed) == total:
                if total == 1:
                    await ctx.send("??? I could not ban {}.".format(members[0]))
                elif total > 1:
                    await ctx.send("??? I could not ban any users.")
            else:
                f = StringIO()
                for user in failed:
                    f.write(f"{user} - {user.id}\n")
                f.seek(0)
                await ctx.send(
                    "??? I banned {} users for `{}`. I've attached the users I could not ban.".format(
                        len(passed), reason
                    ),
                    files=[discord.File(f)],
                )

    @commands.command(name="kick")
    @commands.guild_only()
    @commands.bot_has_guild_permissions(kick_members=True)
    @is_staff_perms(kick_members=True)
    async def kick_command(
        self,
        ctx: commands.Context,
        members: commands.Greedy[typing.Union[discord.Member, discord.User]],
        reason: typing.Optional[str],
    ):
        """Kick user(s) from the server"""
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
                    if self.staff_or_permission(
                        ctx, member, member.guild_permissions.kick_members
                    ) or not (ctx.author.id == ctx.guild.owner_id):
                        failed.append(member)
                        continue
                await ctx.guild.kick(user=member, reason=reason)
                await self.client.db.execute(
                    "INSERT INTO infractions (guild_id, user_id, mod_id, type, reason) VALUES ($1, $2, $3,'KICK', $4)",
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
                        "type": "KICK",
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
                await ctx.send(
                    "??? Kicked {} for reason: `{}`".format(members[0], reason)
                )
            elif total > 1:
                await ctx.send(
                    "??? Kicked all {} users for reason: `{}`".format(total, reason)
                )
        else:
            if len(failed) == total:
                if total == 1:
                    await ctx.send("??? I could not kick {}.".format(members[0]))
                elif total > 1:
                    await ctx.send("??? I could not kick any users.")
            else:
                f = StringIO()
                for user in failed:
                    f.write(f"{user} - {user.id}\n")
                f.seek(0)
                await ctx.send(
                    "??? I kicked {} users for `{}`. I've attached the users I could not kick.".format(
                        len(passed), reason
                    ),
                    files=[discord.File(f)],
                )

    @commands.command(name="mute", aliases=["timeout", "tempmute"])
    @commands.guild_only()
    @is_staff_perms(moderate_members=True)
    async def tempmute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        time: typing.Optional[TimeConverter],
        *,
        reason: typing.Optional[str] = "No reason provided",
    ):
        if self.staff(ctx, member) or not (ctx.author.id == ctx.guild.owner_id):
            return await ctx.send(
                "??? The targeted member is above you in the role hierarchy"
            )
        try:
            mute_role = self.client.guild_cache[ctx.guild.id]["mute_role"]
            muted = discord.utils.get(member.roles, id=mute_role.id)
            if muted:
                return await ctx.send("???? But aren't they already muted?")
            await member.add_roles(mute_role, reason=f"User muted - Reason: {reason}")
            await self.log_inf(ctx.guild.id, member.id, "MUTE", reason, ctx.author.id)
            expires_at = (
                datetime.datetime.now(tz=None) + datetime.timedelta(seconds=time + 20)
                if time is not None
                else "Never"
            )
            await self.client.db.execute(
                "INSERT INTO mutes (user_id, expired, expires_at, guild) VALUES ($1, $2, $3, $4)",
                member.id,
                True if time is None else False,
                expires_at if time is not None else datetime.datetime.now(tz=None),
                ctx.guild.id,
            )
            await ctx.send(
                "??? Muted {user} for reason {reason}. The mute expires {expires_at}".format(
                    user=member.__str__(),
                    reason=reason,
                    expires_at=f"{'in ' + str(time) + '.' if time is not None else 'never.'}",
                )
            )
            if self.mutes.is_running():
                self.mutes.restart()
            else:
                self.mutes.start()
        except Exception as e:
            await ctx.send("??? Failed to mute user")
            raise e

    @commands.group(name="infractions", aliases=["inf"])
    @commands.guild_only()
    @is_staff_perms(view_audit_log=True)
    async def infractions(self, ctx: commands.Context):
        """Manage infractions"""
        if ctx.invoked_subcommand is not None:
            return
        infractions = self.client.guild_cache[ctx.guild.id]["infractions"]
        f = StringIO()
        f.write(
            f"\nID  |User               |Moderator          |Time                              |TYPE        |Reason \n{'-' * 98}\n"
        )
        for infraction in infractions[
            0 : (len(infractions) if len(infractions) < 100 else 100)
        ]:
            f.write(
                f"{infraction['id']}{' ' * (4 - len(str(infraction['id'])))}|{infraction['user_id']}{' ' * (19 - len(str(infraction['user_id'])))}|{infraction['mod_id']}{' ' * (19 - len(str(infraction['mod_id'])))}|{infraction['time'].isoformat()}+00:00{' ' * (34 - len(str(infraction['time'].isoformat() + '+00:00')))}|{infraction['type']}{' ' * (10 - len(str(infraction['type'])))}|{infraction['reason'] if infraction['reason'] is not None else ''}\n"
            )
        f.write(
            "Generated by {user} at {time}".format(
                user=self.client.user.name,
                time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
        f.seek(0)
        expand = (
            "\n*Make sure to click expand!*" if f.getvalue().count("\n") > 5 else ""
        )
        await ctx.send(
            content="???? Here are the infractions I've found {}".format(expand),
            file=discord.File(f, "infractions.md"),
        )
        return

    @infractions.command(name="add")
    @commands.guild_only()
    @is_staff()
    async def inf_add(
        self,
        ctx: commands.Context,
        members: commands.Greedy[typing.Union[discord.User, discord.Member]],
        *,
        note: str,
    ):
        """Adds a note to user(s)"""
        if len(members) < 1:
            raise commands.BadArgument
        for member in members:
            await self.client.db.execute(
                "INSERT INTO infractions (guild_id, user_id, mod_id, type, reason) VALUES ($1, $2, $3,'NOTE', $4)",
                ctx.guild.id,
                member.id,
                ctx.author.id,
                note,
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
                    "type": "NOTE",
                    "reason": note,
                }
            )
        await ctx.send(
            "??? Added the NOTE `{}` to {}.".format(
                note,
                f"{len(members)} users" if len(members) > 1 else members[0].__str__(),
            )
        )

    @infractions.command(name="dump")
    @commands.guild_only()
    @is_staff_perms(view_audit_log=True)
    async def dump(self, ctx: commands.Context):
        """Dump all infractions into a file"""
        infractions = self.client.guild_cache[ctx.guild.id]["infractions"]
        f = StringIO()
        to_dump = {"public": infractions}
        f.write(json.dumps(to_dump, sort_keys=True, indent=4, default=str))
        f.write(
            "Generated by {user} at {time}".format(
                user=self.client.user.name,
                time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ).replace("\n", "")
        )
        f.seek(0)
        await ctx.send(
            content="Dumping all the infractions",
            file=discord.File(f, "infractions.json"),
        )
        return

    @infractions.command(name="search")
    @commands.guild_only()
    @is_staff_perms(view_audit_log=True)
    async def searchdump(
        self, ctx: commands.Context, user: typing.Union[discord.User, discord.Member]
    ):
        """Get all infractions from a user"""
        infractions = self.client.guild_cache[ctx.guild.id]["infractions"]
        f = StringIO()
        f.write(
            f"\nID  |User               |Moderator          |Time                              |TYPE      |Reason \n{'-' * 96}\n"
        )
        for infraction in infractions:
            if infraction["user_id"] == user.id or infraction["mod_id"] == user.id:
                f.write(
                    f"{infraction['id']}{' ' * (4 - len(str(infraction['id'])))}|{infraction['user_id']}{' ' * (19 - len(str(infraction['user_id'])))}|{infraction['mod_id']}{' ' * (19 - len(str(infraction['mod_id'])))}|{infraction['time'].isoformat()}+00:00{' ' * (34 - len(str(infraction['time'].isoformat() + '+00:00')))}|{infraction['type']}{' ' * (10 - len(str(infraction['type'])))}|{infraction['reason'] if infraction['reason'] is not None else ''}\n"
                )
        f.write(
            "\n\n\nGenerated by {user} at {time}".format(
                user=self.client.user.name,
                time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
        f.seek(0)
        expand = (
            "\n*Make sure to click expand!*" if f.getvalue().count("\n") > 5 else ""
        )
        await ctx.send(
            content="???? Here are the infractions I've found {}".format(expand),
            file=discord.File(f, "infractions.md"),
        )
        return


async def setup(client: Bot):
    await client.add_cog(Mod(client=client))
