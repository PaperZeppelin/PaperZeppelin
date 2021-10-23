from discord.ext import commands
from discord.ext.commands.help import HelpCommand


async def gen_bot_help(help_command: HelpCommand, mapping) -> str:
    message = f"**Paper Zeppelin help 1/1**\n```diff\n"
    for cog in mapping:
        if cog is not None:
            filtered = await help_command.filter_commands(mapping[cog])
            commands = "\n".join([f"  {command.name}{' ' * (14 - len(command.name))}{command.short_doc}{help_command.is_group(command)}" for command in filtered])
            if cog.qualified_name == "Basic":
                commands += "\n  help          List all commands, and get info on commands" if cog.qualified_name == "Basic" else ""
            message += f'- {cog.qualified_name}\n{commands}\n' if len(commands) > 0 else "\n"
    message += f"You can get more info about a command (params and subcommands) by using '{help_command.context.clean_prefix}help <command>'\nCommands followed by ↪ have subcommands."
    message += "\n```"
    return message

async def gen_cog_help(help_command, cog) -> str:
    message = f"**Paper Zeppelin help 1/1**\n```diff\n- {cog.qualified_name}\n"
    filtered = await help_command.filter_commands(cog.get_commands())
    commands = "\n".join([f"{command.name}{' ' * (14 - len(command.name))}{command.short_doc}{help_command.is_group(command)}" for command in filtered])
    commands += "\nhelp          List all commands, and get info on commands\n" if cog.qualified_name == "Basic" else ""
    message += f'{commands}\n'
    message += f"You can get more info about a command (params and subcommands) by using '{help_command.context.clean_prefix}help <command>'\nCommands followed by ↪ have subcommands."
    message += "\n```" 
    return message if len(filtered) > 0 or cog.qualified_name == "Basic" else "🔒 You do not have permission to view this cog"

async def gen_group_help(help_command, group: commands.Group) -> str:
    message = f"**Paper Zeppelin help 1/1**\n```diff\n"
    filtered = await help_command.filter_commands(group.commands)
    message += f"{help_command.context.clean_prefix}{group.full_parent_name} [{group.name}{'|' + '|'.join(group.aliases) if len(group.aliases) > 0 else ''}]\n"
    message += f"\n{group.short_doc}\n"
    message += "\nSubcommands:\n"
    commands = "\n".join([f"  {command.name}{' ' * (14 - len(command.name))}{command.short_doc}{help_command.is_group(command)}" for index, command in enumerate(group.commands)])
    message += f'{commands}\n'
    message += f"You can get more info about a command (params and subcommands) by using '{help_command.context.clean_prefix}help <command>'\nCommands followed by ↪ have subcommands."
    message += "\n```"
    return message if len(filtered) > 1 or group.cog.qualified_name == "Basic" else "🔒 You do not have permission to view this command"

async def gen_command_help(help_command, command) -> str:
    message = f"**Paper Zeppelin help 1/1**\n```diff\n"
    filtered = await help_command.filter_commands([command])
    commands = f"{help_command.context.clean_prefix}  {command.name}\n\n{command.short_doc}"
    message += f'{commands}\n'
    message += "\n```"
    return message if len(filtered) > 0 else "🔒 You do not have permission to view this command"