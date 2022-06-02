import asyncio
from typing import Optional, List, Dict

import discord
from asyncpg import Record
from discord.ext import commands
from discord.ui import View, Button
import re

from PaperZeppelin import Client
from discord import Embed

MAX_TAG_NAME_LENGTH = 85
MAX_TAG_RESPONSE_LENGTH = 1700

END_OF_MENTION_REGEX = re.compile("(?<=/d)>")


def clean(text: str) -> str:
    return END_OF_MENTION_REGEX.sub(
        "",
        text.replace("*", "")
        .replace("_", "")
        .replace("`", "")
        .replace("<@", "")
        .replace("<@&", "")
        .replace("<@#", "")
        .replace("<:", ""),
    )


class TagName(commands.clean_content):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        converted = await super().convert(ctx, argument)
        lower = converted.lower().strip()

        if not lower:
            raise commands.BadArgument("Missing tag name.")

        if len(lower) > 100:
            raise commands.BadArgument("Tag name is a maximum of 100 characters.")

        first_word, _, _ = lower.partition(" ")

        # get tag command.
        root: commands.GroupMixin = ctx.bot.get_command("tag")  # type: ignore
        if first_word in root.all_commands:
            raise commands.BadArgument("This tag name starts with a reserved word.")

        return lower


class Tags(commands.Cog):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client
        self._reserved: Dict[str, bool] = {
            "paperzeppelin": True,
            "paper zeppelin": True,
        }

    def is_reserved(self, key: str) -> bool:
        return key in self._reserved

    def reserve(self, name: str) -> bool:
        if self.is_reserved(name):
            return False
        else:
            self._reserved[name] = True
            return True

    def free(self, name: str) -> bool:
        if self.is_reserved(name):
            return False
        else:
            self._reserved.pop(name)
            return True

    @commands.group(name="tag", invoke_without_command=True)
    async def tag(self, ctx: commands.Context, *, name: Optional[str] = None):
        """Use a tag

        Examples
        --------
        * {prefix}tag help
          PaperZeppelin looks up the tag 'help' in its internal database and then sends the response
        * {prefix}tag pat's favourite song
          Tag names can include spaces
        * {prefix}tag WhEre are THe RUles
          Tag names are case insensetive

        Rules
        -----
        NOTE: Tags are moderated by the PaperZeppelin team
        NOTE: PaperZeppelin reserves the right to revoke tags without warning
        1. Ensure that tags follow Discord's TOS and Community Guidelines
        2. You may not use tags as a form of currency (trading is prohibited)
        3. Age restricted tags and targeted harrasment through tags are disallowed"""
        if ctx.invoked_subcommand is not None or name is None:
            return await ctx.send_help("tag")
        tag = await self.client.db.fetchrow(
            "SELECT id, response, uses FROM tags WHERE name=$1", name.lower()
        )
        if tag is None:
            return await ctx.send("Tag *{}* not found".format(name))
        await ctx.send(tag.get("response"))
        await self.client.db.execute(
            "UPDATE tags SET uses=$1 WHERE id=$2", tag.get("uses") + 1, tag.get("id")
        )

    @tag.command(name="info")
    async def info(self, ctx: commands.Context, *, name: str):
        """Get the tags information.

        Examples
        --------
        * {prefix}tag info help
          PaperZeppelin looks up the tag 'help' in its internal database and then sends the extracted data
        * {prefix}tag pat's favourite song
          Tag names can include spaces
        * {prefix}tag WhEre are THe RUles
          Tag names are case insensetive"""
        tag = await self.client.db.fetchrow(
            "SELECT * FROM tags WHERE name=$1", name.lower()
        )
        if tag is None:
            return await ctx.send("Tag *{}* not found".format(name))
        embed = Embed(colour=0x5865F2, title=tag.get("name"))
        embed.add_field(
            name="Owner",
            value=f'<@{tag.get("author_id")}>, {tag.get("author_clean")}\n\n**Seeing "@invalid-user" or '
            f'"@lotofnumbers"?**\nClick the button below',
            inline=False,
        )
        embed.add_field(name="Uses", value=tag.get("uses"))
        v = View().add_item(
            Button(url="discord://-/users/665488298533322762", label="Owner")
        )
        await ctx.send(embed=embed, view=v)

    @tag.command(name="list")
    async def list(self, ctx: commands.Context, *, query: Optional[str]):
        """Lists all tags

        Examples
        --------
        * {prefix}tag list
          PaperZeppelin will display the first tags in its compiled list. By default, sorted by ID
        * {prefix}tag list the best tag
          Shows all tags containing the name 'the best tag'
        """
        tags: List[Record] = (
            await self.client.db.fetch(
                "SELECT * FROM tags WHERE position($1 in name)>0 LIMIT 20", query
            )
            if query is not None
            else await self.client.db.fetch("SELECT * FROM tags LIMIT 20")
        )
        clean_tags = "\n".join(
            [
                str(pos + 1)
                + ". "
                + row.get("name")
                + " (ID:"
                + str(row.get("id"))
                + ")"
                for pos, row in enumerate(tags)
            ]
        )
        embed = Embed(colour=0x5865F2, title="Tag list", description=clean_tags)
        embed.set_footer(
            text="Requested by {}".format(ctx.author.display_name),
            icon_url=ctx.author.avatar.url,
        )
        await ctx.send(embed=embed)

    @tag.command(name="make")
    async def make(self, ctx: commands.Context):
        """Interactive walk through of making tags

        Examples
        -------
        * {prefix}tag make"""
        convertor = TagName()
        original = ctx.message

        def check(msg):
            return msg.author == ctx.author and ctx.channel == msg.channel

        await ctx.send("What would you like your tag to be called?")

        try:
            name = await self.client.wait_for("message", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took long. Cancelling setup.")

        try:
            ctx.message = name
            name = clean(await convertor.convert(ctx, name.content))
        except commands.BadArgument as e:
            return await ctx.send(
                f'{e}. Redo the command "{ctx.prefix}tag make" to retry.'
            )
        finally:
            ctx.message = original

        if self.is_reserved(name):
            return await ctx.send(
                "The name you chose is currently reserved. You can however try again later."
            )

        query = """SELECT 1 FROM tags WHERE LOWER(name)=$1;"""
        row = await self.client.db.fetchrow(query, name.lower())
        if row is not None:
            return await ctx.send(
                "This tag name has already been taken. Please retry with another name"
            )

        self.reserve(name)
        await ctx.send(
            "I set your tag's name to {}\n🤔 Now what do you want the response to be? *You can do {}cancel*".format(
                name, ctx.clean_prefix
            )
        )

        try:
            msg = await self.client.wait_for("message", check=check, timeout=300.0)
        except asyncio.TimeoutError:
            self.free(name)
            return await ctx.send("You took too long. Cancelled tag creation.")

        if msg.content == f"{ctx.prefix}cancel":
            self.free(name)
            return await ctx.send("Cancelled.")
        elif msg.content:
            clean_content = await commands.clean_content().convert(ctx, msg.content)
        else:
            # fast path I guess?
            clean_content = msg.content

        if msg.attachments:
            clean_content = f"{clean_content}\n{msg.attachments[0].url}"

        if len(clean_content) > 2000:
            return await ctx.send("Tag content is a maximum of 2000 characters.")

        try:
            await self.client.db.execute(
                "INSERT INTO tags (name, response, uses, author_id, author_clean) VALUES ($1, $2, 0, $3, $4)",
                name,
                clean_content,
                ctx.author.id,
                ctx.author.display_name,
            )
            await ctx.send("All done!")
        finally:
            self.free(name)

    @tag.command(name="remove")
    @commands.is_owner()
    async def remove(self, ctx: commands.Context, *, name: str):
        """Deletes a tag

        Purpose
        -------
        The purpose of the command is for MODERATION, which is why it is restricted to the owner only
        """
        backup: Record = await self.client.db.fetchrow(
            "SELECT * FROM tags WHERE name=$1", name
        )
        await self.client.db.execute("DELETE FROM tags WHERE name=$1", name)
        message = await ctx.send(
            "All done. Deleted tag {}\n\n**If this was a mistake react with ♻ to restore the tag.**".format(
                name
            )
        )
        await message.add_reaction("♻")

        def check(reaction, user):
            return user.id == ctx.author.id and message.id == reaction.message.id

        try:
            _, _ = await self.client.wait_for(
                "reaction_add", check=check, timeout=300.0
            )
            await self.client.db.execute(
                "INSERT INTO tags (id, name, response, uses, author_id, author_clean) VALUES ($1, $2, $3, $4, $5, $6)",
                backup.get("id"),
                backup.get("name"),
                backup.get("response"),
                backup.get("uses"),
                backup.get("author_id"),
                backup.get("author_clean"),
            )
            await ctx.send("Restored tag {}".format(name))
            await message.clear_reactions()
        except asyncio.TimeoutError:
            return await ctx.send("Tag {} permanently deleted".format(name))
        except AttributeError:
            pass


async def setup(client: Client):
    await client.add_cog(Tags(client))
