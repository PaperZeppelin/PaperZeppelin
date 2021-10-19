import datetime
from io import StringIO
import discord
from discord import activity
from discord import message
from discord import permissions
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.errors import Forbidden
from discord.ext.commands.context import Context
from discord.ext.commands.core import command
from discord.ext.commands.errors import CommandNotFound
import json


configure_help = f"""
```diff
! [configure|config|cfg]

  prefix{' ' * 6}Change the guild prefix
  mod_roles{' ' * 3}Set mod roles for the server
```
"""

class Admin(commands.Cog):

    def __init__(self, client) -> None:
        super().__init__()
        self.client = client

    @commands.group(name="configure", aliases=["cfg", "config"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def configure(self, ctx: commands.Context):
        """Configure bot settings"""
        member_permissions = ctx.message.author.guild_permissions
        if ctx.invoked_subcommand is None and member_permissions.administrator:
            await ctx.channel.send(configure_help)
            return

    @configure.command(name = "prefix", invoke_without_command=True)
    async def prefix(self, ctx: commands.Context, *inputs):
        """Change the prefix"""
        prefix = self.client.guild_cache[ctx.guild.id]["prefix"]
        if len(inputs) == 0:
            await ctx.send(f"The current server prefix is `{prefix}`")
            return
        if len(inputs) == 1:
            member_permissions = ctx.message.author.guild_permissions
            if member_permissions.administrator:
                if len(inputs[0]) > 25:
                    await ctx.channel.send(f"Please use a shorter prefix")
                    return
                if isinstance(inputs[0], str):
                    await self.client.pg_con.execute('UPDATE guilds SET prefix = $1 WHERE id = $2', inputs[0], ctx.guild.id)
                    self.client.guild_cache[ctx.guild.id] = {
                        'prefix': inputs[0]
                    }
                    await ctx.channel.send(f"Succesfully set the prefix to `{inputs[0]}`")
                    return
                else:
                    await ctx.channel.send(f"I couldn't parse {inputs[0]}")
                    return

    @configure.group(name="mod_roles", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def mod_roles(self, ctx: commands.Context):
        """Manage mod roles"""
        member_permissions = ctx.message.author.guild_permissions
        if ctx.invoked_subcommand is None and member_permissions.administrator:
            mod_roles_desc = ""
            for role_id in self.client.guild_cache[ctx.guild.id]["mod_roles"]:
                mod_roles_desc += f"<@&{role_id}>\n"
            await ctx.channel.send(embed=Embed(title="Current mod roles", description=mod_roles_desc))
            return

    @mod_roles.command(name="add")
    @commands.has_permissions(administrator=True)
    async def mod_roles_add(self, ctx: commands.Context, inputs):
        """Add a mod role"""
        if(len(ctx.message.role_mentions) > 0):
            if (int(ctx.message.role_mentions[0].id) in self.client.guild_cache[ctx.guild.id]["mod_roles"]):
                await ctx.channel.send(f"❌ `{ctx.message.role_mentions[0].name}` is already a mod role!")
                return
            self.client.guild_cache[ctx.guild.id]["mod_roles"].append(int(ctx.message.role_mentions[0].id))
            await self.client.pg_con.execute("INSERT INTO mod_roles (guild_id, role_id) VALUES ($1, $2)", ctx.guild.id, ctx.message.role_mentions[0].id)
            await ctx.channel.send(f":white_check_mark:  `{str(ctx.message.role_mentions[0].name)}` is now a mod role.")
            return
        elif(ctx.guild.get_role(int(inputs)) is not None):
            if (int(ctx.guild.get_role(int(inputs)).id) in self.client.guild_cache[ctx.guild.id]["mod_roles"]):
                await ctx.channel.send(f"❌ `{ctx.guild.get_role(int(inputs)).name}` is already a mod role!")
                return
            self.client.guild_cache[ctx.guild.id]["mod_roles"].append(int(inputs))
            await self.client.pg_con.execute("INSERT INTO mod_roles (guild_id, role_id) VALUES ($1, $2)", ctx.guild.id, int(inputs))
            await ctx.channel.send(f":white_check_mark:  `{ctx.guild.get_role(int(inputs)).name}` is now a mod role.")
            return
        
        await ctx.channel.send(f"🔒 You do not have access to this command")
        return 
    
    @mod_roles.command(name="remove")  
    @commands.has_permissions(administrator=True) 
    async def mod_roles_remove(self, ctx: commands.Context, inputs):
        """Remove a mod role"""
        if(len(ctx.message.role_mentions) > 0):
            if (int(ctx.message.role_mentions[0].id) in self.client.guild_cache[ctx.guild.id]["mod_roles"]):
                self.client.guild_cache[ctx.guild.id]["mod_roles"].remove(int(ctx.message.role_mentions[0].id))
                await self.client.pg_con.execute("DELETE FROM mod_roles WHERE role_id = $1", ctx.message.role_mentions[0].id)
                await ctx.channel.send(f":white_check_mark:  `{str(ctx.message.role_mentions[0].name)}` is no longer a mod role.")
                return
            await ctx.channel.send(f"❌ `{ctx.message.role_mentions[0].name}` was not a mod role so I cannot remove it")
            return
        elif(ctx.guild.get_role(int(inputs)) is not None):
            if (int(ctx.guild.get_role(int(inputs)).id) in self.client.guild_cache[ctx.guild.id]["mod_roles"]):
                self.client.guild_cache[ctx.guild.id]["mod_roles"].remove(int(inputs))
                await self.client.pg_con.execute("DELETE FROM mod_roles WHERE role_id = $1", int(inputs))
                await ctx.channel.send(f":white_check_mark: `{ctx.guild.get_role(int(inputs)).name}` is no longer a mod role.")
                return
                   
            await ctx.channel.send(f"❌ `{ctx.guild.get_role(int(inputs)).name}` was not a mod role so I cannot remove it")
            return         

        await ctx.channel.send(f"🔒 You do not have access to this command")
        return 
                
        

    @commands.command(name="leave")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx: Context):
        """Force the bot to leave the server"""
        member_permissions = ctx.message.author.guild_permissions
        if(member_permissions.administrator):
            await ctx.channel.send(f"It's been an honour serving {ctx.guild.name}, but alas, my time as come")
            await ctx.guild.leave()
        else: 
            await ctx.channel.send(f"Only server admins can use this command!")

    @commands.command(name="quicklog", aliases=["ql", "quickl"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def quicklog(self, ctx: Context):
        """Get the past 25 interactions between the bot and the server"""
        member_permissions = ctx.message.author.guild_permissions
        if(member_permissions.administrator):
            f = StringIO()
            for log in self.client.logs[str(ctx.guild.id)][0:25]:
                f.write(f"{log}\n")

            length = f.getvalue().count("\n")
            f.write(f"\n\n\nShowing past {length} interaction(s)\nGenerated by {self.client.user.name} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            f.seek(0)

            await ctx.channel.send(content=f"Here are the past {length} interaction(s)", file=discord.File(f, "logs.txt"))
            return
        else: 
            await ctx.channel.send(f"Only server admins can use this command!")
        

def setup(client: Bot):
    client.add_cog(Admin(client=client))