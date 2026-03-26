import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Board display constants
BOARD_SIZE = 8
LIGHT_SQUARE = '.'
DARK_SQUARE = '_'
RED_PIECE = 'r'
BLACK_PIECE = 'b'
KING_SUFFIX = 'K'
FILE_LABELS = "abcdefgh"

# Game messages
GAME_TITLE = "Checkers (Draughts) - CLI mode (Pygame not available)"
GAME_START_MESSAGE = "Red moves first. Forced captures are enforced."
NON_INTERACTIVE_MESSAGE = "Non-interactive environment detected. Exiting CLI mode successfully."
GOODBYE_MESSAGE = "Goodbye."
PARSE_ERROR_MESSAGE = "Parse error: {}"
ILLEGAL_MOVE_MESSAGE = "Illegal move."
MOVE_ACCEPTED_MESSAGE = "Move accepted. {} to move."
GAME_OVER_MESSAGE = "Game over: {} ({})."
GAME_OVER_DRAW_MESSAGE = "Game over: Draw. ({})."
NEW_GAME_MESSAGE = "New game started. Red to move."
PLAY_AGAIN_PROMPT = "Play again? [y/N]: "
MOVE_PROMPT = "[{}] move> "

# Command constants
QUIT_COMMANDS = ("quit", "exit", "q")
HELP_COMMANDS = ("help", "h", "?")
RESTART_COMMANDS = ("restart", "r")
PLAY_AGAIN_YES = ("y", "yes")


def _get_square_background(row: int, col: int) -> str:
    """
    Determine the background character for a board square.
    
    Args:
        row: Row index (0-7)
        col: Column index (0-7)
    
    Returns:
        Background character for light or dark square
    """
    return LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE


def _get_piece_character(piece) -> str:
    """
    Convert a piece object to its display character.
    
    Args:
        piece: Piece object with color and king attributes
    
    Returns:
        Character representation of the piece
    """
    piece_char = RED_PIECE if piece.color == 'red' else BLACK_PIECE
    return piece_char.upper() if piece.king else piece_char


def _print_board_ascii(board) -> None:
    """
    Render the board in ASCII with coordinates.
    
    Displays rows 8..1 (top to bottom) and columns a..h (left to right).
    Light squares shown as '.', dark squares as '_'.
    Red pieces as 'r'/'R', black pieces as 'b'/'B' (uppercase for kings).
    
    Args:
        board: Board object with get(row, col) method
    """
    lines = []
    
    # Iterate through rows from top (8) to bottom (1)
    for row_display, row_index in enumerate(range(BOARD_SIZE - 1, -1, -1), start=1):
        row_str = [str(BOARD_SIZE - (row_display - 1)) + " "]
        
        for col_index in range(BOARD_SIZE):
            piece = board.get(row_index, col_index)
            background = _get_square_background(row_index, col_index)
            
            if piece is None:
                row_str.append(background)
            else:
                row_str.append(_get_piece_character(piece))
        
        lines.append(" ".join(row_str))
    
    # Add file labels at the bottom
    lines.append("  " + " ".join(list(FILE_LABELS)))
    logger.info("\n".join(lines))


def _print_cli_help() -> None:
    """
    Display help information for CLI commands and move notation.
    """
    help_text = [
        "Commands:",
        "- Enter moves using coordinates a-h for files and 1-8 for ranks.",
        "- Examples:",
        "    b6-c5         (simple move)",
        "    c3:e5:g7      (multiple captures)",
        "- Separators '-', ':', 'x', 'to' and spaces are accepted.",
        "- Type 'help' to show this help, 'restart' to start a new game, 'quit' to exit."
    ]
    for line in help_text:
        logger.info(line)


def _get_current_player_name(current_player: str) -> str:
    """
    Convert player identifier to display name.
    
    Args:
        current_player: Player identifier ('red' or 'black')
    
    Returns:
        Capitalized player name
    """
    return 'Red' if current_player == 'red' else 'Black'


def _handle_game_over(state) -> bool:
    """
    Handle game over state and prompt for replay.
    
    Args:
        state: GameState object
    
    Returns:
        True if user wants to play again, False otherwise
    """
    is_over, winner, reason = state.is_game_over()
    
    if not is_over:
        return True
    
    if winner:
        logger.info(GAME_OVER_MESSAGE.format(winner.capitalize() + " wins!", reason))
    else:
        logger.info(GAME_OVER_DRAW_MESSAGE.format(reason))
    
    while True:
        answer = input(PLAY_AGAIN_PROMPT).strip().lower()
        if answer in PLAY_AGAIN_YES:
            return True
        else:
            logger.info(GOODBYE_MESSAGE)
            return False


