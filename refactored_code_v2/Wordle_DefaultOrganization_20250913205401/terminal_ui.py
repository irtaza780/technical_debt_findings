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
KEYBOARD_INDENT = 10
BANNER_CHAR = "="

logger = logging.getLogger(__name__)


def status_to_colors(status: str) -> Tuple[str, str]:
    """
    Map letter status to ANSI color codes.

    Args:
        status: One of CORRECT, PRESENT, or ABSENT status constants.

    Returns:
        Tuple of (foreground_code, background_code) ANSI escape sequences.
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
        ANSI-formatted string representing the colored tile.
    """
    fg, bg = status_to_colors(status)
    tile = f" {letter.upper()} "
    return f"{BOLD}{fg}{bg}{tile}{RESET}"


def _render_empty_tile() -> str:
    """
    Render a single empty tile for unfilled board positions.

    Returns:
        ANSI-formatted string representing an empty tile.
    """
    return f"{BOLD}{FG_BLACK}{BG_LIGHT}   {RESET}"


def render_row(guess: Optional[str], statuses: Optional[List[str]]) -> str:
    """
    Render a row of tiles for a guess or empty row.

    Args:
        guess: 5-letter word guess, or None for empty row.
        statuses: List of status strings for each letter, or None for empty row.

    Returns:
        ANSI-formatted string representing the complete row.
    """
    pieces = []
    if guess is None or statuses is None:
        # Render empty tiles for unfilled rows
        pieces = [_render_empty_tile() for _ in range(WORD_LENGTH)]
    else:
        # Render tiles with status colors for guessed words
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
        ANSI-formatted string representing the keyboard letter.
    """
    status = status_map.get(letter.lower(), None)
    if status is None:
        return f"{BOLD}{FG_BLACK}{BG_LIGHT} {letter} {RESET}"
    else:
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
        # Center keyboard rows based on row length
        indent = " " * (KEYBOARD_INDENT - len(row))
        print(indent + " ".join(line_parts))
    print()


def _print_banner(text: str) -> None:
    """
    Print a centered banner with decorative border.

    Args:
        text: Text to display in the banner.
    """
    border = BANNER_CHAR * len(text)
    print(border)
    print(text)
    print(border)


def _get_game_and_banner(date=None, random_word: bool = False) -> Tuple[WordleGame, str]:
    """
    Initialize game and create appropriate banner text.

    Args:
        date: Optional date for daily word selection.
        random_word: If True, use random word instead of daily word.

    Returns:
        Tuple of (WordleGame instance, banner text).
    """
    if random_word:
        secret = get_random_word()
        banner = "Wordle (Random word)"
    else:
        secret = get_daily_word(date=date)
        if date:
            banner = f"Wordle (Daily word for {date.isoformat()} UTC)"
        else:
            banner = "Wordle (Today's daily word)"

    game = WordleGame(secret_word=secret)
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
        Valid guess string, or None if input was invalid or closed.
    """
    prompt = f"Enter guess #{game.attempts_used + 1}: "
    try:
        guess = input(prompt).strip()
    except EOFError:
        logger.info("Input closed by user. Exiting game.")
        return None

    ok, msg = game.validate_guess(guess)
    if not ok:
        print(f"Invalid guess: {msg}\n")
        return None

    return guess


def _submit_and_display_guess(game: WordleGame, guess: str) -> bool:
    """
    Submit guess to game and display result.

    Args:
        game: Current WordleGame instance.
        guess: The guess to submit.

    Returns:
        True if guess was successfully submitted, False otherwise.
    """
    try:
        statuses = game.submit_guess(guess)
    except ValueError as e:
        logger.error(f"Error submitting guess: {e}")
        print(f"Error: {e}")
        return False

    print()
    # Print the latest row immediately for responsiveness
    print(render_row(guess.lower(), statuses))
    print()
    return True


def _print_win_message(game: WordleGame) -> None:
    """
    Print congratulations message and game summary for a win.

    Args:
        game: Completed WordleGame instance.
    """
    print_board(game.history, game.max_attempts)
    print_keyboard(game.get_keyboard_status())
    print(f"Congratulations! You guessed it in {game.attempts_used}/{game.max_attempts} attempts.")
    print(f"The word was: {game.secret.upper()}")


def _print_loss_message(game: WordleGame) -> None:
    """
    Print loss message and reveal the secret word.

    Args:
        game: Completed WordleGame instance.
    """
    print_board(game.history, game.max_attempts)
    print_keyboard(game.get_keyboard_status())
    print("Better luck next time!")
    print(f"The word was: {game.secret.upper()}")


def run_terminal_game(date=None, random_word: bool = False) -> None:
    """
    Orchestrate playing Wordle in the terminal.

    Handles game initialization, main game loop, user input, and end-game display.

    Args:
        date: Optional date for daily word selection.
        random_word: If True, use random word instead of daily word.
    """
    game, banner = _get_game_and_banner(date=date, random_word=random_word)

    _print_banner(banner)
    _print_game_instructions()

    while not game.is_over:
        print_board(game.history, game.max_attempts)
        print_keyboard(game.get_keyboard_status())

        guess = _handle_guess_input(game)
        if guess is None:
            return

        if not _submit_and_display_guess(game, guess):
            continue

        if game.is_won:
            _print_win_message(game)
            return

    # Game over without a win
    _print_loss_message(game)