import discord
from discord.ext import commands

from utils import MessageUtils


class HelpMenu(discord.ui.Select):
    def __init__(self, help_command, bot):

        options = [
            discord.SelectOption(
                label="All",
                description="View all commands and their description",
                default=True,
            ),
            discord.SelectOption(
                label="Admin", description="View all commands for the Admin cog"
            ),
            discord.SelectOption(
                label="Basic", description="View all commands for the Basic cog"
            ),
            discord.SelectOption(
                label="Core", description="View all commands for the Core cog"
            ),
            discord.SelectOption(
                label="Mod", description="View all commands for the Mod cog"
            ),
        ]
        self.help_command = help_command
        self.bot = bot
        super().__init__(min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "All":
            message = await MessageUtils.gen_bot_help(
                self.help_command, self.help_command.get_bot_mapping()
            )
            view = HelpView(self.help_command, self.bot)
        else:
            message = await MessageUtils.gen_cog_help(
                self.help_command, self.bot.get_cog(self.values[0])
            )
            view = HelpView(self.help_command, self.bot).set_default(
                label=self.values[0]
            )
        await interaction.response.edit_message(content=message, view=view)

    def set_default(self, label: str = None) -> discord.ui.Select:
        if label is None:
            return self
        else:
            for option in self.options:
                if option.label == label:
                    option.default = True
                elif option.label == "All":
                    option.default = False
        return self


class HelpView(discord.ui.View):
    def __init__(self, help_command, bot):
        super().__init__(timeout=None)
        self.help_command = help_command
        self.bot = bot

        # Adds the dropdown to our view object.
        self.add_item(HelpMenu(help_command, bot))

    def set_default(self, label: str = None) -> discord.ui.View:
        self.clear_items()
        self.add_item(HelpMenu(self.help_command, self.bot).set_default(label=label))
        return self
