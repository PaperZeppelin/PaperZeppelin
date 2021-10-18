import datetime, time
import discord
from discord import message
from discord.components import SelectOption
from discord.enums import DefaultAvatar
from discord.ext import commands
from discord.ext.commands.core import Command, Group, guild_only
from discord.ext.commands.errors import MemberNotFound
from discord.ui import view
from discord.ui.select import Select


from utils.message_utils import gen_bot_help, gen_cog_help, gen_group_help, gen_command_help
from views.help import HelpView

class Basic(commands.Cog):
    def __init__(self, client) -> None:
        super().__init__()
        self.client = client
        self.client.help_command = Help()
        
    @commands.command(name="about")
    async def about(self, ctx: commands.Context):
        uptime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) - self.client.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        days, hours = divmod(hours, 24)
        minutes, seconds = divmod(remainder, 60)
        total = str(sum(len(guild.members) for guild in self.client.guilds))
        unique = str(len(self.client.users))
        description = f"Stats for shard 0\nI've been up for {days} days, {hours} hours, {minutes} minutes, {seconds} seconds\nI've recieved {self.client.user_messages} user messages, {self.client.bot_messages} bot messages ({self.client.self_messages} were mine)\nI'm serving {total} users ({unique} unique)"
        embed = discord.Embed(description=description, colour=0x00cea2, timestamp=datetime.datetime.utcfromtimestamp(time.time()).replace(tzinfo=datetime.timezone.utc))
        await ctx.send(embed=embed)


    @commands.command(name="userinfo", aliases=["user", "whois", "user_info", "user_profile"])
    @commands.guild_only()
    async def userinfo(self, ctx: commands.Context, target: discord.Member = None):
        member = target if target is not None else ctx.message.author
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)


        embed = discord.Embed(colour=member.top_role.colour if member.top_role.colour is not None else 0x00cea2, timestamp=now)
        embed.set_thumbnail(url=member.avatar.url)

        embed.add_field(name="Name", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="ID", value=f"{member.id}", inline=True)
        embed.add_field(name="Bot account", value=f"{member.bot}", inline=True)
        embed.add_field(name="Animated avatar", value=f"{member.avatar.is_animated()}", inline=True)
        embed.add_field(name="Avatar url", value=f"[Avatar url]({member.avatar.url})", inline=True)
        embed.add_field(name="Profile", value=f"<@{member.id}>", inline=True)
        embed.add_field(name="Nickname", value=member.nick, inline=False)

        role_list = [role.mention for role in reversed(member.roles) if role is not ctx.guild.default_role]
        if len(role_list) > 40:
            embed.add_field(name="Roles", value="Too many roles!", inline=False)
        elif len(role_list) > 0:
            embed.add_field(name="Roles", value=" ".join(role_list), inline=False)
        else:
            embed.add_field(name="Roles", value="No roles", inline=False)

        embed.add_field(name="Joined at", value=f"{(now - member.joined_at).days} days ago, (``{member.joined_at}+00:00``)", inline=True)
        embed.add_field(name="Created at", value=f"{(now - member.created_at).days} days ago, (``{member.created_at}+00:00``)", inline=True)

        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @userinfo.error
    async def userinfo_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("I can't find that member")
            return

    @commands.command(name="serverinfo", aliases=["server"])
    @commands.guild_only()
    async def server_info(self, ctx: commands.Context):
        guild = ctx.guild
        guild_features = ", ".join(guild.features)
        if guild_features == "":
            guild_features = None
        guild_made = guild.created_at.strftime("%d-%m-%Y")
        embed = discord.Embed(color=guild.roles[-1].color, timestamp=datetime.datetime.utcfromtimestamp(time.time()).replace(tzinfo=datetime.timezone.utc))
        if guild.icon is not None:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Name", value=guild.name, inline=True)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=f"📚 Categories: {str(len(guild.categories))}\n📝 Text channels: {str(len(guild.text_channels))}\n:microphone2: Voice channels: {str(len(guild.voice_channels))}\nTotal channels: {str(len(guild.text_channels) + len(guild.voice_channels))}", inline=True)
        embed.add_field(name="Created at", value=f"{guild_made} ({(datetime.datetime.utcfromtimestamp(time.time()).replace(tzinfo=datetime.timezone.utc) - guild.created_at).days} days ago)", inline=True)
        embed.add_field(name="VIP features", value=guild_features, inline=True)

        if guild.icon is not None:
            embed.add_field(
                name="Server icon",
                value=f"[Server icon]({guild.icon.url})",
                inline=True
            )

        roles = ", ".join(role.name for role in guild.roles)
        embed.add_field(
            name="Roles",
            value=roles if len(roles) < 1024 else f"{len(guild.roles)} roles",
            inline=False
        )

        if guild.emojis:
            emoji = "".join(str(e) for e in guild.emojis)
            embed.add_field(
                name="Server emoji",
                value=emoji if len(emoji) < 1024 else f"{len(guild.emojis)} emoji"
            )

        if guild.splash is not None:
            embed.set_image(url=guild.splash.url)
        if guild.banner is not None:
            embed.set_image(url=guild.banner.url)

        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)



class Help(commands.HelpCommand):
    """Custom help command"""
    def __init__(self):
        super().__init__()

    def is_group(self, command: Command):
        return '\n  ↪' if isinstance(command, Group) else ''

    async def send_bot_help(self, mapping):

        message = await gen_bot_help(self, mapping)
        view = HelpView(self, self.context.bot)

        await self.get_destination().send(content=message, view=view)

    async def send_cog_help(self, cog: commands.Cog):

        message = await gen_cog_help(self, cog)
        view = HelpView(self, self.context.bot)

        await self.get_destination().send(content=message, view=view.set_default(cog.qualified_name))

    async def send_group_help(self, group: commands.Group):

        message = await gen_group_help(self, group)
        view = HelpView(self, self.context.bot)

        await self.get_destination().send(content=message, view=view.set_default(group.cog_name))

    async def send_command_help(self, command: commands.Command):

        message = await gen_command_help(self, command)
        view = HelpView(self, self.context.bot)

        await self.get_destination().send(content=message, view=view.set_default(command.cog_name))

    async def command_not_found(self, string):
        return f"I can't seem to find any cog or command named {string}"

def setup(client):
    client.add_cog(Basic(client=client))