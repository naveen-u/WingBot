import random
import textwrap

import discord
import nabg
import requests
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from utils.configManager import BullshitConfig
from utils.log import log


class Bullshit(commands.Cog):
    """
    Create WhatsApp family group forwards based on Seb Pearce's New-Age Bullshit Generator.
    """

    def __init__(self, bot):
        self.config = BullshitConfig()
        self.bot = bot

    @commands.command(aliases=["shit"])
    async def bullshit(self, ctx):
        """
        Creates a new-age bullshit image.
        """
        await self.makePost(ctx)

    async def makePost(self, ctx):
        """
        Creates and sends the message.
        """
        image = Image.open(
            requests.get("http://placeimg.com/640/480/nature", stream=True).raw
        )
        draw = ImageDraw.Draw(image)

        fontsize = 1
        txt = nabg.ionize()
        # portion of image width you want text width to be
        img_fraction = 0.8

        message = await ctx.send("Opening photoshop...")
        font = ImageFont.truetype(self.config.font, fontsize)
        log(ctx.channel.id, "Finding optimum wrap")
        while (
            font.getsize_multiline(txt)[1] < 0.2 * font.getsize_multiline(txt)[0]
            and fontsize < 80
        ):
            fontsize += 1
            font = ImageFont.truetype(self.config.font, fontsize)
            w = (len(txt) * image.width) // font.getsize(txt)[0]
            txt = "\n".join(textwrap.wrap(txt, w))

        await message.edit(content="Making text boxes...")
        log(ctx.channel.id, "Finding optimum font size")
        while font.getsize_multiline(txt, spacing=10)[0] < img_fraction * image.size[0]:
            # iterate until the text size is just larger than the criteria
            fontsize += 1
            font = ImageFont.truetype(self.config.font, fontsize)

        await message.edit(content="Putting text on the template...")
        log(ctx.channel.id, "Fitting font")
        while font.getsize_multiline(txt, spacing=10)[0] > img_fraction * image.size[0]:
            fontsize -= 1
            font = ImageFont.truetype(self.config.font, fontsize)

        w, h = draw.multiline_textsize(txt, font, spacing=1)
        left = (image.width - w) * 0.5
        top = (image.height - h) * 0.2

        await message.edit(content="Rasterizing image...")
        draw.text(
            (left, top),
            txt,
            random.choice(["yellow", "orange", "red", "skyblue", "green"]),
            font=font,
            spacing=50,
            stroke_width=5,
            stroke_fill="black",
        )  # put the text on the image
        image.save("bullshit.png")
        await message.delete()
        await ctx.send(file=discord.File("bullshit.png"))


def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the Anagram cog on to the bot.
    """
    bot.add_cog(Bullshit(bot))
