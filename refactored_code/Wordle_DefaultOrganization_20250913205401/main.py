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


def parse_date(date_string):
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


def launch_game(date, random_word, use_gui):
    """
    Launch the Wordle game in the specified mode.
    
    Args:
        date (datetime.date or None): Specific date for daily word, or None for today.
        random_word (bool): Whether to use a random word instead of daily word.
        use_gui (bool): Whether to launch GUI mode instead of terminal mode.
    """
    if use_gui:
        # Import GUI lazily so terminal users don't need tkinter available.
        from gui import run_gui
        run_gui(date=date, random_word=random_word)
    else:
        run_terminal_game(date=date, random_word=random_word)


def main():
    """
    Main entry point for the Wordle game application.
    
    Parses command-line arguments and launches the game in the appropriate mode.
    """
    args = parse_args()
    date = parse_date(args.date)
    launch_game(date=date, random_word=args.random, use_gui=args.gui)


if __name__ == '__main__':
    main()