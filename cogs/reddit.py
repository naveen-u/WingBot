import os
import random

import discord
import praw
import urlextract
import urllib
from discord.ext import commands
from utils.configManager import BotConfig, RedditConfig


class Reddit(commands.Cog):
    """Pull posts from Reddit."""

    def __init__(self, bot):
        self.bot = bot

        self.bot_config = BotConfig()
        self.reddit_config = RedditConfig()

        self.reddit_instance = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_SECRET"),
            user_agent=self.reddit_config.user_agent,
        )

    async def check_and_post_reddit(self, message):
        channel = message.channel
        url = message.content

        extractor = urlextract.URLExtract()
        if not extractor.has_urls(url):
            return

        parse_result = urllib.parse.urlparse(url)
        if parse_result[1] != "www.reddit.com":
            return

        try:
            post = self.reddit_instance.submission(url=url)
        except:
            print("INFO: This Reddit URL seems to be invalid. The link might not be prefixed with https://")
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

    def getsubpost(self, sublist):
        posts = []
        for submission in sublist:
            if not submission.stickied:
                posts.append(submission)
        post = random.choice(posts)
        return post

    def getsubpost_sfw(self, sublist):
        posts = []
        for submission in sublist:
            if not submission.stickied and not submission.over_18:
                if len(submission.selftext) < 2000:
                    posts.append(submission)
        post = random.choice(posts)
        return post

    def credits(self, post):
        embed = discord.Embed(
            title=post.title,
            description="r/{0}".format(post.subreddit.display_name),
            url="https://www.reddit.com" + post.permalink,
        )
        return embed

    async def post(self, ctx, subname, true_if_top):
        try:
            subreddit = self.reddit_instance.subreddit(subname)
        except:
            await ctx.send("That didn't load. Check the subreddit name and try again.")
            return

        try:
            if subreddit.over18 and not ctx.channel.is_nsfw():
                await ctx.send("Go run this in an NSFW channel you degenerate")
                return
        except:
            await ctx.send(
                "That didn't work. It's possible the subreddit you're trying to view is banned."
            )
            return

        post = None

        if true_if_top:
            post = self.getsubpost(subreddit.top("day", limit=40))
        else:
            post = self.getsubpost(subreddit.hot(limit=40))

        print(post.url)
        await ctx.send(embed=self.credits(post))
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
        subreddit = self.reddit_instance.subreddit("copypasta")
        post = self.getsubpost_sfw(subreddit.hot(limit=40))
        await ctx.send("**{0}**".format(post.title))
        await ctx.send(post.selftext)

def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the Reddit cog on to the bot.
    """
    bot.add_cog(Reddit(bot))