def _initialize_new_game():
    """
    Create a new game with fresh board and game state.
    
    Returns:
        Tuple of (Board, GameState) objects
    """
    from board import Board
    from rules import GameState
    
    board = Board()
    state = GameState(board)
    return board, state


def _process_user_command(text: str, board, state) -> tuple:
    """
    Process special user commands (help, restart, quit).
    
    Args:
        text: User input text
        board: Current board object
        state: Current game state object
    
    Returns:
        Tuple of (should_continue, new_board, new_state)
        should_continue: False if user wants to quit
        new_board: Updated board (same or new)
        new_state: Updated state (same or new)
    """
    low = text.lower()
    
    if low in QUIT_COMMANDS:
        logger.info(GOODBYE_MESSAGE)
        return False, board, state
    
    if low in HELP_COMMANDS:
        _print_cli_help()
        return True, board, state
    
    if low in RESTART_COMMANDS:
        board, state = _initialize_new_game()
        logger.info(NEW_GAME_MESSAGE)
        _print_board_ascii(board)
        return True, board, state
    
    return None, board, state  # Not a special command


def _process_move(text: str, board, state) -> bool:
    """
    Parse and execute a move command.
    
    Args:
        text: Move notation string
        board: Current board object
        state: Current game state object
    
    Returns:
        True if move was successful, False otherwise
    """
    from move_parser import MoveParser, MoveParseError
    
    try:
        move_sequence = MoveParser.parse(text)
    except MoveParseError as error:
        logger.info(PARSE_ERROR_MESSAGE.format(error))
        return False
    
    move_successful, message = state.try_move(move_sequence)
    
    if move_successful:
        _print_board_ascii(board)
        next_player = _get_current_player_name(state.current_player)
        logger.info(MOVE_ACCEPTED_MESSAGE.format(next_player))
        return True
    else:
        logger.info(message or ILLEGAL_MOVE_MESSAGE)
        return False


def _run_game_loop(board, state) -> None:
    """
    Main game loop for CLI mode.
    
    Handles user input, move processing, and game state updates.
    
    Args:
        board: Board object
        state: GameState object
    """
    while True:
        current_player = _get_current_player_name(state.current_player)
        
        try:
            user_input = input(MOVE_PROMPT.format(current_player)).strip()
        except (EOFError, KeyboardInterrupt):
            logger.info("\nExiting. " + GOODBYE_MESSAGE)
            break
        
        if not user_input:
            continue
        
        # Check for special commands
        should_continue, board, state = _process_user_command(user_input, board, state)
        if should_continue is False:
            break
        if should_continue is True:
            continue
        
        # Process move
        if _process_move(user_input, board, state):
            # Check if game is over
            if not _handle_game_over(state):
                break
            # Reinitialize for new game if user chose to play again
            board, state = _initialize_new_game()
            logger.info(NEW_GAME_MESSAGE)
            _print_board_ascii(board)


def run_cli() -> None:
    """
    Run the CLI (terminal) mode of the Checkers game.
    
    Initializes the game and starts the main game loop.
    Falls back gracefully in non-interactive environments.
    """
    board, state = _initialize_new_game()
    
    logger.info(GAME_TITLE)
    logger.info(GAME_START_MESSAGE)
    _print_cli_help()
    _print_board_ascii(board)
    
    # Exit gracefully in non-interactive environments
    if not sys.stdin.isatty():
        logger.info(NON_INTERACTIVE_MESSAGE)
        return
    
    _run_game_loop(board, state)


def _initialize_pygame_app():
    """
    Attempt to initialize and run the Pygame GUI application.
    
    Returns:
        True if Pygame app ran successfully, False if initialization failed
    """
    try:
        import pygame
        from app import GameApp
        
        pygame.init()
        try:
            app = GameApp()
            app.run()
            return True
        finally:
            pygame.quit()
    except ImportError:
        return False
    except Exception as error:
        logger.debug(f"Pygame initialization failed: {error}")
        return False


def main() -> None:
    """
    Main entry point for the Checkers application.
    
    Attempts to start the Pygame GUI. If Pygame is not available or
    initialization fails, falls back to CLI mode.
    """
    if _initialize_pygame_app():
        return
    
    run_cli()


if __name__ == "__main__":
    main()