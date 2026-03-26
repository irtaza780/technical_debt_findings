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

# Game state constants
EXIT_SUCCESS = 0
EXIT_FAILURE = 1

# Command aliases
QUIT_COMMANDS = {"q", "quit", "exit"}
HELP_COMMANDS = {"h", "help", "?"}
BOARD_COMMANDS = {"b", "board"}
MOVES_COMMAND = "moves"

# UI messages
WELCOME_MESSAGE = "ChatDev Chess - Terminal"
MOVE_INPUT_HINT = "Enter moves in SAN (e4, Nf3, O-O, exd5, e8=Q) or coordinates (e2e4, g7g8q)."
TYPE_HELP_MESSAGE = "Type 'help' for commands.\n"
INVALID_MOVE_MESSAGE = "Invalid move. Type 'moves' to list legal moves or 'help' for help."
CHECK_MESSAGE = "Check."
CHECKMATE_MESSAGE = "Checkmate! {winner} wins."
STALEMATE_MESSAGE = "Stalemate. Draw."
GOODBYE_MESSAGE = "Goodbye."
EXITING_MESSAGE = "\nExiting."
MOVE_PLAYED_MESSAGE = "Played {san}\n"

HELP_TEXT = """Commands:
  moves    - list legal moves in current position
  board    - reprint the board
  help     - show this help
  quit     - exit the game
Examples: e4, Nf3, O-O, exd5, e8=Q, e2e4, g7g8q"""

LEGAL_MOVES_HEADER = "Legal moves:"


def display_welcome() -> None:
    """Display welcome message and instructions."""
    logger.info(WELCOME_MESSAGE)
    logger.info(MOVE_INPUT_HINT)
    logger.info(TYPE_HELP_MESSAGE)


def display_help() -> None:
    """Display help text with available commands and examples."""
    logger.info(HELP_TEXT)


def display_board(board: Board) -> None:
    """Display the current board state."""
    board.print_board()


def check_game_end_conditions(board: Board) -> Optional[int]:
    """
    Check for checkmate, stalemate, or check conditions.
    
    Args:
        board: The current game board state.
        
    Returns:
        EXIT_SUCCESS if game has ended, None if game continues.
    """
    if board.is_checkmate():
        winner = "Black" if board.white_to_move else "White"
        logger.info(CHECKMATE_MESSAGE.format(winner=winner))
        return EXIT_SUCCESS
    
    if board.is_stalemate():
        logger.info(STALEMATE_MESSAGE)
        return EXIT_SUCCESS
    
    if board.in_check(board.white_to_move):
        logger.info(CHECK_MESSAGE)
    
    return None


def get_player_input(board: Board) -> str:
    """
    Prompt the current player for input.
    
    Args:
        board: The current game board state.
        
    Returns:
        The user's input string, stripped of whitespace.
        
    Raises:
        EOFError: If EOF is encountered.
        KeyboardInterrupt: If user interrupts (Ctrl+C).
    """
    turn = "White" if board.white_to_move else "Black"
    return input(f"{turn} move > ").strip()


def handle_quit_command() -> int:
    """
    Handle quit/exit command.
    
    Returns:
        EXIT_SUCCESS to signal game termination.
    """
    logger.info(GOODBYE_MESSAGE)
    return EXIT_SUCCESS


def handle_moves_command(board: Board) -> None:
    """
    Display all legal moves in Standard Algebraic Notation.
    
    Args:
        board: The current game board state.
    """
    legal_moves = board.generate_legal_moves()
    sans = [generate_san_for_move(board, move, legal_moves) for move in legal_moves]
    sans.sort()
    logger.info(LEGAL_MOVES_HEADER)
    logger.info(", ".join(sans))


def process_move_input(board: Board, user_input: str) -> bool:
    """
    Parse and execute a move from user input.
    
    Args:
        board: The current game board state.
        user_input: The raw user input string.
        
    Returns:
        True if move was successfully executed, False if invalid.
    """
    move = parse_user_input(board, user_input)
    
    if move is None:
        logger.info(INVALID_MOVE_MESSAGE)
        return False
    
    san_str = generate_san_for_move(board, move)
    board.make_move(move)
    logger.info(MOVE_PLAYED_MESSAGE.format(san=san_str))
    return True


def process_user_command(board: Board, user_input: str) -> Optional[int]:
    """
    Process user commands and moves.
    
    Args:
        board: The current game board state.
        user_input: The raw user input string.
        
    Returns:
        EXIT_SUCCESS if game should end, None if game continues.
    """
    if not user_input:
        return None
    
    command = user_input.lower()
    
    if command in QUIT_COMMANDS:
        return handle_quit_command()
    
    if command in HELP_COMMANDS:
        display_help()
        return None
    
    if command in BOARD_COMMANDS:
        display_board(board)
        return None
    
    if command == MOVES_COMMAND:
        handle_moves_command(board)
        return None
    
    # Treat input as a move
    process_move_input(board, user_input)
    return None


def run_game_loop(board: Board) -> int:
    """
    Execute the main game loop.
    
    Args:
        board: The initialized game board.
        
    Returns:
        EXIT_SUCCESS on normal completion, EXIT_FAILURE on error.
    """
    while True:
        display_board(board)
        
        # Check for game-ending conditions
        end_result = check_game_end_conditions(board)
        if end_result is not None:
            return end_result
        
        # Get player input
        try:
            user_input = get_player_input(board)
        except (EOFError, KeyboardInterrupt):
            logger.info(EXITING_MESSAGE)
            return EXIT_SUCCESS
        
        # Process command or move
        end_result = process_user_command(board, user_input)
        if end_result is not None:
            return end_result
    
    return EXIT_SUCCESS


def main() -> int:
    """
    Initialize and run the chess game.
    
    Returns:
        EXIT_SUCCESS on successful completion, EXIT_FAILURE on error.
    """
    try:
        board = Board()
        board.setup_start_position()
        
        display_welcome()
        
        return run_game_loop(board)
    
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())