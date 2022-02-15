import datetime, time
from io import StringIO
import typing
import aiohttp
from aiohttp.client import ClientSession
import discord
from discord import message
from discord import file
from discord.components import SelectOption
from discord.enums import DefaultAvatar
from discord.ext import commands
from discord.ext.commands.core import Command, Group, guild_only
from discord.ext.commands.errors import BadArgument, MemberNotFound
from discord.http import Route
from discord.ui import view
from discord.ui.select import Select
from convertors import HTTPConvertors

from utils import MessageUtils, MathUtils
from views.help import HelpView
from inspect import Parameter
import re
import os



class Basic(commands.Cog):
    """Basic utilities/information"""
    def __init__(self, client) -> None:
        super().__init__()
        self.client: commands.Bot = client
        self.client.help_command = Help()
        self.session = aiohttp.ClientSession

    @commands.command(name="about")
    async def about(self, ctx: commands.Context):
        uptime = (
            datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
            - self.client.start_time
        )
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        days, hours = divmod(hours, 24)
        minutes, seconds = divmod(remainder, 60)
        total = str(sum(len(guild.members) for guild in self.client.guilds))
        unique = str(len(self.client.users))
        description = f"Stats for shard 0\nI've been up for {days} days, {hours} hours, {minutes} minutes, {seconds} seconds\nI've recieved {self.client.user_messages} user messages, {self.client.bot_messages} bot messages ({self.client.self_messages} were mine)\nI'm serving {total} users ({unique} unique)"
        embed = discord.Embed(
            description=description,
            colour=0x00CEA2,
            timestamp=datetime.datetime.utcfromtimestamp(time.time()).replace(
                tzinfo=datetime.timezone.utc
            ),
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="userinfo", aliases=["user", "whois", "user_info", "user_profile"]
    )
    @commands.guild_only()
    async def userinfo(
        self,
        ctx: commands.Context, *,
        target: typing.Union[discord.Member, discord.User] = None,
    ):
        await ctx.send(
            embed=MessageUtils.build(type="user_info", member=target, issuer=ctx.author)
        )

    @userinfo.error
    async def userinfo_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("I can't find that member")
            return

    @commands.group(name="math")
    async def mathtools(self, ctx: commands.Context):
        """Root command for math tools"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help("math")

    @mathtools.command(name="fib")
    async def fib(self, ctx: commands.Context, *, n: str = None):
        """Compute the nth Fibbonaci term"""
        if n is None:
            await ctx.send_help("math fib")
        else:
            try:
                n = int(n.replace(" ", "").replace(",", ""))
                if n == 0:
                    await ctx.send_help("math fib")
                elif n < 0:
                    raise BadArgument()
                else:
                    try:
                        start_time = time.time()
                        fib = MathUtils.fib(n)
                        end_time = time.time()
                        await ctx.send(
                            f"The {n}th number in the classic Fibonnaci sequence is\n```{fib}\n```"
                        )
                    except RecursionError:
                        await ctx.send(
                            f"The number supplied ({n}) is greater then my threshold"
                        )
            except ValueError:
                raise BadArgument()

    @mathtools.command(name="tri")
    async def tri(self, ctx: commands.Context, *, n: str = None):
        """Compute the nth triangular number"""
        if n is None:
            await ctx.send_help("math tri")
        else:
            try:
                n = int(n.replace(" ", "").replace(",", ""))
                if n == 0:
                    await ctx.send_help("math tri")
                elif n < 0:
                    raise BadArgument()
                else:
                    start_time = time.time()
                    tri = MathUtils.tri(n)
                    end_time = time.time()
                    await ctx.send(f"The {n}th triangular number is\n```{tri}\n```")
            except ValueError:
                raise BadArgument()

    @commands.command(name="serverinfo", aliases=["server"])
    @commands.guild_only()
    async def server_info(self, ctx: commands.Context):
        guild = ctx.guild
        guild_features = ", ".join(guild.features)
        if guild_features == "":
            guild_features = None
        guild_made = guild.created_at.strftime("%d-%m-%Y")
        embed = discord.Embed(
            color=guild.roles[-1].color,
            timestamp=datetime.datetime.utcfromtimestamp(time.time()).replace(
                tzinfo=datetime.timezone.utc
            ),
        )
        if guild.icon is not None:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Name", value=guild.name, inline=True)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(
            name="Channels",
            value=f"📚 Categories: {str(len(guild.categories))}\n📝 Text channels: {str(len(guild.text_channels))}\n:microphone2: Voice channels: {str(len(guild.voice_channels))}\nTotal channels: {str(len(guild.text_channels) + len(guild.voice_channels))}",
            inline=True,
        )
        embed.add_field(
            name="Created at",
            value=f"{guild_made} ({(datetime.datetime.utcfromtimestamp(time.time()).replace(tzinfo=datetime.timezone.utc) - guild.created_at).days} days ago)",
            inline=True,
        )
        embed.add_field(name="VIP features", value=guild_features, inline=True)

        if guild.icon is not None:
            embed.add_field(
                name="Server icon",
                value=f"[Server icon]({guild.icon.url})",
                inline=True,
            )

        roles = ", ".join(role.name for role in guild.roles)
        embed.add_field(
            name="Roles",
            value=roles if len(roles) < 1024 else f"{len(guild.roles)} roles",
            inline=False,
        )

        if guild.emojis:
            emoji = "".join(str(e) for e in guild.emojis)
            embed.add_field(
                name="Server emoji",
                value=emoji if len(emoji) < 1024 else f"{len(guild.emojis)} emoji",
            )

        if guild.splash is not None:
            embed.set_image(url=guild.splash.url)
        if guild.banner is not None:
            embed.set_image(url=guild.banner.url)

        embed.set_footer(
            text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url
        )

        await ctx.send(embed=embed)


class Help(commands.HelpCommand):
    """Custom help command"""

    def __init__(self):
        super().__init__()

    def is_group(self, command: Command):
        return "\n  ↪" if isinstance(command, Group) else ""

    async def send_bot_help(self, mapping):

        help = await MessageUtils.gen_bot_help(self, mapping)
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(url="https://discord.gg/DbdMRVCbKG", style=discord.ButtonStyle.link, label="Support server", emoji=discord.PartialEmoji(
                name="influx_round",
                animated=False,
                id=936158443998416947
            ))
        )
        await self.get_destination().send(content=help["message"], embeds=[help["embed"]], view=view)

    async def send_cog_help(self, cog: commands.Cog):

        help = await MessageUtils.gen_cog_help(self, cog)
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(url="https://discord.gg/DbdMRVCbKG", style=discord.ButtonStyle.link, label="Support server", emoji=discord.PartialEmoji(
                name="influx_round",
                animated=False,
                id=936158443998416947
            ))
        )
        await self.get_destination().send(
            content=help["message"],
            embeds=[help["embed"]],
            view=view
        )

    async def send_group_help(self, group: commands.Group):

        help = await MessageUtils.gen_group_help(self, group)
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(url="https://discord.gg/DbdMRVCbKG", style=discord.ButtonStyle.link, label="Support server", emoji=discord.PartialEmoji(
                name="influx_round",
                animated=False,
                id=936158443998416947
            ))
        )
        await self.get_destination().send(
            content=help["message"],
            embeds=[help["embed"]],
            view=view
        )

    async def send_command_help(self, command: commands.Command):

        help = await MessageUtils.gen_command_help(self, command)
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(url="https://discord.gg/DbdMRVCbKG", style=discord.ButtonStyle.link, label="Support server", emoji=discord.PartialEmoji(
                name="influx_round",
                animated=False,
                id=936158443998416947
            ))
        )
        await self.get_destination().send(
            content=help["message"],
            embeds=[help["embed"]],
            view=view
        )
        

    async def command_not_found(self, string):
        return f"I can't seem to find any cog or command named {string}"


def setup(client):
    client.add_cog(Basic(client=client))
