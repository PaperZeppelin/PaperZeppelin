from discord.ext import commands
import discord
import typing
from PaperZeppelin import Client
import ast


def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


class Owner(commands.Cog):
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

    @commands.command("eval")
    @commands.is_owner()
    async def eval_fn(self, ctx: commands.Context, *, input_code: str):
        """Evaluates python inputs"""
        fn_name = "eval_job"

        input_code = input_code.strip("```py ").strip("``` ")

        # add a layer of indentation
        input_code = "\n".join(f"    {i}" for i in input_code.splitlines())

        # wrap in async def body
        body = f"async def {fn_name}():{input_code}"

        parsed = ast.parse(body)
        parsed_body = parsed.body[0].body

        insert_returns(parsed_body)

        env = {
            "client": ctx.bot,
            "discord": discord,
            "commands": commands,
            "ctx": ctx,
            "__import__": __import__,
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        result = await eval(f"{fn_name}()", env)
        e = discord.Embed(colour=0x5865F2, title="Eval Job")
        e.add_field(name="📥 Input", value=f"```py\n{body}```", inline=False)
        e.add_field(name="📤 Output", value=f"```py\n{result}```", inline=False)
        e.set_footer(
            text=f"Executed by {ctx.author.name}#{ctx.author.discriminator}",
            icon_url=ctx.author.avatar.url,
        )
        await ctx.send(embeds=[e])


class ModalCommandView(discord.ui.View):
    def __init__(self, *, timeout: typing.Optional[float] = 180):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Click", style=discord.ButtonStyle.green)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_modal(ModalCommandModal())


class ModalCommandModal(discord.ui.Modal, title="Command"):
    c = discord.ui.TextInput(label="Command", max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{self.c.value}")


async def setup(client: commands.Bot):
    await client.add_cog(Owner(client))
