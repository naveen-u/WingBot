import os
import random

import discord
import praw
import urlextract
import urllib
from discord.ext import commands
from utils.configManager import BotConfig, RedditConfig


class RedditAuto(commands.Cog):
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
            print("INFO: This Reddit URL seems to be invalid. Maybe check if the link isn't prefixed with https?")
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


def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the RedditAuto cog on to the bot.
    """
    bot.add_cog(RedditAuto(bot))
