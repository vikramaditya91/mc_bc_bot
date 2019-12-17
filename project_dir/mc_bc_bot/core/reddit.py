import praw
import json
import cachetools
import pathlib
import logging
import asyncio
import random
from project_dir.mc_bc_bot.version import __loose_version__
from project_dir.mc_bc_bot.utils.general_utilities import get_content_directory

SUBREDDITS = ['EmergingCricket']
cache = cachetools.TTLCache(maxsize=100, ttl=3600)

logger = logging.getLogger(__name__)


def get_reddit_object():
    """Returns the praw's Reddit object taking the credentials from the praw.ini file"""
    logger.info("Logging into the bot with the Praw.ini credentials")
    return praw.Reddit('mc_bc_bot', user_agent='MCBCBOT (by /u/vikramaditya91)')



def get_valid_subreddits(reddit):
    """Returns the valid sub-reddits that the bot will be parsing through
    :param reddit The reddit object that was authenticated

    :return list of subreddit objects
    """
    subreddits = []
    for subreddit in SUBREDDITS:
        subreddits.append(reddit.subreddit(subreddit))
    return subreddits


async def ensure_not_child_of_bot_comment(comment):
    """This ensures that the bot is not replying to a thread whose parent is from the bot.
    Mainly to avoid spam"""
    bots_thread = True
    logger.info(f"Checking if the comment {comment.body} is a child of the mc_bc_bot comment")
    try:
        parent = comment.parent()
        if parent.author.name == "mc_bc_bot":
            bots_thread = False
        ensure_not_child_of_bot_comment(parent)
        return bots_thread
    except AttributeError as e:
        if "'Submission' object has no attribute 'parent'" in str(e):
            return
        raise


@cachetools.cached(cache)
def get_triggers_from_json():
    """Parse the json file which contains information about the triggers"""
    with open(get_content_directory() / "triggers.json", "r") as triggers:
        return json.load(triggers)


async def valid_comment(comment):
    """A valid comment should satisfy the following criteria
    1) Any of its parents should not have already been replied to by the mc_bc_bot
    2) The comment itself should not have been made by someone in the list"""
    if await ensure_not_child_of_bot_comment(comment) is True:
        if comment.author.name not in get_triggers_from_json()['undesirable']:
            return True
    return False


def get_all_sledges():
    """Parse the json file for a random sledge
    :return A dict of sledges"""
    with open(get_content_directory()/"sledges.json", "r") as sledge_file:
        return json.load(sledge_file)


def construct_comment():
    quote, [perp, victim, context] = random.choice(list(get_all_sledges().items()))
    logger.info(f"The following will be the reply {quote}")
    comment = quote.upper()
    comment += f"\n\n*{perp}* to *{victim}*"
    comment += f"\n\n{context}"
    comment += f"\n\n---"
    comment += f"^[source](https://github.com/vikramaditya91/mc_bc_bot) ^| ^v{__loose_version__}"
    return comment


def is_trigger_comment(comment):
    """Verifies if the comment is one of the bot triggers"""
    logging.info(f"Checking if {comment.body} is a trigger comment")
    return any(ele in comment.body for ele in get_triggers_from_json()['triggered_by'])


def reply_to_said_comment(comment):
    """Replies to the comment as it satisfied all the criteria"""
    comment_to_reply = construct_comment()
    comment.reply(comment_to_reply)
    logger.info(f"{comment.author}'s comment was replied to at {comment.permalink}")

