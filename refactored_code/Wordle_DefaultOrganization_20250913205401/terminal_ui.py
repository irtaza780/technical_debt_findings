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
MAX_KEYBOARD_ROW_INDENT = 10
BANNER_SEPARATOR = "="

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
        # Render all letters in the row
        line_parts = [_render_keyboard_letter(ch, status_map) for ch in row]
        # Center the row slightly
        indent = " " * (MAX_KEYBOARD_ROW_INDENT - len(row))
        print(indent + " ".join(line_parts))
    print()


def _print_game_banner(banner_text: str) -> None:
    """
    Print a centered banner with separator lines.

    Args:
        banner_text: Text to display in the banner.
    """
    separator = BANNER_SEPARATOR * len(banner_text)
    print(separator)
    print(banner_text)
    print(separator)


def _print_game_instructions() -> None:
    """Print game instructions and rules to the player."""
    print("Guess the 5-letter word in 6 tries.")
    print("Feedback: green = correct spot, yellow = wrong spot, grey = not in word.")
    print()


def _get_secret_word(date=None, random_word: bool = False) -> str:
    """
    Retrieve the secret word for the game.

    Args:
        date: Optional date for daily word mode.
        random_word: If True, use a random word instead of daily word.

    Returns:
        The secret word to guess.
    """
    if random_word:
        return get_random_word()
    return get_daily_word(date=date)


def _get_game_banner(date=None, random_word: bool = False) -> str:
    """
    Generate the banner text for the game.

    Args:
        date: Optional date for daily word mode.
        random_word: If True, indicate random word mode.

    Returns:
        Banner text string.
    """
    if random_word:
        return "Wordle (Random word)"
    if date:
        return f"Wordle (Daily word for {date.isoformat()} UTC)"
    return "Wordle (Today's daily word)"


def _handle_guess_input(game: WordleGame, attempt_number: int) -> Optional[List[str]]:
    """
    Get and validate a guess from the player, then submit it.

    Args:
        game: The WordleGame instance.
        attempt_number: Current attempt number (1-indexed).

    Returns:
        List of statuses if successful, None if input was invalid or closed.
    """
    prompt = f"Enter guess #{attempt_number}: "
    try:
        guess = input(prompt).strip()
    except EOFError:
        print("\nInput closed. Exiting game.")
        return None

    # Validate the guess format and dictionary
    is_valid, validation_message = game.validate_guess(guess)
    if not is_valid:
        print(f"Invalid guess: {validation_message}\n")
        return None

    # Submit the guess and get status feedback
    try:
        statuses = game.submit_guess(guess)
        return statuses
    except ValueError as error:
        logger.error(f"Error submitting guess: {error}")
        print(f"Error: {error}")
        return None


def _print_game_state(game: WordleGame) -> None:
    """
    Print the current board and keyboard state.

    Args:
        game: The WordleGame instance.
    """
    print_board(game.history, game.max_attempts)
    print_keyboard(game.get_keyboard_status())


def _print_win_message(game: WordleGame) -> None:
    """
    Print the victory message.

    Args:
        game: The WordleGame instance.
    """
    _print_game_state(game)
    print(f"Congratulations! You guessed it in {game.attempts_used}/{game.max_attempts} attempts.")
    print(f"The word was: {game.secret.upper()}")


def _print_loss_message(game: WordleGame) -> None:
    """
    Print the loss message.

    Args:
        game: The WordleGame instance.
    """
    _print_game_state(game)
    print("Better luck next time!")
    print(f"The word was: {game.secret.upper()}")


def run_terminal_game(date=None, random_word: bool = False) -> None:
    """
    Orchestrate a complete Wordle game session in the terminal.

    Args:
        date: Optional date for daily word mode.
        random_word: If True, play with a random word instead of daily word.
    """
    # Initialize game
    secret = _get_secret_word(date=date, random_word=random_word)
    game = WordleGame(secret_word=secret)
    banner = _get_game_banner(date=date, random_word=random_word)

    # Display game header
    _print_game_banner(banner)
    _print_game_instructions()

    # Main game loop
    while not game.is_over:
        _print_game_state(game)
        attempt_number = game.attempts_used + 1
        statuses = _handle_guess_input(game, attempt_number)

        if statuses is None:
            # Input was invalid or closed
            continue

        print()
        # Print the latest row immediately for responsiveness
        print(render_row(game.history[-1][0].lower(), statuses))
        print()

        if game.is_won:
            _print_win_message(game)
            return

    # Game over without a win
    _print_loss_message(game)