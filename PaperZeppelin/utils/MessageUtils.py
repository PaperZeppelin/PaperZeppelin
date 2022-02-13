import datetime
import typing
import discord
from discord.activity import Activity, BaseActivity
from discord.ext import commands
from discord.ext.commands.help import HelpCommand


async def gen_bot_help(help_command: HelpCommand, mapping: typing.Mapping[typing.Optional[commands.Cog], typing.List[commands.Command]]) -> str:
    message = f"Need some help?\n"
    description = "These are all the enabled cogs**{}** that are usable by you.\nNeed more help? Join our support server!\n\n".format('in ' + help_command.context.guild.name if help_command.context.guild is not None else '')
    for cog in mapping:
        if cog is not None:
            if len(await help_command.filter_commands(mapping[cog])) > 0:
                description += f"**{cog.qualified_name}** {'- ' + cog.description if cog.description else ''}\n"
    return {
        "message": message,
        "embed": discord.Embed(colour=0x5865F2, description=description, title="PaperZeppelin Help").set_footer(
            text=f"Requested by {help_command.context.author.name}#{help_command.context.author.discriminator}", icon_url=help_command.context.author.display_avatar.url
        )
    }


async def gen_cog_help(help_command: commands.HelpCommand, cog: commands.Cog) -> str:
    message = f"Need some help with the {cog.qualified_name} cog?\n"
    description = "These are all the enabled commands that are usable by you.\nNeed more help? Join our support server!\n\n__{}__\n{}".format(cog.qualified_name, '```' + cog.description + '```\n' if cog.description else '') 
    filtered = await help_command.filter_commands(cog.get_commands())
    for command in filtered:
        description += f"**{help_command.context.prefix}{command.qualified_name}** {'- ' + command.short_doc if command.short_doc else ''}\n"
    return {
        "message": message,
        "embed": discord.Embed(colour=0x5865F2, description=description, title="PaperZeppelin Help").set_footer(
            text=f"Requested by {help_command.context.author.name}#{help_command.context.author.discriminator}", icon_url=help_command.context.author.display_avatar.url
        )
    } if len(filtered) > 0 else {
        "message": "🔒 You do not have permission to view this cog",
        "embed": discord.Embed(colour=0xED4245, title="This is awkward", description="Looks like you do not have permission to view the the contents of this cog").set_footer(
            text=f"Requested by {help_command.context.author.name}#{help_command.context.author.discriminator}", icon_url=help_command.context.author.display_avatar.url
        )
    }


async def gen_group_help(help_command: commands.HelpCommand, group: commands.Group) -> str:
    message = f"Need some help with the {group.qualified_name} command?\n"
    description = "These are all the enabled subcommands that are usable by you.\nNeed more help? Join our support server!\n\n__{}__\n{}".format(group.qualified_name, '```' + group.short_doc + '```\n' if group.short_doc else '') 
    filtered = await help_command.filter_commands(group.commands)
    for command in filtered:
        description += f"**{help_command.context.prefix}{command.qualified_name}** {'- ' + command.short_doc if command.short_doc else ''}\n"
    return {
        "message": message,
        "embed": discord.Embed(colour=0x5865F2, description=description, title="PaperZeppelin Help").set_footer(
            text=f"Requested by {help_command.context.author.name}#{help_command.context.author.discriminator}", icon_url=help_command.context.author.display_avatar.url
        )
    } if len(filtered) > 0 else {
        "message": "🔒 You do not have permission to view this command's subcommands",
        "embed": discord.Embed(colour=0xED4245, title="This is awkward", description="Looks like you do not have permission to view the the contents of this command's subcommands").set_footer(
            text=f"Requested by {help_command.context.author.name}#{help_command.context.author.discriminator}", icon_url=help_command.context.author.display_avatar.url
        )
    }
    
