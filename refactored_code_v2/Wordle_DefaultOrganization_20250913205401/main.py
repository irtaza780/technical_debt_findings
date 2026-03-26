import argparse
import logging
from datetime import datetime

from terminal_ui import run_terminal_game

# Configuration constants
DATE_FORMAT = "%Y-%m-%d"
LOGGER = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def parse_arguments() -> argparse.Namespace:
    """
    Parse and return command-line arguments for the Wordle game.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments containing:
            - date: Optional date string in YYYY-MM-DD format
            - random: Boolean flag to use random word
            - gui: Boolean flag to launch GUI mode
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


def parse_date_argument(date_string: str) -> datetime.date | None:
    """
    Parse a date string in YYYY-MM-DD format to a date object.
    
    Args:
        date_string: Date string to parse in YYYY-MM-DD format.
    
    Returns:
        datetime.date object if parsing succeeds, None otherwise.
        Logs a warning and returns None if the format is invalid.
    """
    if not date_string:
        return None
    
    try:
        return datetime.strptime(date_string, DATE_FORMAT).date()
    except ValueError:
        LOGGER.warning(
            "Invalid date format '%s'. Expected YYYY-MM-DD. Falling back to today.",
            date_string
        )
        return None


def launch_gui_mode(date: datetime.date | None, use_random: bool) -> None:
    """
    Launch the Wordle GUI application.
    
    Imports the GUI module lazily to avoid requiring tkinter for terminal users.
    
    Args:
        date: Optional date object for the daily word.
        use_random: Boolean flag to use a random word instead of daily word.
    """
    try:
        from gui import run_gui
        run_gui(date=date, random_word=use_random)
    except ImportError as e:
        LOGGER.error(
            "Failed to import GUI module. Ensure tkinter is installed: %s",
            e
        )
        raise


def launch_terminal_mode(date: datetime.date | None, use_random: bool) -> None:
    """
    Launch the Wordle terminal game.
    
    Args:
        date: Optional date object for the daily word.
        use_random: Boolean flag to use a random word instead of daily word.
    """
    run_terminal_game(date=date, random_word=use_random)


def main() -> None:
    """
    Main entry point for the Wordle game application.
    
    Parses command-line arguments and launches either the GUI or terminal mode
    based on user preferences. Handles date parsing and mode selection.
    """
    args = parse_arguments()
    
    # Parse the date argument if provided
    parsed_date = parse_date_argument(args.date)
    
    # Launch appropriate game mode
    if args.gui:
        launch_gui_mode(date=parsed_date, use_random=args.random)
    else:
        launch_terminal_mode(date=parsed_date, use_random=args.random)


if __name__ == '__main__':
    main()