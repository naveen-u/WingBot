import discord
import random
from discord.ext import commands
import asyncio
from utils.configManager import BotConfig
import csv

with open("cogs/words.txt", "r") as f:
    lines = f.readlines() 

class TugOfWar(commands.Cog):
    """Play Tug of War."""
    def __init__(self, bot):
        self.bot = bot
        self.channelStates = {}
        self.bot_config = BotConfig()
        self.players = {}
        self.position = {}
        self.teamRed = {}
        self.teamBlue = {}
        self.currword = {}
        self.locks = {}

    def getword(self):
        word = random.choice(lines)
        return word.strip()

    @commands.command()
    async def tugofwar(self, ctx):
        """Start a game of Tug of War."""
        if str(ctx.channel.id) not in self.channelStates:
            self.channelStates[str(ctx.channel.id)] = "joining"
            embed = discord.Embed(
                title = ctx.message.author.name + ' started a game of Tug of War',
                description = 'Type the given words to pull the rope towards your side. Wait for more people to join, then type **'+ 
                self.bot_config.commandPrefix + 
                'start** to start the game.',
                colour = discord.Colour.blue()
            )
            embed.set_footer(text = "Join the game with " + self.bot_config.commandPrefix + "join.")
            self.players[str(ctx.channel.id)] = set()
            self.position[str(ctx.channel.id)] = 100
            self.teamRed[str(ctx.channel.id)] = set()
            self.teamBlue[str(ctx.channel.id)] = set()
            self.players[str(ctx.channel.id)].add(ctx.author.display_name)
            self.currword[str(ctx.channel.id)] = self.getword()
            self.locks[str(ctx.channel.id)] = asyncio.Lock()
            await ctx.send(embed = embed)
            # try:
            #     await self.teamsTugOfWar(ctx)
            # except Exception as e:
            #     print(ctx.channel.id + ' Bruh, exception: ' + e)
        elif self.channelStates[str(ctx.channel.id)] == "joining":
            embed = discord.Embed(
                title = "You're in luck, there's a game waiting for people!",
                description = 'Join with **'+ self.bot_config.commandPrefix + 'join**.',
                colour = discord.Colour.green()
            )
            await ctx.send(embed = embed)
        else:
            embed = discord.Embed(
                title = "There's already a game running here, fool.",
                description = 'Try running the command in another channel or be mean and stop the ongoing game with **'+ self.bot_config.commandPrefix + 'stop**.',
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed)

    @commands.command()
    async def join(self, ctx):
        """Join an existing game of Tug of War."""

        if str(ctx.channel.id) not in self.channelStates:
            embed = discord.Embed(
                title = "No game going on here dumdum",
                description = 'Start one with **'+ self.bot_config.commandPrefix + 'tugofwar**.',
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed)
        elif self.channelStates[str(ctx.channel.id)] == "joining":
            self.players[str(ctx.channel.id)].add(ctx.author.display_name)
            embed = discord.Embed(
                title = "Welcome, {0}!".format(ctx.author.display_name),
                description = "So far we have " + ", ".join(self.players[str(ctx.channel.id)]),
                colour = discord.Colour.green()
            )
            embed.set_footer(text = "Start the game with " + self.bot_config.commandPrefix + "start.")
            await ctx.send(embed = embed)
        else:
            embed = discord.Embed(
                title = "The game's already started. __Without you.__",
                description = 'Go cry a bit, and once this game is done, start another with **'+ self.bot_config.commandPrefix + 'tugofwar**.',
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed)

    def pick_teams(self, ctx):
        teamsize = len(self.players[str(ctx.channel.id)])//2
        self.teamBlue[str(ctx.channel.id)] = set(random.sample(self.players[str(ctx.channel.id)], teamsize))
        self.teamRed[str(ctx.channel.id)] = self.players[str(ctx.channel.id)].difference(self.teamBlue[str(ctx.channel.id)])

    @commands.command()
    async def start(self, ctx):
        """Finally start the game of Tug of War."""
        if str(ctx.channel.id) not in self.channelStates:
            embed = discord.Embed(
                title = "No game going on here dumdum",
                description = 'Start one with **'+ self.bot_config.commandPrefix + 'tugofwar**.',
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed)
        elif len(self.players[str(ctx.channel.id)]) < 2:
            embed = discord.Embed(
                title = "I know you have no friends but you can't play with yourself. Play Tug of War, that is.",
                description = "Ask people to join and maybe they'll eventually take pity on you.",
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed)
        elif self.channelStates[str(ctx.channel.id)] == "joining":
            self.channelStates[str(ctx.channel.id)] = "running"
            print(self.channelStates[str(ctx.channel.id)])
            self.pick_teams(ctx)  
            embed = discord.Embed(
                title = "The game has begun.",
                description = "Sit down, grab your popcorn, get back up, and keep typing to pull the rope towards your side.",
                colour = discord.Colour.green()
            )
            await ctx.send(embed = embed)
            embed = discord.Embed(
                title = "Team Red:",
                description = ", ".join(self.teamRed[str(ctx.channel.id)]),
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed)
            embed = discord.Embed(
                title = "Team Blue:",
                description = ", ".join(self.teamBlue[str(ctx.channel.id)]),
                colour = discord.Colour.blue()
            )
            await ctx.send(embed = embed)
            await ctx.send("Your first word is `{0}`".format(self.currword[str(ctx.channel.id)]))
        else:
            embed = discord.Embed(
                title = "Game's already started idiot",
                description = "Go watch",
            )
            await ctx.send(embed = embed)

    def getpositionembed(self, channel):
        winning_team = "Red" if self.position[str(channel.id)] < 100 else "Blue"
        strleft = "oO"
        for i in range(0, self.position[str(channel.id)], 5):
            strleft += '-'
        strright = "|"
        for i in range(self.position[str(channel.id)], 200, 5):
            strright += '-'
        top = "----------------------v----------------------\n"
        embed = discord.Embed(
            title = "{0} is leading!".format(winning_team),
            description = top + strleft + strright + "Oo", #each dash is supposed to be 5 units,
            colour = discord.Colour.red() if winning_team == "Red" else discord.Colour.blue()
        )
        return embed

    @commands.Cog.listener()
    async def on_message(self, message):    
        if message.author == self.bot.user:
            return
        if str(message.channel.id) not in self.channelStates:
            return
        if self.channelStates[str(message.channel.id)] == "joining":
            return
        if self.channelStates[str(message.channel.id)] == "running":
            async with self.locks[str(message.channel.id)]:
                print(str.lower(message.content) + "||")
                print(self.currword[str(message.channel.id)] + "||")
                if str.lower(message.content) == self.currword[str(message.channel.id)]:
                    if(message.author.display_name in self.players[str(message.channel.id)]):
                        addval = 10 if message.author.display_name in self.teamBlue[str(message.channel.id)] else -10
                        self.position[str(message.channel.id)] += addval
                        print("k")
                        if(self.position[str(message.channel.id)] == 0):
                            await self.concludeGame(message.channel, "Red", "Blue")
                            return
                        elif(self.position[str(message.channel.id)] == 200):
                            await self.concludeGame(message.channel, "Blue", "Red")
                            return
                        elif(self.position[str(message.channel.id)] % 20 == 0):
                            await message.channel.send(embed = self.getpositionembed(message.channel))
                        #put the new word
                        print("ok")
                        self.currword[str(message.channel.id)] = self.getword()
                        await message.channel.send("Now type `{0}`".format(self.currword[str(message.channel.id)]))

    
    async def concludeGame(self, channel, winning_team, losing_team):
        embed = discord.Embed(
            title = "{0} won!".format(winning_team),
            description = "lol get rekt {0}".format(losing_team),
            colour = discord.Colour.red() if winning_team == "Red" else discord.Colour.blue()
        )
        await self.cleanTasks(channel)
        await channel.send(embed = embed)

    @commands.command()
    async def scores(self, ctx):
        """Get the current position."""
        await ctx.send(embed = self.getpositionembed(ctx.channel))

    @commands.command(name='stop', aliases=['quit', 'q', 's', 'end'])
    async def stop(self, ctx):
        """
        Stop an ongoing game of Tug of War.
        """
        embed = discord.Embed(
            title = "The game was aborted.",
            description = "Shame, {0} was winning.".format("Red" if self.position[str(ctx.channel.id)] < 100 else "Blue")
        )
        await self.cleanTasks(ctx.channel)
        await ctx.channel.send(embed = embed)
        
    async def cleanTasks(self, channel):
        """
        Clean up any existing game task.
        Parameters:
        channel (discord.TextChannel): Channel to clean up tasks in.
        """
        del self.channelStates[str(channel.id)] 
        del self.players[str(channel.id)]
        del self.position[str(channel.id)] 
        del self.teamRed[str(channel.id)] 
        del self.teamBlue[str(channel.id)] 
        del self.currword[str(channel.id)]
        del self.locks[str(channel.id)]

def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the Reddit cog on to the bot.
    """
    bot.add_cog(TugOfWar(bot))
        