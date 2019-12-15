import argparse
import logging
import sys
import pathlib


def get_argument_parser():
    parser = argparse.ArgumentParser(description='Parse the arguments that are passed to the bot.'
                                                 'Currently, progressing on the reddit bot')
    reddit_help = "Starts the bot on reddit"
    twitter_help = "Twitter bot shall be initialied with this, but is currently not implemented"
    version_help = "Prints the version of the language installer"
    parser.add_argument("--reddit",  help=reddit_help, action="store_true", required=False)
    parser.add_argument("--twitter",   help=twitter_help, action="store_true", required=False)
    parser.add_argument("--version", help=version_help, action="store_true", required=False)
    return parser


def get_logger():
    """Initialise _logger.

    This should only be called when run as main program to override the default
    _logger.
    """
    log_dir = pathlib.Path(__file__).parents[1] / "log_dir"
    if log_dir.exists() is False:
        log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger("numeca")

    c_handler = logging.StreamHandler(sys.stdout)
    f_handler = logging.FileHandler(log_dir / 'bot_logger.log')
    e_handler = logging.FileHandler(log_dir / 'bot_logger.err')

    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.DEBUG)
    e_handler.setLevel(logging.ERROR)

    # Create formatters and add it to handlers
    log_format = "%(levelname)s %(asctime)-15s %(threadName)s %(module)s %(lineno)i %(funcName)s \n%(message)s"
    formatter = logging.Formatter(log_format, None)

    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)
    e_handler.setFormatter(formatter)

    # Add handlers to the _logger
    _logger.addHandler(c_handler)
    _logger.addHandler(f_handler)
    _logger.addHandler(e_handler)
    _logger.propagate = False
    return _logger
