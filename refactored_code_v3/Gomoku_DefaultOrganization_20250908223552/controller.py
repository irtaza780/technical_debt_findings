import logging
from typing import Optional, List, Tuple

# Support both package and flat-file imports
try:
    from .model import Board
except ImportError:
    from model import Board

# Configure logging
logger = logging.getLogger(__name__)

# Game constants
BOARD_SIZE = 15
BLACK_PLAYER = 1
WHITE_PLAYER = 2
NO_WINNER = 0
WINNING_SEQUENCE_LENGTH = 5

# Player names for display
PLAYER_NAMES = {
    BLACK_PLAYER: "Black",
    WHITE_PLAYER: "White"
}

Coord = Tuple[int, int]


class GameController:
    """
    GameController manages the game flow between the model (Board) and view (GUI).
    
    Responsibilities:
    - Tracks current player and game-over state
    - Delegates move placement to the model
    - Detects wins and draws
    - Notifies the view to refresh and present results
    """

    def __init__(self) -> None:
        """Initialize a new game controller with a fresh board and game state."""
        self.board = Board(size=BOARD_SIZE)
        self.current_player: int = BLACK_PLAYER
        self.game_over: bool = False
        self.winner: int = NO_WINNER
        self.winning_coords: Optional[List[Coord]] = None
        self._view = None

    def attach_view(self, view) -> None:
        """
        Attach the view so the controller can trigger refreshes and notifications.
        
        Args:
            view: The GUI view object to notify of state changes.
        """
        self._view = view
        # Initial refresh to sync UI with current game state
        self._refresh_view()

    def start_new_game(self) -> None:
        """Reset the game state to initial conditions and notify the view."""
        self.board.reset()
        self.current_player = BLACK_PLAYER
        self.game_over = False
        self.winner = NO_WINNER
        self.winning_coords = None
        logger.info("New game started")
        self._refresh_view()

    def handle_board_click(self, row: int, col: int) -> None:
        """
        Handle a click on the board at the given logical coordinates.
        
        Attempts to place a stone for the current player, then checks for a win or draw.
        
        Args:
            row: The row coordinate of the click.
            col: The column coordinate of the click.
        """
        if self.game_over:
            logger.debug("Ignoring click: game is already over")
            return

        if not self.board.place_stone(row, col, self.current_player):
            # Invalid move (occupied or out of bounds)
            logger.debug(f"Invalid move at ({row}, {col})")
            return

        logger.info(f"Player {PLAYER_NAMES[self.current_player]} placed stone at ({row}, {col})")
        self._process_move_result(row, col)

    def undo_move(self) -> None:
        """
        Undo the last move.
        
        If successful, restores the current player to the one who played the undone move
        and clears any end-game state.
        """
        undone = self.board.undo()
        if undone is None:
            logger.debug("No moves to undo")
            return

        # Set the current player to the one who played the undone move
        _, _, player = undone
        self.current_player = player
        # Clear game-over state since the position changed
        self.game_over = False
        self.winner = NO_WINNER
        self.winning_coords = None
        logger.info(f"Undone move by {PLAYER_NAMES[player]}")
        self._refresh_view()

    def redo_move(self) -> None:
        """
        Redo the most recently undone move (if any).
        
        Recomputes win/draw conditions and updates game state accordingly.
        """
        if self.game_over:
            logger.debug("Ignoring redo: game is already over")
            return

        redone = self.board.redo()
        if redone is None:
            logger.debug("No moves to redo")
            return

        row, col, player = redone
        # After redoing a move, it's now the other player's turn
        self.current_player = self._get_opponent(player)
        logger.info(f"Redone move by {PLAYER_NAMES[player]} at ({row}, {col})")
        self._process_move_result(row, col)

    def get_status_text(self) -> str:
        """
        Return a human-readable status string for the UI.
        
        Returns:
            A string describing the current game state.
        """
        if self.game_over:
            if self.winner == BLACK_PLAYER:
                return "Game Over: Black wins!"
            elif self.winner == WHITE_PLAYER:
                return "Game Over: White wins!"
            else:
                return "Game Over: Draw."
        else:
            player_name = PLAYER_NAMES[self.current_player]
            return f"Turn: {player_name}"

    def _process_move_result(self, row: int, col: int) -> None:
        """
        Process the result of a move: check for win/draw and update game state.
        
        Args:
            row: The row coordinate of the move.
            col: The column coordinate of the move.
        """
        # Check for a winning sequence from the last move
        winner, coords = self.board.check_win_from(row, col)
        if winner != NO_WINNER:
            self._end_game_with_winner(winner, coords)
            return

        # Check for a draw (board full)
        if self.board.is_full():
            self._end_game_with_draw()
            return

        # Continue to next player's turn
        self.current_player = self._get_opponent(self.current_player)
        self._refresh_view()

    def _end_game_with_winner(self, winner: int, coords: List[Coord]) -> None:
        """
        End the game with a winner.
        
        Args:
            winner: The player number who won (1 or 2).
            coords: The coordinates of the winning sequence.
        """
        self.game_over = True
        self.winner = winner
        self.winning_coords = coords
        logger.info(f"{PLAYER_NAMES[winner]} wins!")
        self._refresh_view()
        if self._view:
            self._view.show_winner(winner, coords)

    def _end_game_with_draw(self) -> None:
        """End the game with a draw (board is full)."""
        self.game_over = True
        self.winner = NO_WINNER
        self.winning_coords = None
        logger.info("Game ended in a draw")
        self._refresh_view()

    def _get_opponent(self, player: int) -> int:
        """
        Get the opponent of the given player.
        
        Args:
            player: The player number (1 for Black, 2 for White).
            
        Returns:
            The opponent's player number.
        """
        return WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER

    def _refresh_view(self) -> None:
        """Refresh the view to reflect the current game state."""
        if self._view:
            self._view.refresh()