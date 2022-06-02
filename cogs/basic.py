import base64
import datetime
import time
import typing

from discord.ext import commands
from discord.ext.commands.errors import BadArgument

import discord
from discord import ButtonStyle
from utils import MathUtils

DESCRIPTION = 'Hello! Welcome to the help page.\n\nUse "{prefix}help command" for more info on a command.\nUse "{prefix}help category" for more info on a category.'
HELP_VIEW = discord.ui.View()
HELP_VIEW.add_item(
    discord.ui.Button(
        url="https://hippo.wtf/",
        style=discord.ButtonStyle.link,
        label="Support server",
    )
)


class Basic(commands.Cog):
    """A collection of commands standard across bots.

    This category offers commands that extract information, and some questionably useful tools."""

    def __init__(self, client) -> None:
        super().__init__()
        self.client: commands.Bot = client
        self.client.help_command = Help()

    @commands.command(name="about")
    async def about(self, ctx: commands.Context):
        """Get information about the bot.

        While this information may not be extremely helpful as an end user, it still is nice to know."""
        uptime = (
            datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
            - self.client.start_time
        )
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        days, hours = divmod(hours, 24)
        minutes, seconds = divmod(remainder, 60)
        total = str(sum(len(guild.members) for guild in self.client.guilds))
        unique = str(len(self.client.users))
        description = [
            "Stats for the bot",
            "I've been up for {days} days, {hours} hours, {minutes} minutes, {seconds} seconds".format(
                days=days, hours=hours, minutes=minutes, seconds=seconds
            ),
            "In this time, I've watched {user_messages} messages, {bot_messages} bot messages ({self_messages} were mine)".format(
                user_messages=self.client.user_messages,
                bot_messages=self.client.bot_messages,
                self_messages=self.client.self_messages,
            ),
            "I'm serving {total} users ({unique} unique)".format(
                total=total, unique=unique
            ),
        ]
        embed = discord.Embed(
            description="\n".join(description),
            colour=0x00CEA2,
            timestamp=datetime.datetime.utcfromtimestamp(time.time()).replace(
                tzinfo=datetime.timezone.utc
            ),
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="userinfo", aliases=["user", "whois", "user_info", "user_profile"]
    )
    async def userinfo(
        self,
        ctx: commands.Context,
        *,
        t: typing.Union[discord.Member, discord.User] = None,
    ):
        """Extracts information about a user.

        Aliases
        -------
        Many bots have different names for this command, for this reason PaperZeppelin has many aliases for this command.
        * user
        * whois
        * user_info
        * user_profile"""

        target = ctx.author if t is None else t
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        is_member = isinstance(target, discord.Member)
        embed = discord.Embed(
            colour=target.top_role.colour if is_member else 0x00CEA2, timestamp=now
        )
        embed.set_thumbnail(url=target.avatar.url)
        embed.add_field(
            name="Name", value=f"{target.name}#{target.discriminator}", inline=True
        )
        embed.add_field(name="ID", value=f"{target.id}", inline=True)
        embed.add_field(name="Bot account", value=f"{target.bot}", inline=True)
        embed.add_field(
            name="Avatar url", value=f"[Avatar url]({target.avatar.url})", inline=True
        )
        if is_member:
            embed.add_field(name="Nickname", value=target.nick, inline=False)
        if is_member:
            role_list = [
                role.mention
                for role in reversed(target.roles)
                if role is not target.guild.default_role
            ]
            if len(role_list) > 40:
                embed.add_field(name="Roles", value="Too many roles!", inline=False)
            elif len(role_list) > 0:
                embed.add_field(name="Roles", value=" ".join(role_list), inline=False)
            else:
                embed.add_field(name="Roles", value="No roles", inline=False)
            embed.add_field(
                name="Joined at",
                value=f"{(now - target.joined_at).days} days ago, (``{target.joined_at}+00:00``)",
                inline=True,
            )
        embed.add_field(
            name="Created at",
            value=f"{(now - target.created_at).days} days ago, (``{target.created_at}+00:00``)",
            inline=True,
        )
        embed.set_footer(
            text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url
        )
        view = discord.ui.View().add_item(
            discord.ui.Button(
                style=ButtonStyle.link,
                url=f"discord://-/users/{target.id}",
                label="Profile",
            )
        )
        await ctx.send(embed=embed, view=view)

    @commands.group(name="math")
    async def mathtools(self, ctx: commands.Context):
        """Use PaperZeppelin's computing power for maths

        This command only supports two basic algorithims, Nth fibinoacci number and Nth triangular number.

        This command is a ROOT command. Use one of the listed subcommands to use the specified tool."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help("math")

    @mathtools.command(name="fib")
    async def fib(self, ctx: commands.Context, *, n: str = None):
        """Calculates the Nth fibonacci number.

        This command uses a recursion to find the Nth term."""
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
                            "The {}th number in the classic Fibonnaci sequence is\n```{}\n```\nCalculated in `{}s`".format(
                                n, fib, end_time - start_time
                            )
                        )
                    except RecursionError:
                        await ctx.send(
                            "The number supplied ({}) is greater then my threshold".format(
                                n
                            )
                        )
            except ValueError:
                raise BadArgument()

    @mathtools.command(name="tri")
    async def tri(self, ctx: commands.Context, *, n: str = None):
        """Calculates the Nth triangular number

        Formula
        -------
            n * (n + 1)
        Tₙ = ━━━━━━━━━━━━
                2

        Representation
        --------------
        This is a representation of the 4th triangular number, 10

           1
          2 3
         4 5 6
        7 8 9 10
        """
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
                    await ctx.send(
                        "The {}th triangular number is\n```{}\n```\nCalculated in `{}s`".format(
                            n, tri, end_time - start_time
                        )
                    )
            except ValueError:
                raise BadArgument

    @commands.command(name="serverinfo", aliases=["server"])
    @commands.guild_only()
    async def server_info(self, ctx: commands.Context):
        """Extracts data from the current guild

        Due to privacy concerns, this command does NOT take a guild parameter."""
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

    @commands.command(name="encode")
    async def _encode(self, ctx: commands.Context, encoding: str, *, text: str):
        """Encode a string of characters, a "phrase", into the given encoding type

        Supported encodings
        -------------------
        NOTE: Key - Value means Name - Accepted encodings
        * base 64: b64, base64
        * base 32: b32, base32
        * base 16: b16, base16
        * base 85: b85, base85
        """
        e = discord.Embed(colour=0x5865F2)
        e.add_field(name="📥 Input", value=f"```{text}```", inline=False)
        e.set_footer(
            text=f"Executed by {ctx.author.name}#{ctx.author.discriminator}",
            icon_url=ctx.author.avatar.url,
        )
        if encoding in ("b64", "base64"):
            await ctx.send(
                embeds=[
                    e.add_field(
                        name="📤 Output",
                        value=f"```{base64.b64encode(text.encode('ascii')).decode('ascii')}```",
                    )
                ]
            )
        elif encoding in ("b32", "base32"):
            await ctx.send(
                embeds=[
                    e.add_field(
                        name="📤 Output",
                        value=f"```{base64.b32encode(text.encode('ascii')).decode('ascii')}```",
                    )
                ]
            )
        elif encoding in ("b16", "base16"):
            await ctx.send(
                embeds=[
                    e.add_field(
                        name="📤 Output",
                        value=f"```{base64.b16encode(text.encode('ascii')).decode('ascii')}```",
                    )
                ]
            )
        elif encoding in ("b85", "base85"):
            await ctx.send(
                embeds=[
                    e.add_field(
                        name="📤 Output",
                        value=f"```{base64.b16encode(text.encode('ascii')).decode('ascii')}```",
                    )
                ]
            )
        else:
            await ctx.send("An invalid or unsupported encoding type was provided")

    @commands.command(name="decode")
    async def _decode(self, ctx: commands.Context, encoding: str, *, text: str):
        """Decodes an already encoded string of characters, a "phrase", into the given encoding type

        Supported encodings
        -------------------
        NOTE: Key - Value means Name - Accepted encodings
        * base 64: b64, base64
        """
        e = discord.Embed(colour=0x5865F2)
        e.add_field(name="📥 Input", value=f"```{text}```", inline=False)
        e.set_footer(
            text=f"Executed by {ctx.author.name}#{ctx.author.discriminator}",
            icon_url=ctx.author.avatar.url,
        )
        if encoding in ("b64", "base64"):
            await ctx.send(
                embeds=[
                    e.add_field(
                        name="📤 Output",
                        value=f"```{base64.b64decode(text.encode('ascii') + b'==').decode('ascii')}```",
                    )
                ]
            )
        else:
            await ctx.send("An invalid or unsupported encoding type was provided")


class Help(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    def is_required(self, annotation: typing.Any) -> bool:
        if hasattr(annotation, "__origin__"):
            if annotation.__origin__ is typing.Union:
                return False
            else:
                return True
        else:
            return True

    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            color=0x5865F2,
            title="Bot Help",
            description=DESCRIPTION.format(prefix=self.context.clean_prefix),
        )
        embed.add_field(
            name="Support server",
            value="You can find a link to the support server in the button",
            inline=False,
        )
        all_cogs = list()
        for cog in mapping:
            if len(await self.filter_commands(mapping[cog])) > 0 and cog is not None:
                all_cogs.append(cog.qualified_name)
        embed.add_field(name="Categories", value="\n".join(all_cogs), inline=False)
        ctx = self.context
        embed.add_field(
            name="About",
            value=f"The bot is owned and developed by [Pat](https://discord.com/users/665488298533322762)",
            inline=False,
        )
        embed.add_field(
            name="Server",
            value=f"The prefix for {ctx.guild.name} is `{ctx.bot.guild_cache[ctx.guild.id]['prefix']}`",
            inline=False,
        )
        embed.set_footer(
            text=f"Executed by {ctx.author.name}#{ctx.author.discriminator}",
            icon_url=ctx.author.avatar.url,
        )

        await self.get_destination().send(embeds=[embed], view=HELP_VIEW)

    async def send_cog_help(self, cog: commands.Cog):
        embed = discord.Embed(
            color=0x5865F2,
            title="Category help",
            description=DESCRIPTION.format(prefix=self.context.clean_prefix),
        )
        embed.add_field(
            name="Support server",
            value="You can find a link to the support server in the button",
            inline=False,
        )
        all_commands = list()
        for command in await self.filter_commands(cog.get_commands()):
            all_commands.append(
                "{q} {h}".format(
                    q=command.qualified_name,
                    h=f"- {command.short_doc}" if command.short_doc != "" else "",
                )
            )
        embed.add_field(
            name=cog.qualified_name, value="\n".join(all_commands), inline=False
        )
        ctx = self.context
        embed.set_footer(
            text=f"Executed by {ctx.author.name}#{ctx.author.discriminator}",
            icon_url=ctx.author.avatar.url,
        )
        await self.get_destination().send(embeds=[embed], view=HELP_VIEW)

    async def send_group_help(self, group: commands.Group):
        embed = discord.Embed(
            color=0x5865F2,
            title="Command Help",
            description=DESCRIPTION.format(prefix=self.context.clean_prefix),
        )
        embed.add_field(
            name="Support server",
            value="You can find a link to the support server in the button",
            inline=False,
        )
        ctx = self.context
        if not await group.can_run(ctx):
            raise commands.MissingPermissions
        all_commands = list()
        if group.help is not None:
            all_commands.append(
                f"```{group.help.format(prefix=ctx.clean_prefix)}```"
            )  # hacky
            all_commands.append("**Subcommands**")
        else:
            all_commands.append("**Subcommands**")

        for command in await self.filter_commands(group.commands):
            all_commands.append(
                "{q} {h}".format(
                    q=command.name,
                    h=f"- {command.short_doc}" if command.short_doc != "" else "",
                )
            )
        embed.add_field(
            name=f"{group.cog.qualified_name} - `{group.qualified_name}`",
            value="\n".join(all_commands),
            inline=False,
        )
        ctx = self.context
        embed.set_footer(
            text=f"Executed by {ctx.author.name}#{ctx.author.discriminator}",
            icon_url=ctx.author.avatar.url,
        )
        await self.get_destination().send(embeds=[embed], view=HELP_VIEW)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            color=0x5865F2,
            title="Command Help",
            description=DESCRIPTION.format(prefix=self.context.clean_prefix),
        )
        embed.add_field(
            name="Support server",
            value="You can find a link to the support server in the button",
            inline=False,
        )
        ctx = self.context
        if not await command.can_run(ctx):
            raise commands.MissingPermissions
        commands_desc = list()
        if command.help is not None:
            commands_desc.append(f"```{command.help.format(prefix=ctx.prefix)}```")
        else:
            commands_desc.append(
                "🏗️ This command is currently under construction.\n\nThe command is missing documentation. Please let us know by joining the support server below."
            )
        embed.add_field(
            name=f"{command.cog.qualified_name} - `{command.qualified_name}`",
            value="\n".join(commands_desc),
            inline=False,
        )
        ctx = self.context
        params = ""
        if command.clean_params:
            for (param_name, param_type) in command.clean_params.items():
                required = self.is_required(param_type.annotation)
                default = f"`{param_name}`\n╰ Default - {param_type.default if param_type.default is not param_type.empty else 'None'}\n╰ Required - {required}\n\n"
                try:
                    if issubclass(param_type.annotation, commands.FlagConverter):
                        flags = param_type.annotation.get_flags()
                        params += f"`{param_name.capitalize()}`\n"
                        for k, v in flags.items():
                            required = self.is_required(v.annotation)
                            params += f"--{k}\n╰ Default - {param_type.default if param_type.default is not param_type.empty else 'None'}\n╰ Required - {required}\n\n"
                    else:
                        params += default
                except TypeError:
                    params += default
        if params != "":
            embed.add_field(name="Paramaters", value=params, inline=False)

        embed.set_footer(
            text=f"Executed by {ctx.author.name}#{ctx.author.discriminator}",
            icon_url=ctx.author.avatar.url,
        )
        await self.get_destination().send(embeds=[embed], view=HELP_VIEW)

    async def command_not_found(self, string):
        return "I can't seem to find any cog or command named {}".format(string)


async def setup(client):
    await client.add_cog(Basic(client=client))