async def gen_command_help(help_command: commands.HelpCommand, command: commands.Command) -> str:
    message = f"Need some help?\n"
    description = f"**{help_command.context.prefix}{command.qualified_name}**"
    if command.short_doc:
        description += f"\n```{command.short_doc}```"
    if command.clean_params:
        description += "\n__Paramaters__\n"
        for (param_name, param_type) in command.clean_params.items():
            req = 'True' if ((param_type.kind == param_type.KEYWORD_ONLY) or (param_type.kind == param_type.VAR_KEYWORD)) else 'False'
            description += f"`{param_name}`\n╰ Default - {param_type.default if param_type.default is not param_type.empty else 'None'}\n╰ Required - {req}\n\n"
                       

    filtered = await help_command.filter_commands([command])
    return {
        "message": message,
        "embed": discord.Embed(colour=0x5865F2, description=description, title="PaperZeppelin Help").set_footer(
            text=f"Requested by {help_command.context.author.name}#{help_command.context.author.discriminator}", icon_url=help_command.context.author.display_avatar.url
        )
    } if len(filtered) > 0 else {
        "message": "🔒 You do not have permission to view this command's subcommands",
        "embed": discord.Embed(colour=0xED4245, title="This is awkward", description="Looks like you do not have permission to view the the contents of this command's subcommands").set_footer(
            text=f"Requested by {help_command.context.author.name}#{help_command.context.author.discriminator}", icon_url=help_command.context.author.display_avatar.url
        )
    }


def build(**kwargs):
    type = kwargs.get("type")
    if type is None:
        return "An internal error occured"
    else:
        if type == "user_info":
            return user_info(member=kwargs.get("member"), issuer=kwargs.get("issuer"))
        elif type == "status_update":
            return status_update(before=kwargs.get("before"), after=kwargs.get("after"))
        elif type == "presence_update":
            return presence_update(
                before=kwargs.get("before"), after=kwargs.get("after")
            )
        elif type == "verification_level":
            return verification_level(
                level=kwargs.get("level"), prefix=kwargs.get("prefix")
            )


def verification_level(level: int, prefix: str) -> str:
    if level == 0:
        return "There is currently no verification method set up for this server (use `{prefix}help cfg verification` to find out how to set it up)".format(
            prefix=prefix
        )
    elif level == 1:
        return "Current verification level: 1 (command)"


def user_info(
    member: typing.Union[discord.User, discord.Member], issuer: discord.User
) -> discord.Embed:
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    is_member = isinstance(member, discord.Member)

    embed = discord.Embed(
        colour=member.top_role.colour if is_member else 0x00CEA2, timestamp=now
    )
    embed.set_thumbnail(url=member.avatar.url)

    embed.add_field(
        name="Name", value=f"{member.name}#{member.discriminator}", inline=True
    )
    embed.add_field(name="ID", value=f"{member.id}", inline=True)
    embed.add_field(name="Bot account", value=f"{member.bot}", inline=True)
    embed.add_field(
        name="Animated avatar", value=f"{member.avatar.is_animated()}", inline=True
    )
    embed.add_field(
        name="Avatar url", value=f"[Avatar url]({member.avatar.url})", inline=True
    )
    embed.add_field(name="Profile", value=f"<@{member.id}>", inline=True)

    if is_member:
        embed.add_field(name="Nickname", value=member.nick, inline=False)
    if is_member:
        role_list = [
            role.mention
            for role in reversed(member.roles)
            if role is not member.guild.default_role
        ]
        if len(role_list) > 40:
            embed.add_field(name="Roles", value="Too many roles!", inline=False)
        elif len(role_list) > 0:
            embed.add_field(name="Roles", value=" ".join(role_list), inline=False)
        else:
            embed.add_field(name="Roles", value="No roles", inline=False)

    if is_member:
        embed.add_field(
            name="Joined at",
            value=f"{(now - member.joined_at).days} days ago, (``{member.joined_at}+00:00``)",
            inline=True,
        )

    embed.add_field(
        name="Created at",
        value=f"{(now - member.created_at).days} days ago, (``{member.created_at}+00:00``)",
        inline=True,
    )

    embed.set_footer(text=f"Requested by {issuer.name}", icon_url=issuer.avatar.url)
    return embed


def status_update(before: str, after: str) -> discord.Embed:
    embed = discord.Embed(
        color=0xE67E22,
        timestamp=datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc),
        description=f"```Updated status```",
    )
    embed.add_field(name="Before", value=before)
    embed.add_field(name="After", value=after)
    return embed


def presence_update(before: str, after: Activity) -> discord.Embed:
    embed = discord.Embed(
        color=0xE67E22,
        timestamp=datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc),
        description=f"```Updated activity```",
    )
    embed.add_field(name="Before", value=before)
    embed.add_field(name="After", value=f"`{after.type}` {after.name}")
    return embed
