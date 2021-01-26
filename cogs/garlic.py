import textwrap

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from utils.configManager import BotConfig, GarlicConfig
from utils.log import log


class Garlic(commands.Cog):
    """
    Create posts for The Garlic.
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = GarlicConfig()
        self.botConfig = BotConfig()

    @commands.command(
        usage="[dark | light] <text to include in post>", aliases=["garlic"]
    )
    async def diygarlic(self, ctx, *, args: str):
        """
        Creates a garlic post with the given text. Dark mode or light mode can be specified. Defaults to light mode.
        """
        args = args.upper()
        words = args.split()
        if words[0] == "DARK":
            if not words[1:]:
                await ctx.send("You forgot to give me input dumdum!")
                return
            await self.makePost(ctx, self.config.darkTemplate, words[1:], "white")
        elif words[0] == "LIGHT":
            if not words[1:]:
                await ctx.send("You forgot to give me input dumdum!")
                return
            await self.makePost(ctx, self.config.template, words[1:], "black")
        else:
            await self.makePost(ctx, self.config.template, words, "black")

    async def makePost(self, ctx, imageFile, words, colour):
        """
        Creates and sends the garlic post.
        """
        image = Image.open(imageFile)
        draw = ImageDraw.Draw(image)

        fontsize = 1
        txt = " ".join(words)
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
        top = (image.height - h) * 0.4

        await message.edit(content="Rasterizing image...")
        draw.text(
            (left, top), txt, colour, font=font, spacing=50
        )  # put the text on the image
        image.save("diygarlic.png")
        await message.delete()
        await ctx.send(file=discord.File("diygarlic.png"))

    @diygarlic.error
    async def diygarlicError(self, ctx, error):
        """
        Error handler for the diygarlic command
        """
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send("You forgot to give me input dumdum!")
        else:
            log(ctx.channel.id, "Oopsie, exception: ", error)


def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the Anagram cog on to the bot.
    """
    bot.add_cog(Garlic(bot))
