import logging
from typing import List, Tuple, Dict, Optional

from game import WordleGame, ABSENT, PRESENT, CORRECT
from words import get_daily_word, get_random_word

# ANSI escape codes for coloring tiles
RESET = "\033[0m"
BOLD = "\033[1m"
FG_BLACK = "\033[30m"
FG_WHITE = "\033[97m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_GREY = "\033[100m"
BG_LIGHT = "\033[47m"

QWERTY_ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
WORD_LENGTH = 5
MAX_KEYBOARD_ROW_LENGTH = 10
KEYBOARD_INDENT_FACTOR = 10
BANNER_SEPARATOR_CHAR = "="

logger = logging.getLogger(__name__)


def status_to_colors(status: str) -> Tuple[str, str]:
    """
    Map letter status to ANSI color codes.

    Args:
        status: One of CORRECT, PRESENT, or ABSENT status constants.

    Returns:
        Tuple of (foreground_color, background_color) ANSI codes.
    """
    if status == CORRECT:
        return (FG_BLACK, BG_GREEN)
    elif status == PRESENT:
        return (FG_BLACK, BG_YELLOW)
    else:
        return (FG_WHITE, BG_GREY)


def colorize_letter(letter: str, status: str) -> str:
    """
    Render a single letter as an ANSI-colored tile.

    Args:
        letter: Single character to colorize.
        status: Status constant determining tile color.

    Returns:
        ANSI-formatted colored tile string.
    """
    fg, bg = status_to_colors(status)
    tile = f" {letter.upper()} "
    return f"{BOLD}{fg}{bg}{tile}{RESET}"


def _render_empty_tile() -> str:
    """
    Render a single empty tile for unfilled guess positions.

    Returns:
        ANSI-formatted empty tile string.
    """
    return f"{BOLD}{FG_BLACK}{BG_LIGHT}   {RESET}"


def render_row(guess: Optional[str], statuses: Optional[List[str]]) -> str:
    """
    Render a complete row of tiles for a guess.

    Args:
        guess: 5-letter word guess, or None for empty row.
        statuses: List of status values for each letter, or None for empty row.

    Returns:
        Space-separated string of colored tiles.
    """
    pieces = []
    if guess is None or statuses is None:
        # Render empty tiles for unfilled rows
        pieces = [_render_empty_tile() for _ in range(WORD_LENGTH)]
    else:
        # Render tiles with status colors
        for i in range(WORD_LENGTH):
            ch = guess[i].upper()
            st = statuses[i]
            pieces.append(colorize_letter(ch, st))
    return " ".join(pieces)


def print_board(history: List[Tuple[str, List[str]]], max_attempts: int) -> None:
    """
    Print the full game board with history and remaining empty rows.

    Args:
        history: List of (guess, statuses) tuples from previous attempts.
        max_attempts: Total number of allowed attempts.
    """
    for guess, statuses in history:
        print(render_row(guess, statuses))
    for _ in range(max_attempts - len(history)):
        print(render_row(None, None))


def _render_keyboard_letter(letter: str, status_map: Dict[str, str]) -> str:
    """
    Render a single letter for the keyboard display.

    Args:
        letter: Single character to render.
        status_map: Dictionary mapping letters to their best-known status.

    Returns:
        ANSI-formatted letter tile.
    """
    status = status_map.get(letter.lower(), None)
    if status is None:
        return f"{BOLD}{FG_BLACK}{BG_LIGHT} {letter} {RESET}"
    return colorize_letter(letter, status)


def print_keyboard(status_map: Dict[str, str]) -> None:
    """
    Print a QWERTY keyboard with letter colors reflecting game state.

    Args:
        status_map: Dictionary mapping letters to their best-known status.
    """
    print()
    for row in QWERTY_ROWS:
        line_parts = [_render_keyboard_letter(ch, status_map) for ch in row]
        # Center keyboard rows based on longest row
        indent = " " * (KEYBOARD_INDENT_FACTOR - len(row))
        print(indent + " ".join(line_parts))
    print()


def _print_game_banner(banner_text: str) -> None:
    """
    Print a centered banner with separator lines.

    Args:
        banner_text: Text to display in the banner.
    """
    separator = BANNER_SEPARATOR_CHAR * len(banner_text)
    print(separator)
    print(banner_text)
    print(separator)


def _initialize_game(date=None, random_word: bool = False) -> Tuple[WordleGame, str]:
    """
    Initialize a Wordle game with appropriate word source.

    Args:
        date: Optional date for daily word selection.
        random_word: If True, use random word; otherwise use daily word.

    Returns:
        Tuple of (WordleGame instance, banner text).
    """
    if random_word:
        secret = get_random_word()
        game = WordleGame(secret_word=secret)
        banner = "Wordle (Random word)"
    else:
        secret = get_daily_word(date=date)
        game = WordleGame(secret_word=secret)
        if date:
            banner = f"Wordle (Daily word for {date.isoformat()} UTC)"
        else:
            banner = "Wordle (Today's daily word)"
    return game, banner


def _print_game_instructions() -> None:
    """Print game instructions and rules to the player."""
    print("Guess the 5-letter word in 6 tries.")
    print("Feedback: green = correct spot, yellow = wrong spot, grey = not in word.")
    print()


def _handle_guess_input(game: WordleGame) -> Optional[str]:
    """
    Prompt player for a guess and validate it.

    Args:
        game: Current WordleGame instance.

    Returns:
        Valid guess string, or None if input was closed or invalid.
    """
    prompt = f"Enter guess #{game.attempts_used + 1}: "
    try:
        guess = input(prompt).strip()
    except EOFError:
        logger.info("Input closed by user")
        print("\nInput closed. Exiting game.")
        return None

    is_valid, validation_msg = game.validate_guess(guess)
    if not is_valid:
        print(f"Invalid guess: {validation_msg}\n")
        return None

    try:
        statuses = game.submit_guess(guess)
        return guess
    except ValueError as e:
        logger.error(f"Error submitting guess: {e}")
        print(f"Error: {e}")
        return None


def _print_win_message(game: WordleGame) -> None:
    """
    Print congratulations message and reveal the word.

    Args:
        game: Completed WordleGame instance.
    """
    print_board(game.history, game.max_attempts)
    print_keyboard(game.get_keyboard_status())
    print(f"Congratulations! You guessed it in {game.attempts_used}/{game.max_attempts} attempts.")
    print(f"The word was: {game.secret.upper()}")


def _print_loss_message(game: WordleGame) -> None:
    """
    Print loss message and reveal the word.

    Args:
        game: Completed WordleGame instance.
    """
    print_board(game.history, game.max_attempts)
    print_keyboard(game.get_keyboard_status())
    print("Better luck next time!")
    print(f"The word was: {game.secret.upper()}")


def run_terminal_game(date=None, random_word: bool = False) -> None:
    """
    Orchestrate a complete Wordle game session in the terminal.

    Args:
        date: Optional date for daily word selection.
        random_word: If True, use random word; otherwise use daily word.
    """
    game, banner = _initialize_game(date=date, random_word=random_word)

    _print_game_banner(banner)
    _print_game_instructions()

    while not game.is_over:
        print_board(game.history, game.max_attempts)
        print_keyboard(game.get_keyboard_status())

        guess = _handle_guess_input(game)
        if guess is None:
            return

        statuses = game.get_keyboard_status()
        print()
        print(render_row(guess.lower(), statuses))
        print()

        if game.is_won:
            _print_win_message(game)
            return

    _print_loss_message(game)