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

# Command constants
COMMAND_QUIT = {"q", "quit", "exit"}
COMMAND_HELP = {"h", "help", "?"}
COMMAND_BOARD = {"b", "board"}
COMMAND_MOVES = "moves"

# UI messages
WELCOME_MESSAGE = "ChatDev Chess - Terminal"
MOVE_INPUT_PROMPT = "Enter moves in SAN (e4, Nf3, O-O, exd5, e8=Q) or coordinates (e2e4, g7g8q)."
HELP_PROMPT = "Type 'help' for commands.\n"
INVALID_MOVE_MESSAGE = "Invalid move. Type 'moves' to list legal moves or 'help' for help."
GOODBYE_MESSAGE = "Goodbye."
EXITING_MESSAGE = "Exiting."
CHECK_MESSAGE = "Check."
CHECKMATE_MESSAGE = "Checkmate! {player} wins."
STALEMATE_MESSAGE = "Stalemate. Draw."
PLAYED_MESSAGE = "Played {san}\n"

HELP_TEXT = """Commands:
  moves    - list legal moves in current position
  board    - reprint the board
  help     - show this help
  quit     - exit the game
Examples: e4, Nf3, O-O, exd5, e8=Q, e2e4, g7g8q"""


def display_welcome() -> None:
    """Display welcome message and instructions."""
    logger.info(WELCOME_MESSAGE)
    logger.info(MOVE_INPUT_PROMPT)
    logger.info(HELP_PROMPT)


def display_help() -> None:
    """Display help text with available commands."""
    logger.info(HELP_TEXT)


def display_board(board: Board) -> None:
    """Display the current board state."""
    board.print_board()


def get_game_status_message(board: Board) -> Optional[str]:
    """
    Determine the current game status and return appropriate message.
    
    Args:
        board: The current game board state.
        
    Returns:
        Status message if game has ended, None otherwise.
    """
    if board.is_checkmate():
        winner = "Black" if board.white_to_move else "White"
        return CHECKMATE_MESSAGE.format(player=winner)
    
    if board.is_stalemate():
        return STALEMATE_MESSAGE
    
    if board.in_check(board.white_to_move):
        return CHECK_MESSAGE
    
    return None


def display_legal_moves(board: Board) -> None:
    """
    Generate and display all legal moves in SAN notation.
    
    Args:
        board: The current game board state.
    """
    legal_moves = board.generate_legal_moves()
    san_moves = [generate_san_for_move(board, move, legal_moves) for move in legal_moves]
    san_moves.sort()
    logger.info("Legal moves:")
    logger.info(", ".join(san_moves))


def get_player_input(board: Board) -> str:
    """
    Prompt the current player for input.
    
    Args:
        board: The current game board state.
        
    Returns:
        User input string (stripped of whitespace).
        
    Raises:
        EOFError: If EOF is encountered.
        KeyboardInterrupt: If user interrupts (Ctrl+C).
    """
    player = "White" if board.white_to_move else "Black"
    return input(f"{player} move > ").strip()


def process_move_input(board: Board, user_input: str) -> bool:
    """
    Parse and execute a move from user input.
    
    Args:
        board: The current game board state.
        user_input: Raw user input string.
        
    Returns:
        True if move was successfully executed, False otherwise.
    """
    move = parse_user_input(board, user_input)
    
    if move is None:
        logger.info(INVALID_MOVE_MESSAGE)
        return False
    
    san_notation = generate_san_for_move(board, move)
    board.make_move(move)
    logger.info(PLAYED_MESSAGE.format(san=san_notation))
    return True


def handle_user_command(board: Board, command: str) -> Optional[bool]:
    """
    Handle special commands (help, moves, board, quit).
    
    Args:
        board: The current game board state.
        command: Lowercase command string.
        
    Returns:
        False if user wants to quit, None if command was handled but game continues,
        True if input should be treated as a move attempt.
    """
    if command in COMMAND_QUIT:
        logger.info(GOODBYE_MESSAGE)
        return False
    
    if command in COMMAND_HELP:
        display_help()
        return None
    
    if command in COMMAND_BOARD:
        return None
    
    if command == COMMAND_MOVES:
        display_legal_moves(board)
        return None
    
    return True


def game_loop(board: Board) -> bool:
    """
    Main game loop handling player input and game state.
    
    Args:
        board: The current game board state.
        
    Returns:
        True if game ended normally, False if user quit.
    """
    while True:
        display_board(board)
        
        # Check game status
        status_message = get_game_status_message(board)
        if status_message:
            logger.info(status_message)
            return True
        
        # Get player input
        try:
            user_input = get_player_input(board)
        except (EOFError, KeyboardInterrupt):
            logger.info(EXITING_MESSAGE)
            return False
        
        if not user_input:
            continue
        
        # Process command or move
        command_result = handle_user_command(board, user_input.lower())
        
        if command_result is False:
            return False
        elif command_result is None:
            continue
        else:
            process_move_input(board, user_input)


def main() -> int:
    """
    Initialize and run the chess game.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        board = Board()
        board.setup_start_position()
        
        display_welcome()
        game_loop(board)
        
        return EXIT_SUCCESS
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())