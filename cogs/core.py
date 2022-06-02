import time

from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.ext.commands.errors import (
    BadArgument,
    CommandNotFound,
    MissingPermissions,
)

import discord
from PaperZeppelin import Client


class MissingArgument(commands.UserInputError):
    def __init__(self, param: str) -> None:
        self.param: str = param
        super().__init__(f"{param} is a required argument that is missing.")


class Core(commands.Cog):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is online")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, CommandNotFound):
            return
        if isinstance(error, MissingPermissions):
            await ctx.send("You are not allowed to use this command")
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing a required parameter")
            return
        if isinstance(error, BadArgument):
            await ctx.send("Failed to parse your arguements")
            return
        if isinstance(error, commands.NotOwner):
            await ctx.send("You are not the bot owner.")
            return
        if isinstance(error, commands.BadUnionArgument):
            return
        if isinstance(error, MissingArgument):
            e = discord.Embed(
                colour=0xE84118,
                title="Missing a required parameter `{}`".format(error.param),
                description="Correct command usage: `{}`".format(
                    self.client.get_command_signature(
                        ctx.command.qualified_name, ctx.clean_prefix
                    )
                ),
            )
            await ctx.send(embeds=[e])
            return
        raise error

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            if message.author.id == self.client.user.id:
                self.client.self_messages += 1
            self.client.bot_messages += 1
            return
        self.client.user_messages += 1

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Get the approximate ping (Discord API -> Bot) in ms"""
        start_time = time.time()
        message = await ctx.send("Testing Ping...")
        end_time = time.time()

        await message.edit(
            content=f"⌛ REST API ping is {round((end_time - start_time) * 1000)} ms | Websocket ping is {round(self.client.latency * 1000)} ms ⌛"
        )


async def setup(client: Bot):
    await client.add_cog(Core(client=client))
