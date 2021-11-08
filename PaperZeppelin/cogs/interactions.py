import datetime
import discord
from discord import activity
from discord.client import Client
from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.errors import Forbidden
from discord.ext.commands.errors import (
    BadArgument,
    CommandNotFound,
    MemberNotFound,
    MissingPermissions,
)
import typing

from discord.interactions import Interaction
from utils import MessageUtils


class Interactions(commands.Cog):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client: Client = client

    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        if interaction.data["name"] == "presence":
            if interaction.data["options"][0]["name"] == "status":
                status: str = interaction.data["options"][0]["options"][0]["value"]
                client_status = self.client.status
                await self.client.change_presence(status=status)
                await interaction.response.send_message(
                    embed=MessageUtils.build(
                        type="status_update", before=client_status.value, after=status
                    )
                )
            elif interaction.data["options"][0]["name"] == "activity":
                activity_type = interaction.data["options"][0]["options"][0]["value"]
                client_activity = self.client.before_activity
                activity = discord.Activity()
                activity.type = activity_type
                activity.name = interaction.data["options"][0]["options"][1]["value"]
                print(self.client.status)
                await self.client.change_presence(
                    activity=activity, status=self.client.status
                )
                await interaction.response.send_message(
                    embed=MessageUtils.build(
                        type="presence_update", before=client_activity, after=activity
                    )
                )
                self.client.before_activity = f"`{activity.type}` {activity.name}"
        elif interaction.data["name"] == "User info":
            target = interaction.data["target_id"]
            user_dict = interaction.data["resolved"]["users"][target]
            if (
                "members" in interaction.data["resolved"]
                and target in interaction.data["resolved"]["members"]
            ):
                member_dict = interaction.data["resolved"]["members"][target]
                member_dict["user"] = user_dict
                member = discord.Member(
                    data=member_dict, guild=interaction.guild, state=interaction._state
                )
            await interaction.response.send_message(
                embed=MessageUtils.build(
                    type="user_info", member=member, issuer=interaction.user
                ),
                ephemeral=True,
            )


def setup(client: Bot):
    client.add_cog(Interactions(client=client))
