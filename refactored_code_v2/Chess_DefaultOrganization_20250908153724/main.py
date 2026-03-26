import logging
import sys
from typing import Optional

from board import Board
from san import parse_user_input, generate_san_for_move

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Game constants
GAME_TITLE = "ChatDev Chess - Terminal"
MOVE_INPUT_PROMPT = "move > "
HELP_TEXT = """Commands:
  moves    - list legal moves in current position
  board    - reprint the board
  help     - show this help
  quit     - exit the game
Examples: e4, Nf3, O-O, exd5, e8=Q, e2e4, g7g8q"""

QUIT_COMMANDS = ("q", "quit", "exit")
HELP_COMMANDS = ("h", "help", "?")
BOARD_COMMANDS = ("b", "board")
MOVES_COMMAND = "moves"

INVALID_MOVE_MESSAGE = "Invalid move. Type 'moves' to list legal moves or 'help' for help."
CHECKMATE_MESSAGE_TEMPLATE = "Checkmate! {winner} wins."
STALEMATE_MESSAGE = "Stalemate. Draw."
CHECK_MESSAGE = "Check."
PLAYED_MESSAGE_TEMPLATE = "Played {san}\n"
GOODBYE_MESSAGE = "Goodbye."
EXITING_MESSAGE = "\nExiting."


def display_welcome_message() -> None:
    """Display the welcome message and initial instructions."""
    logger.info(GAME_TITLE)
    logger.info("Enter moves in SAN (e4, Nf3, O-O, exd5, e8=Q) or coordinates (e2e4, g7g8q).")
    logger.info("Type 'help' for commands.\n")


def display_board(board: Board) -> None:
    """Display the current board state."""
    board.print_board()


def check_game_end_conditions(board: Board) -> bool:
    """
    Check for checkmate or stalemate conditions.
    
    Args:
        board: The current game board.
        
    Returns:
        True if the game has ended, False otherwise.
    """
    if board.is_checkmate():
        winner = "Black" if board.white_to_move else "White"
        logger.info(CHECKMATE_MESSAGE_TEMPLATE.format(winner=winner))
        return True
    
    if board.is_stalemate():
        logger.info(STALEMATE_MESSAGE)
        return True
    
    return False


def display_check_status(board: Board) -> None:
    """Display check status if the current player is in check."""
    if board.in_check(board.white_to_move):
        logger.info(CHECK_MESSAGE)


def get_player_input(board: Board) -> str:
    """
    Get and return the player's input.
    
    Args:
        board: The current game board.
        
    Returns:
        The player's input string, or empty string if interrupted.
        
    Raises:
        EOFError: When EOF is reached.
        KeyboardInterrupt: When user interrupts (Ctrl+C).
    """
    turn = "White" if board.white_to_move else "Black"
    return input(f"{turn} {MOVE_INPUT_PROMPT}").strip()


def handle_quit_command() -> bool:
    """
    Handle the quit command.
    
    Returns:
        True to indicate the game should exit.
    """
    logger.info(GOODBYE_MESSAGE)
    return True


def handle_help_command() -> None:
    """Display the help message."""
    logger.info(HELP_TEXT)


def handle_moves_command(board: Board) -> None:
    """
    Display all legal moves in the current position.
    
    Args:
        board: The current game board.
    """
    legal_moves = board.generate_legal_moves()
    sans = [generate_san_for_move(board, move, legal_moves) for move in legal_moves]
    sans.sort()
    logger.info("Legal moves:")
    logger.info(", ".join(sans))


def process_move_input(board: Board, user_input: str) -> bool:
    """
    Process a move input from the user.
    
    Args:
        board: The current game board.
        user_input: The raw user input string.
        
    Returns:
        True if the move was valid and executed, False otherwise.
    """
    move = parse_user_input(board, user_input)
    
    if move is None:
        logger.info(INVALID_MOVE_MESSAGE)
        return False
    
    san_str = generate_san_for_move(board, move)
    board.make_move(move)
    logger.info(PLAYED_MESSAGE_TEMPLATE.format(san=san_str))
    return True


def handle_user_command(board: Board, user_input: str) -> Optional[bool]:
    """
    Handle a user command or move input.
    
    Args:
        board: The current game board.
        user_input: The raw user input string.
        
    Returns:
        True if the game should exit, False if the turn should continue,
        or None if the input was a non-move command that doesn't affect turn flow.
    """
    command = user_input.lower()
    
    if command in QUIT_COMMANDS:
        return handle_quit_command()
    
    if command in HELP_COMMANDS:
        handle_help_command()
        return None
    
    if command in BOARD_COMMANDS:
        return None
    
    if command == MOVES_COMMAND:
        handle_moves_command(board)
        return None
    
    # Treat as a move attempt
    return process_move_input(board, user_input)


def run_game_loop(board: Board) -> None:
    """
    Run the main game loop.
    
    Args:
        board: The current game board.
    """
    while True:
        display_board(board)
        
        if check_game_end_conditions(board):
            break
        
        display_check_status(board)
        
        try:
            user_input = get_player_input(board)
        except (EOFError, KeyboardInterrupt):
            logger.info(EXITING_MESSAGE)
            break
        
        if not user_input:
            continue
        
        result = handle_user_command(board, user_input)
        
        # result is True: exit game
        # result is False: move was processed, continue to next turn
        # result is None: command was processed, stay on same turn
        if result is True:
            break
        elif result is False:
            continue


def main() -> int:
    """
    Main entry point for the chess game.
    
    Returns:
        Exit code (0 for success).
    """
    board = Board()
    board.setup_start_position()
    
    display_welcome_message()
    run_game_loop(board)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())