import discord
from discord.ext import commands
from utils.configManager import RedditConfig, BotConfig

class Misc(commands.Cog):
    """Miscellaneous commands."""
    def __init__(self, bot):
        self.bot = bot
        self.bot_config = BotConfig()

    @commands.command(usage = '"<question>" "<option1>" "<option2>" (the quotation marks are important)')
    async def poll(self, ctx, question: str, option1: str, option2: str):
        """Make polls."""

        commandmsg = await ctx.channel.fetch_message(ctx.channel.last_message_id)
        await commandmsg.delete()

        embed = discord.Embed(
            title = question,
            color = discord.Color.from_rgb(230, 0, 0)
        )

        embed.add_field(name = "A", value = option1, inline = False)
        embed.add_field(name = "B", value = option2, inline = False)

        pollmsg = await ctx.send(embed = embed)

        await pollmsg.add_reaction("🇦")
        await pollmsg.add_reaction("🇧")

    def uwufy(message):
        message = message.replace('L', 'W')
        message = message.replace('R', 'W')
        message = message.replace('l', 'w')
        message = message.replace('r', 'w')
        message = message.replace("no", "nyo")
        message = message.replace("mo", "myo")
        message = message.replace("No", "Nyo")
        message = message.replace("Mo", "Myo")
        message = message.replace("na", "nya")
        message = message.replace("ni", "nyi")
        message = message.replace("nu", "nyu")
        message = message.replace("ne", "nye")
        message = message.replace("anye", "ane")
        message = message.replace("inye", "ine")
        message = message.replace("onye", "one")
        message = message.replace("unye", "une")
        if message.endswith('.'):
            message = message[:-1]
            message+= ', uwu'
        elif message.endswith('?'):
            message = message[:-1]
            message+= ', uwu?'
        elif message.endswith('!'):
            message = message[:-1]
            message+= ', uwu, chibi-san!'
        else: message+= ' uwu'
        return message 

    @commands.command()
    async def uwu(ctx, *args):
        """Kawaii desu ne senpai uwu .｡･ﾟﾟ･(＞_＜)･ﾟﾟ･｡."""
        if(len(args) > 0):
            msgcontent = " ".join(args)
        else:
            msglist = []
            async for message in ctx.channel.history(limit=10):
                if(not message.content.startswith("$") and not message.content == ''):
                    msglist.append(message.content)
            print(msglist)
            msgcontent = msglist[0]
        await ctx.send(uwufy(msgcontent))

    @commands.command()
    async def hmm(ctx):
        """For when someone says something questionable."""
        hstring = "H"
        hmlength = random.randint(15, 25)
        for i in range(0, hmlength):
            flag = random.randint(0, 2)
            if flag:
                hstring += 'M'
            else:
                hstring += 'm'
        hstring += 'm'
        await ctx.send(hstring)   

def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the Miscellaneous cog on to the bot.
    """
    bot.add_cog(Misc(bot))
