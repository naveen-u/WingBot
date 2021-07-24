import random
from re import sub

import discord

def credit_embed(post):
    embed = discord.Embed(
        title=post.title,
        description="r/{0}".format(post.subreddit.display_name),
        url="https://www.reddit.com" + post.permalink,
    )
    return embed

async def get_subpost(sublist, is_sfw):
    posts = []
    async for submission in sublist:
        if is_submission_valid(submission, is_sfw):
            posts.append(submission)
    post = random.choice(posts)
    return post

def is_submission_valid(submission, is_sfw):
    return not submission.stickied and len(submission.selftext) < 2000 and not (is_sfw and submission.over_18) 
