import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.configManager import BotConfig

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
        bot.load_extension(cogDirectory + '.' + cog)
    return

bot.run(TOKEN)