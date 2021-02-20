import asyncio
import os
import signal

import discord
import pymongo
from discord.ext import commands
from dotenv import load_dotenv
from utils.configManager import BotConfig
from utils.help import HelpCommand

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")
config = BotConfig()
bot = commands.Bot(command_prefix=config.commandPrefix, case_insensitive=True)

db_client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)

bot.config = config
bot.db_client = db_client


async def signal_handler():
    """
    Signal handler to perform required cleanup operations before quitting bot
    """
    print("Cleaning up the mess...")
    for item in config.cogs:
        cog = bot.get_cog(item.capitalize())
        print(f"Executing signal handlers of the {item} cog...")
        if hasattr(cog, "signal_handler"):
            cog.signal_handler()
    db_client.close()
    await bot.close()


@bot.event
async def on_ready():
    """
    Finish set up once bot is ready
    """
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")
    await bot.change_presence(activity=discord.Game(name=config.activity))
    cogs = config.cogs
    cog_directory = config.cogDirectory
    for cog in cogs:
        try:
            bot.load_extension(cog_directory + "." + cog)
        except commands.errors.ExtensionAlreadyLoaded:
            pass
    loop = asyncio.get_event_loop()
    for signame in ("SIGINT", "SIGTERM"):
        loop.add_signal_handler(
            getattr(signal, signame), lambda: asyncio.ensure_future(signal_handler())
        )
    return


# Adding custom help command
helpCommand = HelpCommand()
bot.help_command = helpCommand
bot.run(TOKEN)
