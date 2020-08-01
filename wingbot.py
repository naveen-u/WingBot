import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.configManager import BotConfig
from utils.help import HelpCommand
import signal
import sys
import asyncio

load_dotenv()
# TOKEN = os.getenv('DISCORD_TOKEN')
TOKEN = 'NjkzMzkyMzczNzk5MDU5NDU3.Xn8Z-A.HGEqVTUVD2OLyzIN7KSTLRz-rdc'
config = BotConfig()
bot = commands.Bot(command_prefix = config.commandPrefix, case_insensitive = True)

async def signalHandler():
    """
    Signal handler to perform required cleanup operations before quitting bot
    """
    print('Cleaning up the mess...')
    for item in config.cogs:
        cog = bot.get_cog(item.capitalize())
        print(f'Executing signal handlers of the {item} cog...')
        if hasattr(cog, 'signalHandler'):
            cog.signalHandler()
    await bot.close()

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
    loop = asyncio.get_event_loop()
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame), lambda: asyncio.ensure_future(signalHandler()))
    return

# Adding custom help command
helpCommand = HelpCommand()
bot.help_command = helpCommand
bot.run(TOKEN)
