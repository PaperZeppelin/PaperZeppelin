import discord
from discord import activity
from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.errors import Forbidden
from discord.ext.commands.errors import BadArgument, CommandNotFound, MemberNotFound, MissingPermissions
import json
import time

class Core(commands.Cog):

    def __init__(self, client) -> None:
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
            await ctx.send("🔒 You are not allowed to use this command")
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing a required parameter")
            return
        if isinstance(error, BadArgument):
            await ctx.send("Failed to convert your arguments")
            return
        raise error

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            if message.author.id == self.client.user.id:
                self.client.self_messages += 1
            self.client.bot_messages += 1
            return
        self.client.user_messages += 1

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        '''Get the approximate ping (Discord API -> Bot) in ms'''
        start_time = time.time()
        message = await ctx.send("Testing Ping...")
        end_time = time.time()

        await message.edit(content=f"⌛ REST API ping is {round((end_time - start_time) * 1000)} ms | Websocket ping is {round(self.client.latency * 1000)} ms ⌛")

def setup(client: Bot):
    client.add_cog(Core(client=client))