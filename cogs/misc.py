import discord
from discord.ext import commands
from utils.configManager import BotConfig, RedditConfig


class Misc(commands.Cog):
    """Miscellaneous commands."""

    def __init__(self, bot):
        self.bot = bot
        self.bot_config = BotConfig()

    @commands.command(
        usage='"<question>" "<option1>" "<option2>" (the quotation marks are important)'
    )
    async def poll(self, ctx, question: str, option1: str, option2: str):
        """Make polls."""

        commandmsg = await ctx.channel.fetch_message(ctx.channel.last_message_id)
        await commandmsg.delete()

        embed = discord.Embed(title=question, color=discord.Color.from_rgb(230, 0, 0))

        embed.add_field(name="A", value=option1, inline=False)
        embed.add_field(name="B", value=option2, inline=False)

        pollmsg = await ctx.send(embed=embed)

        await pollmsg.add_reaction("🇦")
        await pollmsg.add_reaction("🇧")


def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the Miscellaneous cog on to the bot.
    """
    bot.add_cog(Misc(bot))
