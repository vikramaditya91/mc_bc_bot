import argparse
import logging
import sys
import pathlib
import cachetools
from logging.handlers import RotatingFileHandler

cache = cachetools.TTLCache(maxsize=100, ttl=3600)


def get_argument_parser():
    parser = argparse.ArgumentParser(description='Parse the arguments that are passed to the bot.'
                                                 'Currently, progressing on the reddit bot')
    reddit_help = "Starts the bot on reddit"
    twitter_help = "Twitter bot shall be initialied with this, but is currently not implemented"
    version_help = "Prints the version of the language installer"
    parser.add_argument("--reddit",  help=reddit_help, action="store_true", required=False)
    parser.add_argument("--twitter",   help=twitter_help, action="store_true", required=False)
    parser.add_argument("--version", help=version_help, action="store_true", required=False)
    parser.add_argument("--verbose", action="store_true", required=False)
    return parser


def init_logger(fname='mc_bc_bot.log', level=logging.INFO, verbose=False):
    """ Init logger file where all output can be logged and classified

    :param fname: name of the log file
    :param level: level of the logger (?)
    :param verbose: True if print the logs on the screen
    :return:
        logger, the logger to use to print message on screen
    """
    log_folder = pathlib.Path(__file__).parents[1] / "log_dir"
    if log_folder.exists() is False:
        log_folder.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(level=level)
    logger = logging.getLogger("numeca")
    for handler in logger.handlers:
        logger.removeHandler(handler)

    handler = RotatingFileHandler(log_folder / fname, maxBytes=131072, backupCount=3)

    log_format = "%(levelname)s %(asctime)-15s %(threadName)s %(module)s %(lineno)i %(funcName)s %(message)s"
    formatter = logging.Formatter(log_format, None)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if verbose:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        stdout_handler.setLevel(level)
        logger.addHandler(stdout_handler)

    # Prevent call forwarding to root logger
    logger.propagate = False
    return logger


def get_content_directory():
    """Returns the directory which contains all the content json files"""
    return pathlib.Path(__file__).parents[1] / "content"
