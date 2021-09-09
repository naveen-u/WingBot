import discord
from discord.ext import commands
from utils.configManager import ValheimConfig


class Valheim(commands.Cog):
    """
    Commands for Valheim discord server management.
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = ValheimConfig()
        self.bot_config = bot.config
        self.server_state_collection = bot.db_client[self.bot_config.database][
            self.config.server_state_collection
        ]

    @commands.group(
        name="valheim",
        invoke_without_command=False,
        case_insensitive=True,
    )
    async def valheim(self, ctx):
        pass

    @valheim.command(name="up")
    async def up(self, ctx: commands.Context):
        """
        Sets Valheim server state to "Up" on the discord server.
        """
        send_embed = await self.set_server_state(ctx, True)
        if send_embed:
            embed = discord.Embed(
                title=f"{ctx.author.name} has fired up the server!",
                colour=discord.Colour.green(),
            )
            embed.set_author(
                name="Server is now UP ✅",
                icon_url="https://cdn.discordapp.com/avatars/"
                + str(ctx.author.id)
                + "/"
                + str(ctx.author.avatar)
                + ".png",
            )
            await ctx.send(embed=embed)
        await ctx.message.delete()

    @valheim.command(name="down")
    async def down(self, ctx: commands.Context):
        """
        Sets Valheim server state to "Down" on the discord server.
        """
        send_embed = await self.set_server_state(ctx, False)
        if send_embed:
            embed = discord.Embed(
                title=f"{ctx.author.name} has shut down the server!",
                colour=discord.Colour.red(),
            )
            embed.set_author(
                name="Server is now DOWN ❌",
                icon_url="https://cdn.discordapp.com/avatars/"
                + str(ctx.author.id)
                + "/"
                + str(ctx.author.avatar)
                + ".png",
            )
            await ctx.send(embed=embed)
        await ctx.message.delete()

    async def set_server_state(self, ctx: commands.Context, isUp: bool) -> bool:
        """
        Set's server state to the given state.

        Args:
            ctx (commands.Context): Command context.
            isUp (bool): True if server is up, false otherwise.

        Returns:
            bool: True if embed needs to be sent, false otherwise.
        """
        server_state_object = (
            self.server_state_collection.find_one({"serverId": ctx.guild.id}) or {}
        )
        channel_id = server_state_object.get("channelId")
        server_state = server_state_object.get("isUp")
        if channel_id is not None:
            if server_state is not None and server_state == isUp:
                return False
            old_channel = discord.utils.get(ctx.guild.channels, id=channel_id)
            await self.delete_server_state_channel(old_channel)
        channel = await self.create_server_state_channel(ctx, isUp)
        self.server_state_collection.update_one(
            {"serverId": ctx.guild.id},
            {"$set": {"serverId": ctx.guild.id, "channelId": channel.id, "isUp": isUp}},
            upsert=True,
        )
        return True

    async def create_server_state_channel(
        self, ctx: commands.Context, isUp: bool
    ) -> discord.VoiceChannel:
        """
        Create a private voice channel to display the server state on.

        Args:
            ctx (commands.Context): Command context.
            isUp (bool): True if server is up, false otherwise.

        Returns:
            discord.VoiceChannel: The channel object.
        """
        guild: discord.Guild = ctx.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                connect=False, manage_channels=False
            ),
            guild.me: discord.PermissionOverwrite(connect=True, manage_channels=True),
        }
        await self.bot.wait_until_ready()
        server_state = f"SERVER IS {'UP ✅' if isUp else 'DOWN ❌'}"
        channel = await guild.create_voice_channel(
            server_state, overwrites=overwrites, position=0
        )
        await self.bot.wait_until_ready()
        return channel

    async def delete_server_state_channel(self, channel: discord.VoiceChannel):
        """
        Deletes the given channel.

        Args:
            channel (discord.VoiceChannel): Channel to be deleted.
        """
        await channel.delete()


def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the Valheim cog on to the bot.
    """
    bot.add_cog(Valheim(bot))
