import argparse
import logging
from datetime import datetime

from terminal_ui import run_terminal_game

# Configuration constants
DATE_FORMAT = "%Y-%m-%d"
LOG_FORMAT = "%(levelname)s: %(message)s"

# Initialize logging
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse and return command-line arguments for the Wordle game.
    
    Returns:
        argparse.Namespace: Parsed arguments containing date, random, and gui flags.
    """
    parser = argparse.ArgumentParser(
        description="Play Wordle in your terminal (or optional GUI)."
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Play the word for a specific date (UTC), format YYYY-MM-DD.'
    )
    parser.add_argument(
        '--random',
        action='store_true',
        help='Use a random word instead of the daily word.'
    )
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Launch the GUI instead of terminal mode.'
    )
    return parser.parse_args()


def parse_date_argument(date_string):
    """
    Parse a date string in YYYY-MM-DD format.
    
    Args:
        date_string (str): Date string to parse.
    
    Returns:
        datetime.date or None: Parsed date object, or None if parsing fails.
    """
    if not date_string:
        return None
    
    try:
        return datetime.strptime(date_string, DATE_FORMAT).date()
    except ValueError:
        logger.warning(
            "Invalid date format '%s'. Use YYYY-MM-DD. Falling back to today.",
            date_string
        )
        return None


def launch_gui(date, random_word):
    """
    Launch the GUI mode for Wordle.
    
    Imports GUI module lazily to avoid requiring tkinter for terminal users.
    
    Args:
        date (datetime.date or None): Specific date for the daily word, or None for today.
        random_word (bool): Whether to use a random word instead of the daily word.
    """
    try:
        from gui import run_gui
        run_gui(date=date, random_word=random_word)
    except ImportError as e:
        logger.error(
            "GUI mode requires tkinter. Please install it or use terminal mode. %s",
            str(e)
        )


def launch_terminal(date, random_word):
    """
    Launch the terminal mode for Wordle.
    
    Args:
        date (datetime.date or None): Specific date for the daily word, or None for today.
        random_word (bool): Whether to use a random word instead of the daily word.
    """
    run_terminal_game(date=date, random_word=random_word)


def main():
    """
    Main entry point for the Wordle game.
    
    Parses command-line arguments and launches either GUI or terminal mode.
    """
    args = parse_args()
    
    # Parse and validate the date argument
    date = parse_date_argument(args.date)
    
    # Launch the appropriate game mode
    if args.gui:
        launch_gui(date=date, random_word=args.random)
    else:
        launch_terminal(date=date, random_word=args.random)


if __name__ == '__main__':
    main()