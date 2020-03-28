def log(channel, *args):
    """
    Utility function to log statements with the channel ID at the beginning
    """
    print('Channel ' + str(channel) + ':\t' + ' '.join(map(str,args)))