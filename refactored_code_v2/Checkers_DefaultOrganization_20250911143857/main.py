import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BOARD_FILES = "abcdefgh"
BOARD_RANKS = 8
LIGHT_SQUARE = '.'
DARK_SQUARE = '_'
RED_PIECE = 'r'
BLACK_PIECE = 'b'
KING_PIECE_UPPER = True
HELP_COMMANDS = ("help", "h", "?")
QUIT_COMMANDS = ("quit", "exit", "q")
RESTART_COMMANDS = ("restart", "r")
PLAY_AGAIN_YES = ("y", "yes")
MOVE_SEPARATOR_CHARS = ('-', ':', 'x')
MOVE_SEPARATOR_WORDS = ('to',)


def _get_square_background(row: int, col: int) -> str:
    """
    Determine the background character for a board square.
    
    Args:
        row: Row index (0-7)
        col: Column index (0-7)
    
    Returns:
        Background character ('.' for light, '_' for dark)
    """
    return LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE


def _get_piece_character(piece) -> str:
    """
    Convert a piece object to its display character.
    
    Args:
        piece: Piece object with color and king attributes
    
    Returns:
        Character representation ('r', 'R', 'b', or 'B')
    """
    piece_char = RED_PIECE if piece.color == 'red' else BLACK_PIECE
    return piece_char.upper() if piece.king else piece_char


def _build_board_row(board, row_index: int, display_rank: int) -> str:
    """
    Build a single row string for ASCII board display.
    
    Args:
        board: Board object with get(row, col) method
        row_index: Internal row index (0-7)
        display_rank: Display rank number (1-8)
    
    Returns:
        Formatted row string with rank number and pieces
    """
    row_str = [str(display_rank) + " "]
    for col in range(BOARD_RANKS):
        piece = board.get(row_index, col)
        background = _get_square_background(row_index, col)
        
        if piece is None:
            row_str.append(background)
        else:
            row_str.append(_get_piece_character(piece))
    
    return " ".join(row_str)


def _print_board_ascii(board) -> None:
    """
    Render and display the board in ASCII format with coordinates.
    
    Displays rows 8..1 (top to bottom) and columns a..h (left to right).
    Light squares shown as '.', dark squares as '_'.
    Pieces shown as r/R (red), b/B (black), uppercase for kings.
    
    Args:
        board: Board object with get(row, col) method
    """
    lines = []
    
    # Build board rows from top (rank 8) to bottom (rank 1)
    for display_index, row_index in enumerate(range(BOARD_RANKS - 1, -1, -1), start=1):
        display_rank = BOARD_RANKS - (display_index - 1)
        row_str = _build_board_row(board, row_index, display_rank)
        lines.append(row_str)
    
    # Add file labels at bottom
    lines.append("  " + " ".join(list(BOARD_FILES)))
    logger.info("\n" + "\n".join(lines))


def _print_cli_help() -> None:
    """Display help information for CLI commands."""
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
    Get display name for current player.
    
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
    over, winner, reason = state.is_game_over()
    
    if not over:
        return True
    
    if winner:
        logger.info(f"Game over: {winner.capitalize()} wins! ({reason})")
    else:
        logger.info(f"Game over: Draw. ({reason})")
    
    # Prompt for replay
    while True:
        try:
            answer = input("Play again? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            logger.info("\nGoodbye.")
            return False
        
        if answer in PLAY_AGAIN_YES:
            return True
        else:
            logger.info("Goodbye.")
            return False


def _process_move_input(state, board, text: str) -> bool:
    """
    Process and execute a move from user input.
    
    Args:
        state: GameState object
        board: Board object
        text: Raw move input string
    
    Returns:
        True if move was successful, False otherwise
    """
    from move_parser import MoveParser, MoveParseError
    
    try:
        move_sequence = MoveParser.parse(text)
    except MoveParseError as error:
        logger.info(f"Parse error: {error}")
        return False
    
    move_successful, message = state.try_move(move_sequence)
    
    if move_successful:
        _print_board_ascii(board)
        
        if not _handle_game_over(state):
            return False
        
        next_player = _get_current_player_name(state.current_player)
        logger.info(f"Move accepted. {next_player} to move.")
    else:
        logger.info(message or "Illegal move.")
    
    return True


def _handle_cli_command(command: str, board, state) -> tuple[bool, bool]:
    """
    Handle special CLI commands (help, restart, quit).
    
    Args:
        command: Lowercased command string
        board: Board object (may be modified)
        state: GameState object (may be modified)
    
    Returns:
        Tuple of (should_continue, game_restarted)
    """
    if command in QUIT_COMMANDS:
        logger.info("Goodbye.")
        return False, False
    
    if command in HELP_COMMANDS:
        _print_cli_help()
        return True, False
    
    if command in RESTART_COMMANDS:
        from board import Board
        from rules import GameState
        
        board.__dict__.update(Board().__dict__)
        state.__dict__.update(GameState(board).__dict__)
        logger.info("New game started. Red to move.")
        _print_board_ascii(board)
        return True, True
    
    return True, False


def _run_cli_game_loop(board, state) -> None:
    """
    Main game loop for CLI mode.
    
    Args:
        board: Board object
        state: GameState object
    """
    while True:
        current_player = _get_current_player_name(state.current_player)
        
        try:
            user_input = input(f"[{current_player}] move> ").strip()
        except (EOFError, KeyboardInterrupt):
            logger.info("\nExiting. Goodbye.")
            break
        
        if not user_input:
            continue
        
        command = user_input.lower()
        should_continue, _ = _handle_cli_command(command, board, state)
        
        if not should_continue:
            break
        
        if command not in QUIT_COMMANDS + HELP_COMMANDS + RESTART_COMMANDS:
            if not _process_move_input(state, board, user_input):
                break


def run_cli() -> None:
    """
    Run the game in CLI (terminal) mode.
    
    This is used when Pygame is not available. Allows playing by typing
    moves in notation (e.g., b6-c5 or c3:e5:g7).
    """
    from board import Board
    from rules import GameState
    
    board = Board()
    state = GameState(board)
    
    logger.info("Checkers (Draughts) - CLI mode (Pygame not available)")
    logger.info("Red moves first. Forced captures are enforced.")
    _print_cli_help()
    _print_board_ascii(board)
    
    # Exit gracefully in non-interactive environments
    if not sys.stdin.isatty():
        logger.info("Non-interactive environment detected. Exiting CLI mode successfully.")
        return
    
    _run_cli_game_loop(board, state)


def main() -> None:
    """
    Main entry point for the Checkers application.
    
    Attempts to start the Pygame GUI. If Pygame is not installed or cannot
    be initialized (e.g., in headless test environments), falls back to
    lightweight CLI mode.
    """
    try:
        import pygame  # type: ignore
        from app import GameApp
        
        pygame.init()
        try:
            app = GameApp()
            app.run()
        finally:
            pygame.quit()
        return
    except ImportError:
        logger.debug("Pygame not available, falling back to CLI mode")
    except Exception as error:
        logger.debug(f"Pygame initialization failed: {error}, falling back to CLI mode")
    
    run_cli()


if __name__ == "__main__":
    main()