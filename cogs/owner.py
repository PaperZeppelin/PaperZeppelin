from discord.ext import commands
import discord
import typing

class New(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command(name="modal")
    @commands.is_owner()
    async def modal(self, ctx: commands.Context):
        await ctx.send(content="Modal testing", view=ModalCommandView())

class ModalCommandView(discord.ui.View):
    def __init__(self, *, timeout: typing.Optional[float] = 180):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label="Click", style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(ModalCommandModal())

class ModalCommandModal(discord.ui.Modal, title="Testing"):
    c = discord.ui.TextInput(label="content", max_length=1000)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'{self.c.value}')

def setup(client: commands.Bot):
    client.add_cog(New(client))