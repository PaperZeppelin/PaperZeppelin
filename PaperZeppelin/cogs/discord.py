import datetime
import discord
from discord.ext import commands
from math import floor

DISCORD_EPOCH = 1420070400000

class Discord(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        super().__init__()
        self.client = client

    def datetime_from_snowflake(self, snowflake: int) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(floor(int((snowflake >> 22) + DISCORD_EPOCH) / 1000)).replace(tzinfo=None)

    def timestamp_from_snowflake(self, snowflake: int) -> int: 
        return floor(int((snowflake >> 22) + DISCORD_EPOCH) / 1000)

    @commands.command(name="snowflake")
    async def snowflake(self, ctx: commands.Context, snowflake: int):
        """Get (useful?) information about a snowflake"""
        if ctx.invoked_subcommand is None:
            await ctx.send(embed= discord.Embed(
                    color=0x5865F2,
                )
                .set_image(url="https://discord.com/assets/94722171abc49573d1a129e2264da4ad.png")
                .add_field(name="Timestamp", value=f"{self.timestamp_from_snowflake(snowflake)} (<t:{self.timestamp_from_snowflake(snowflake)}:F>)")
            )

def setup(client):
    client.add_cog(Discord(client=client))
