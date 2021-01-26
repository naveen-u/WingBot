import discord
from discord.ext import commands
from utils.configManager import BotConfig


class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()
        self.botConfig = BotConfig()

    async def send_bot_help(self, mapping):
        helpMessage = discord.Embed(
            title="WingBot Help\t|\tModules", color=discord.Color.dark_blue()
        )
        for i in mapping.keys():
            if i is None:
                continue
            helpMessage.add_field(
                name=i.qualified_name, value=i.description, inline=False
            )
        helpMessage.set_footer(
            text=f"Type `{self.botConfig.commandPrefix}help <module>` to learn more about that module."
        )
        await self.get_destination().send(embed=helpMessage)

    async def send_cog_help(self, cog):
        options = ""
        l = []
        for i in cog.walk_commands():
            if i not in l:
                options += (
                    f"`{self.botConfig.commandPrefix}{i.qualified_name}` | {i.help}\n"
                )
                l.append(i)
        helpMessage = discord.Embed(
            title=f"WingBot Help\t|\t{cog.qualified_name}",
            color=discord.Color.dark_blue(),
        )
        helpMessage.add_field(name="Description", value=cog.description)
        helpMessage.add_field(name="Options", value=options, inline=False)
        helpMessage.set_footer(
            text=f"Type `{self.botConfig.commandPrefix}help <command>` to learn more about a command."
        )
        await self.get_destination().send(embed=helpMessage)

    async def send_group_help(self, group):
        options = ""
        l = []
        for i in group.walk_commands():
            if i not in l:
                options += (
                    f"`{self.botConfig.commandPrefix}{i.qualified_name}` | {i.help}\n"
                )
                l.append(i)
        helpMessage = discord.Embed(
            title=f"WingBot Help\t|\t`{self.botConfig.commandPrefix}{group.qualified_name}`",
            color=discord.Color.dark_blue(),
        )
        helpMessage.add_field(name="Description", value=group.short_doc)
        helpMessage.add_field(name="Options", value=options, inline=False)
        helpMessage.set_footer(
            text=f"Type `{self.botConfig.commandPrefix}help <command>` to learn more about a command."
        )
        await self.get_destination().send(embed=helpMessage)

    async def send_command_help(self, command):
        helpMessage = discord.Embed(
            title=f"WingBot Help\t|\t`{self.botConfig.commandPrefix}{command.qualified_name}`",
            color=discord.Color.dark_blue(),
        )
        helpMessage.add_field(name="Description", value=command.help)
        helpMessage.add_field(
            name="Usage",
            value=f"`{self.botConfig.commandPrefix}{command.qualified_name} {command.signature}`",
            inline=False,
        )
        if command.aliases:
            aliasString = ""
            for i in command.aliases:
                aliasString += (
                    f"`{self.botConfig.commandPrefix}{command.full_parent_name} {i}`\n"
                )
            helpMessage.add_field(name="Aliases", value=aliasString, inline=False)
        await self.get_destination().send(embed=helpMessage)
