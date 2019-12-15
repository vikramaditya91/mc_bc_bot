import praw


def get_reddit_object():
    return praw.Reddit('mc_bc_bot', user_agent='MCBCBOT (by /u/vikramaditya91)')
