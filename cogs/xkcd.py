import re
from datetime import datetime

import discord
import feedparser
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands
from textwrap import wrap
from utils.configManager import XkcdConfig

ERROR_MESSAGE = "Ruh-roh! Something's wrong."


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
        try:
            comicId = int(comicId)
        except:
            comicId = None
        async with ctx.typing():
            try:
                embed = await self.make_embed_for_comic(comicId)
            except requests.exceptions.RequestException:
                await ctx.send(
                    f"{ERROR_MESSAGE} Are you sure that comic number is valid?"
                )
                return
        await ctx.reply(embed=embed)

    async def make_embed_for_comic(self, comicId=None):
        """
        Create an embed for the comic with the given ID.

        Args:
            comicId (int, optional): ID of the comic to be fetched. Defaults to the most recent.

        Raises:
            requests.exceptions.RequestException: If something goes wrong with the API call

        Returns:
            discord.Embed: The embed with the comic and description
        """
        if comicId is None:
            response = requests.get(self.config.current_comic)
        else:
            response = requests.get(self.config.nth_comic.replace("${n}", str(comicId)))
        if response.status_code != 200:
            raise requests.exceptions.RequestException()
        comic = response.json()
        timestamp = datetime(
            year=int(comic["year"]), month=int(comic["month"]), day=int(comic["day"])
        )
        embed = discord.Embed(
            title=f"#{comic['num']}: {comic['title']}",
            colour=discord.Colour.blue(),
            description=f":calendar_spiral: {timestamp.strftime('%d %B, %Y')}",
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
                await ctx.reply(
                    "I'm pretty sure you were already subscribed. No worries, I'll keep sending new xkcd comics here!"
                )
            else:
                await ctx.reply("Alright, I'll start sharing new xkcd comics here!")
                self.subscribers.append(ctx.channel.id)
        except:
            await ctx.reply(ERROR_MESSAGE)

    @xkcd.command(name="unsubscribe", aliases=["unsub", "u"])
    async def unsubscribe(self, ctx):
        """
        Unsubscribe the current channel from xkcd updates.
        """
        try:
            result = self.rss_collection.update_one(
                {}, {"$pull": {"subscribers": ctx.channel.id}}
            )
            if result.modified_count == 0:
                await ctx.reply(
                    "I don't think you were subscribed in the first place. No worries, I won't be sending new xkcd comics here!"
                )
            else:
                await ctx.reply("Alright, I'll stop sharing new xkcd comics here!")
                self.subscribers.remove(ctx.channel.id)
        except:
            await ctx.reply(ERROR_MESSAGE)

    @xkcd.command(name="explain")
    async def explain(self, ctx, comicId):
        """
        Fetches the explanation of a comic from explainxkcd.
        """
        async with ctx.typing():
            response = requests.get(
                self.config.explain_url_redirect.replace("${n}", str(comicId))
            )
            if response.status_code != 200:
                await ctx.reply("Ruh-roh! I couldn't find an explanation for that.")
            response_text = response.json()["parse"]["text"]["*"]
            title = re.search(r'href="/wiki/index.php/([^"]+)"', response_text).group(1)
            response = requests.get(
                self.config.explain_url.replace("${title}", str(title))
            )
            if response.status_code != 200:
                await ctx.reply("Ruh-roh! I couldn't find an explanation for that.")
            explanation = self.parse_explanation(
                response.json()["parse"]["wikitext"]["*"]
            )
            lines = explanation.split("\n")
            url = self.config.explain_page_url.replace("${title}", str(title))
            parts = []
            for line in lines:
                parts.extend(wrap(line, 2000))
            await ctx.reply(url)
            for part in parts:
                await ctx.send(part)

    def parse_explanation(self, text):
        """
        Parse wikitext into plain text/discord markdown.

        Args:
            text (str): Wikitext from the explainxkcd wiki

        Returns:
            str: parsed wikitext
        """
        substitution_patterns = [
            # wikipedia links
            (r"\{\{w\|([^|}]+)\}\}", r"\1"),
            # wikipedia links with custom text
            (r"\{\{w\|([^|}]+)\|([^}]+)\}\}", r"\2"),
            # wiki links with custom text
            (r"\[\[([^\|\]]+)\|([^\]]+)\]\]", r"\2"),
            # wiki links
            (r"\[\[([^\]]+)\]\]", r"\1"),
            # formatting commands
            (r"\{\{[^\}]+\}\}", ""),
            # links
            (r"\[[^\s]+\s([^\]]+)\]", r"\1"),
            # bullets
            (r"\*(\S)", r"• \1"),
            # bold + italic
            (r"'''''([^']+)'''''", r"***\1***"),
            # bold
            (r"'''([^']+)'''", r"**\1**"),
            # italics
            (r"''([^']+)''", r"*\1*"),
            # remove comments
            (r"<!--(.*?)-->", r""),
            # heading
            (r"==[^=]+==", ""),
        ]
        for substitution_pattern in substitution_patterns:
            find, replace = substitution_pattern
            text = re.sub(find, replace, text, flags=re.MULTILINE)
        return text

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
                    if channel is None:
                        try:
                            channel = await self.bot.fetch_channel(subscriber)
                        except Exception as e:
                            print(e)
                    await channel.send(embed=embed)
            self.latest = latest_comic_id


def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the Xkcd cog on to the bot.
    """
    bot.add_cog(Xkcd(bot))
