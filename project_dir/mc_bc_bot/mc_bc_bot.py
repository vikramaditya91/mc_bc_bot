import asyncio
from project_dir.mc_bc_bot.utils.general_utilities import get_argument_parser, init_logger
from project_dir.mc_bc_bot.core.reddit import get_reddit_object, valid_comment,\
                                              SUBREDDITS, is_trigger_comment, reply_to_said_comment
from project_dir.mc_bc_bot.version import __version__
import sys
import praw
import logging


logger = logging.getLogger(__name__)


async def main(reddit=None, twitter=None, version=None, verbose=None):
    if verbose is True:
        logger = init_logger(verbose=True)
    if reddit is True:
        skip_existing=True
        reddit_object = get_reddit_object()
        required_subreddits = reddit_object.subreddit("+".join(SUBREDDITS))
        for comment in required_subreddits.stream.comments(skip_existing=skip_existing):
            if is_trigger_comment(comment) is True:
                if await valid_comment(comment) is True:
                    logger.info(f"The following comment will be replied to {comment.body}")
                    await reply_to_said_comment(comment)

    if twitter is True:
        NotImplementedError

    if version is True:
        logger.info(__version__)
        print(__version__)

if __name__ == "__main__":
    import time
    s = time.perf_counter()

    # Configure the argument parser ONLY in case of CLI
    argument_parser = get_argument_parser()
    # Parse only arguments from 1 (strip the 0 which is the script name)
    arguments = argument_parser.parse_args(sys.argv[1:])

    # Call the main with explicit arguments
    asyncio.run(    main(
        reddit=arguments.reddit,
        twitter=arguments.twitter,
        version=arguments.version,
        verbose=arguments.verbose
    ))
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")


