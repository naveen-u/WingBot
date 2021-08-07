import os
import random
import sys
import traceback
import urllib

import asyncpraw
import discord
import urlextract
from discord.ext import commands
from utils.channelUtils import is_nsfw_allowed
from utils.configManager import BotConfig, RedditConfig
from utils.log import log


def credit_embed(post):
    """
    Returns a Discord embed with the post title, subreddit and link to the original post.
    """
    embed = discord.Embed(
        title=post.title,
        description="r/{0}".format(post.subreddit.display_name),
        url="https://www.reddit.com" + post.permalink,
    )
    return embed


async def get_subpost(sublist, is_sfw):
    """
    Picks a random post from a list of posts.
    """
    posts = []
    async for submission in sublist:
        if is_submission_valid(submission, is_sfw):
            posts.append(submission)
    post = random.choice(posts)
    return post


def is_submission_valid(submission, is_sfw):
    """
    Checks if a Reddit submission is valid.
    """
    return (
        not submission.stickied
        and len(submission.selftext) < 2000
        and not (is_sfw and submission.over_18)
    )


class Reddit(commands.Cog):
    """Pull posts from Reddit."""

    def __init__(self, bot):
        self.bot = bot

        self.bot_config = BotConfig()
        self.reddit_config = RedditConfig()

        self.reddit_instance = asyncpraw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_SECRET"),
            user_agent=self.reddit_config.user_agent,
        )

    async def check_and_post_reddit(self, message):
        """
        Checks if a Discord message has a valid Reddit URL, and if it does, post its contents into the channel.
        """
        channel = message.channel
        url = message.content

        extractor = urlextract.URLExtract()
        if not extractor.has_urls(url):
            return

        parse_result = urllib.parse.urlparse(url)
        if parse_result[1] != "www.reddit.com":
            return

        try:
            post = await self.reddit_instance.submission(url=url)
        except:
            log(
                channel.id,
                "INFO: This Reddit URL seems to be invalid. The link might not be prefixed with https://",
            )
            return

        if post.over_18 and not is_nsfw_allowed(channel):
            await channel.send("This isn't an NSFW channel you degenerate")
            return

        if post.is_self:
            await channel.send(post.selftext)
        else:
            await channel.send(post.url)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        await self.check_and_post_reddit(message)

    async def post(self, ctx, subname, should_check_top_posts):
        """
        Takes a subreddit name and sends a post from it in the channel.
        """
        try:
            subreddit = await self.reddit_instance.subreddit(subname)
            await subreddit.load()
        except:
            await ctx.send(
                "That didn't load. Check the subreddit name and try again.\nIf you're spelling it correctly, it's possible the subreddit you're trying to view is banned."
            )
            return

        is_channel_sfw = not is_nsfw_allowed(ctx.channel)

        if subreddit.over18 and is_channel_sfw:
            await ctx.send("Go run this in an NSFW channel you degenerate")
            return

        post = None

        if should_check_top_posts:
            post = await get_subpost(subreddit.top("day", limit=40), is_channel_sfw)
        else:
            post = await get_subpost(subreddit.hot(limit=40), is_channel_sfw)

        log(ctx.channel.id, post.url)

        await ctx.send(embed=credit_embed(post))
        if post.is_self:
            await ctx.send(post.selftext)
        else:
            await ctx.send(post.url)

    @commands.command(usage="<subreddit name>", aliases=["gettop"])
    async def top(self, ctx, subname: str):
        """Gets a random post from the daily top posts of a given subreddit."""
        await self.post(ctx, subname, True)

    @commands.command(usage="<subreddit name>", aliases=["gethot"])
    async def hot(self, ctx, subname: str):
        """Gets a random post from the daily hot posts of a given subreddit."""
        await self.post(ctx, subname, False)

    @commands.command(aliases=["randomcute", "cute", "aw", "awww"])
    async def aww(self, ctx):
        """Gets a random cute post."""
        awwlist = self.reddit_config.cute_subs
        await self.top(ctx, random.choice(awwlist))

    @commands.command(aliases=["funny"])
    async def meme(self, ctx):
        """Gets a random meme."""
        memelist = self.reddit_config.meme_subs
        await self.top(ctx, random.choice(memelist))

    @commands.command()
    async def copypasta(self, ctx):
        """To be fair, you have to have a very high IQ to use this command."""
        subreddit = await self.reddit_instance.subreddit("copypasta")
        post = await get_subpost(
            subreddit.hot(limit=40), not is_nsfw_allowed(ctx.channel)
        )
        await ctx.send("**{0}**".format(post.title))
        await ctx.send(post.selftext)

    async def signal_handler(self):
        """
        Called by bot when it recieves a SIGTERM or SIGINT. For cleanup activities before exiting.
        """
        print("Closing connection to reddit...")
        await self.reddit_instance.close()

    async def cog_command_error(self, ctx, error):
        """This is triggered when an error is raised while invoking a command in this cog.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, "on_error"):
            return

        ignored = (commands.CommandNotFound,)

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, "original", error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You forgot to give me input dumdum!")

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            log(f"Ignoring exception in command {ctx.command}: ")
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )


def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the Reddit cog on to the bot.
    """
    bot.add_cog(Reddit(bot))
