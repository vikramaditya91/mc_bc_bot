import praw
SUBREDDITS = ['EmergingCricket']

def get_reddit_object():
    """Returns the praw's Reddit object taking the credentials from the praw.ini file"""
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


def valid_comment(comment):
    """A valid comment should satisfy the following criteria
    1) Any of its parents should not have already been replied to by the mc_bc_bot
    2) The comment itself should not have been made by a """
    check_parent_is_not_this_bot
    a=1
    return True


