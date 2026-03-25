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
MOVE_SEPARATORS = ('-', ':', 'x', 'to', ' ')


def _get_piece_character(piece):
    """
    Convert a piece object to its display character.
    
    Args:
        piece: A piece object with 'color' and 'king' attributes.
        
    Returns:
        str: Character representation ('r', 'R', 'b', or 'B').
    """
    character = RED_PIECE if piece.color == 'red' else BLACK_PIECE
    return character.upper() if piece.king else character


def _get_square_background(row, col):
    """
    Determine the background character for a board square.
    
    Args:
        row (int): Row index (0-7).
        col (int): Column index (0-7).
        
    Returns:
        str: Background character ('.' for light, '_' for dark).
    """
    # Light squares have even sum of coordinates, dark squares have odd sum
    return LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE


def _print_board_ascii(board):
    """
    Render and display the board in ASCII format with coordinates.
    
    Displays rows from 8 to 1 (top to bottom) and columns a-h (left to right).
    
    Args:
        board: A board object with a get(row, col) method.
    """
    lines = []
    
    # Iterate through rows in reverse order (8 down to 1)
    for display_row, actual_row in enumerate(range(BOARD_RANKS - 1, -1, -1), start=1):
        row_characters = [str(BOARD_RANKS - (display_row - 1)) + " "]
        
        for col in range(BOARD_RANKS):
            piece = board.get(actual_row, col)
            background = _get_square_background(actual_row, col)
            
            if piece is None:
                row_characters.append(background)
            else:
                row_characters.append(_get_piece_character(piece))
        
        lines.append(" ".join(row_characters))
    
    # Add file labels at the bottom
    lines.append("  " + " ".join(list(BOARD_FILES)))
    logger.info("\n".join(lines))


def _print_cli_help():
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
    logger.info("\n".join(help_text))


def _get_current_player_name(current_player):
    """
    Get the display name for the current player.
    
    Args:
        current_player (str): Player identifier ('red' or 'black').
        
    Returns:
        str: Capitalized player name.
    """
    return 'Red' if current_player == 'red' else 'Black'


def _handle_game_over(state, board):
    """
    Handle game over state and prompt for replay.
    
    Args:
        state: GameState object.
        board: Board object.
        
    Returns:
        bool: True if user wants to play again, False otherwise.
    """
    is_over, winner, reason = state.is_game_over()
    
    if not is_over:
        return True
    
    if winner:
        logger.info(f"Game over: {winner.capitalize()} wins! ({reason})")
    else:
        logger.info(f"Game over: Draw. ({reason})")
    
    # Prompt user for replay
    while True:
        response = input("Play again? [y/N]: ").strip().lower()
        if response in PLAY_AGAIN_YES:
            return True
        else:
            logger.info("Goodbye.")
            return False


def _process_move_input(text, state, board):
    """
    Process and execute a move from user input.
    
    Args:
        text (str): Raw move input from user.
        state: GameState object.
        board: Board object.
        
    Returns:
        bool: True if game should continue, False if should exit.
    """
    from move_parser import MoveParser, MoveParseError
    
    try:
        move_sequence = MoveParser.parse(text)
    except MoveParseError as error:
        logger.info(f"Parse error: {error}")
        return True
    
    move_successful, message = state.try_move(move_sequence)
    
    if move_successful:
        _print_board_ascii(board)
        should_continue = _handle_game_over(state, board)
        
        if should_continue:
            next_player = _get_current_player_name(state.current_player)
            logger.info(f"Move accepted. {next_player} to move.")
        
        return should_continue
    else:
        logger.info(message or "Illegal move.")
        return True


def _handle_user_command(command, state, board):
    """
    Handle special user commands (help, restart, quit).
    
    Args:
        command (str): Lowercased user command.
        state: GameState object.
        board: Board object.
        
    Returns:
        tuple: (should_continue: bool, state: GameState, board: Board)
    """
    from board import Board
    from rules import GameState
    
    if command in HELP_COMMANDS:
        _print_cli_help()
        return True, state, board
    
    if command in RESTART_COMMANDS:
        new_board = Board()
        new_state = GameState(new_board)
        logger.info("New game started. Red to move.")
        _print_board_ascii(new_board)
        return True, new_state, new_board
    
    if command in QUIT_COMMANDS:
        logger.info("Goodbye.")
        return False, state, board
    
    return True, state, board


def run_cli():
    """
    Run the checkers game in CLI (command-line interface) mode.
    
    This mode is used when Pygame is not available. Players enter moves
    using algebraic notation (e.g., b6-c5 or c3:e5:g7).
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

    while True:
        current_player_name = _get_current_player_name(state.current_player)
        
        try:
            user_input = input(f"[{current_player_name}] move> ").strip()
        except (EOFError, KeyboardInterrupt):
            logger.info("\nExiting. Goodbye.")
            break
        
        if not user_input:
            continue
        
        lowercased_input = user_input.lower()
        
        # Handle special commands
        should_continue, state, board = _handle_user_command(
            lowercased_input, state, board
        )
        
        if not should_continue:
            break
        
        # Skip if it was a command
        if lowercased_input in (HELP_COMMANDS + QUIT_COMMANDS + RESTART_COMMANDS):
            continue
        
        # Process move input
        should_continue = _process_move_input(user_input, state, board)
        
        if not should_continue:
            break


def main():
    """
    Main entry point for the Checkers application.
    
    Attempts to start the Pygame GUI. If Pygame is not available or cannot
    be initialized (e.g., in headless environments), falls back to CLI mode.
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
        logger.info("Pygame not available. Falling back to CLI mode.")
    except Exception as error:
        logger.warning(f"Failed to initialize Pygame: {error}. Falling back to CLI mode.")

    run_cli()


if __name__ == "__main__":
    main()