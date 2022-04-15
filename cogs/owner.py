from discord.ext import commands
import discord
import typing
from PaperZeppelin import Client

class New(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.command(name="modal")
    @commands.is_owner()
    async def modal(self, ctx: commands.Context):
        await ctx.send(content="Modal testing")

    @commands.command(name="sig")
    @commands.is_owner()
    async def sig(self, ctx: commands.Context, *, cmd: str):        
        await ctx.send(self.client.get_command_signature(cmd, ctx.clean_prefix))

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ModalCommandModal())

class ModalCommandView(discord.ui.View):
    def __init__(self, *, timeout: typing.Optional[float] = 180):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label="Click", style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(ModalCommandModal())

class ModalCommandModal(discord.ui.Modal, title="Command"):
    c = discord.ui.TextInput(label="Command", max_length=1000)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'{self.c.value}')

async def setup(client: commands.Bot):
    await client.add_cog(New(client))