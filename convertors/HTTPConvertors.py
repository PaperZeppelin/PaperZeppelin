from discord.ext import commands


class HeaderFlags(commands.FlagConverter):
    key: str
    value: str
