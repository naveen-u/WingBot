import re
from datetime import datetime

import discord
import feedparser
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands
from utils.configManager import XkcdConfig


class Xkcd(commands.Cog):
    """
    Retrieve and subscribe to xkcd comics.
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = XkcdConfig()
        self.botConfig = bot.config
        self.rss_collection = bot.db_client[self.botConfig.database][
            self.config.rss_collection
        ]
        rss_collection = self.rss_collection.find_one({})
        self.etag = rss_collection["etag"]
        self.modified = rss_collection["modified"]
        self.subscribers = rss_collection["subscribers"]
        self.latest = rss_collection["latest"]
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.check_for_new_comics, "cron", minute="0,30")
        scheduler.start()

    @commands.group(
        name="xkcd",
        invoke_without_command=True,
        case_insensitive=True,
    )
    async def xkcd(self, ctx, comicId=None):
        """
        Get an xkcd comic. If comic ID is not provided, the latest one is fetched.
        """
        await self.get(ctx, comicId)

    @xkcd.command(name="get")
    async def get(self, ctx, comicId=None):
        """
        Fetches an xkcd comic.
        """
        embed = await self.make_embed_for_comic(comicId)
        await ctx.send(embed=embed)

    async def make_embed_for_comic(self, comicId=None):
        if comicId is None:
            response = requests.get(self.config.current_comic)
        else:
            response = requests.get(self.config.nth_comic.replace("${n}", str(comicId)))
        if response.status_code != 200:
            raise requests.exceptions.RequestException()
        comic = response.json()
        embed = discord.Embed(
            title=f"#{comic['num']}: {comic['title']}",
            colour=discord.Colour.blue(),
            timestamp=datetime(
                int(comic["year"]), int(comic["month"]), int(comic["day"])
            ),
        )
        embed.set_image(url=comic["img"])
        embed.set_footer(text=comic["alt"])
        return embed

    @xkcd.command(name="subscribe", aliases=["sub", "s"])
    async def subscribe(self, ctx):
        """
        Subscribe the current channel to xkcd updates.
        """
        try:
            result = self.rss_collection.update_one(
                {}, {"$addToSet": {"subscribers": ctx.channel.id}}
            )
            if result.modified_count == 0:
                await ctx.send(
                    "I'm pretty sure you were already subscribed. No worries, I'll keep sending new xkcd comics here!"
                )
            else:
                await ctx.send("Alright, I'll start sharing new xkcd comics here!")
                self.subscribers.append(ctx.channel.id)
        except:
            await ctx.send("Ruh-roh! Something's wrong.")

    @xkcd.command(name="unsubscribe", aliases=["unsub", "u"])
    async def unsubscribe(self, ctx):
        """
        Unsubscribe the current channel to xkcd updates.
        """
        try:
            result = self.rss_collection.update_one(
                {}, {"$pull": {"subscribers": ctx.channel.id}}
            )
            if result.modified_count == 0:
                await ctx.send(
                    "I don't think you were subscribed in the first place. No worries, I won't be sending new xkcd comics here!"
                )
            else:
                await ctx.send("Alright, I'll stop sharing new xkcd comics here!")
                self.subscribers.remove(ctx.channel.id)
        except:
            await ctx.send("Ruh-roh! Something's wrong.")

    async def check_for_new_comics(self):
        """
        Check for new comics and send relevant updates to all subscribers.
        """
        rss_feed = feedparser.parse(
            self.config.rss_feed, etag=self.etag, modified=self.modified
        )
        if rss_feed.status == 200:
            latest_comic_id = int(
                re.search(r"https://xkcd.com/(\d+)", rss_feed.entries[0].id).group(1)
            )
            try:
                result = self.rss_collection.update_one(
                    {},
                    {
                        "$set": {
                            "etag": rss_feed.etag,
                            "modified": rss_feed.modified,
                            "latest": latest_comic_id,
                        }
                    },
                )
                if result.modified_count == 1:
                    self.etag = rss_feed.etag
                    self.modified = rss_feed.modified
            except Exception as e:
                print(e)
                return
            for comic_id in range(self.latest + 1, latest_comic_id + 1):
                embed = await self.make_embed_for_comic(comicId=comic_id)
                for subscriber in self.subscribers:
                    channel = self.bot.get_channel(subscriber)
                    await channel.send(embed=embed)
            self.latest = latest_comic_id


def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the Xkcd cog on to the bot.
    """
    bot.add_cog(Xkcd(bot))
