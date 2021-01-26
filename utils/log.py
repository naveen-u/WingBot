def log(channelId, *args):
    """
    Utility function to log statements with the channel ID at the beginning
    """
    print("Channel " + str(channelId) + ":\t" + " ".join(map(str, args)))
