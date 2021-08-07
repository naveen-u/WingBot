import discord


def is_nsfw_allowed(channel: discord.abc.Messageable) -> bool:
    """
    Checks if NSFW content is allowed in a channel.

    Args:
        channel (discord.abc.Messageable): The channel in question.

    Returns:
        bool: True if NSFW content is permissible, False otherwise.
    """
    return not hasattr(channel, "is_nsfw") or channel.is_nsfw()
