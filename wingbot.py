import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.configManager import BotConfig
from utils.help import HelpCommand

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
config = BotConfig()
bot = commands.Bot(command_prefix = config.commandPrefix, case_insensitive = True)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game(name = config.activity))
    cogs = config.cogs
    cogDirectory = config.cogDirectory
    for cog in cogs:
        try:
            bot.load_extension(cogDirectory + '.' + cog)
        except commands.errors.ExtensionAlreadyLoaded:
            pass
    return

helpCommand = HelpCommand()
bot.help_command = helpCommand
bot.run(TOKEN)
