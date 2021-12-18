from discord.ext import commands
import discord


class Verification(commands.Cog):
    def __init__(self, client: discord.Client) -> None:
        super().__init__()
        self.client = client


def setup(client: commands.Bot):
    client.add_cog(Verification(client=client))
