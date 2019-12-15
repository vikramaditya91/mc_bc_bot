import asyncio
import time
from project_dir.mc_bc_bot.utils.general_utilities import get_logger, get_argument_parser
from project_dir.mc_bc_bot.core.reddit import get_reddit_object
from project_dir.mc_bc_bot.version import __version__
import sys
import praw

async def count():
    print("One")
    await asyncio.sleep(1)
    print("Two")


async def main(reddit=None, twitter=None, version=None):
    if reddit is True:
        reddit = get_reddit_object()

        subreddit = reddit.subreddit('CricketShitpost')
        for submission in subreddit.stream.submissions():
            comment_queue = submission.comments[:]  # Seed with top-level
            while comment_queue:
                comment = comment_queue.pop(0)
                print(comment.body)

        await asyncio.gather(count(), count(), count())

    if twitter is True:
        NotImplementedError

    if version is True:
        logger.info(__version__)
        print(__version__)

if __name__ == "__main__":
    import time
    s = time.perf_counter()


    # Configure the logger ONLY if used as a CLI tool (iso as module)
    logger = get_logger()

    # Configure the argument parser ONLY in case of CLI
    argument_parser = get_argument_parser()
    # Parse only arguments from 1 (strip the 0 which is the script name)
    arguments = argument_parser.parse_args(sys.argv[1:])

    # Call the main with explicit arguments
    asyncio.run(    main(
        reddit=arguments.reddit,
        twitter=arguments.twitter,
        version=arguments.version
    ))
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")


