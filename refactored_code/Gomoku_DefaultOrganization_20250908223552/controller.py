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
WINNING_LINE_LENGTH = 5

# Player names for display
PLAYER_NAMES = {
    BLACK_PLAYER: "Black",
    WHITE_PLAYER: "White"
}

Coord = Tuple[int, int]


class GameController:
    """
    GameController manages the game flow between the Board model and the GUI view.
    
    Responsibilities:
    - Tracks current player and game-over state
    - Delegates move placement to the model
    - Detects wins and draws
    - Notifies the view to refresh and present results
    - Manages undo/redo operations
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
        Attach the view to enable controller-to-view communication.
        
        Args:
            view: The GUI view object that will receive refresh and notification calls.
        """
        self._view = view
        # Initial refresh to sync UI with current game state
        self._refresh_view()

    def start_new_game(self) -> None:
        """Reset the game state to initial conditions and refresh the view."""
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
        If the game is already over or the move is invalid, this method returns early.
        
        Args:
            row: The row coordinate of the click.
            col: The column coordinate of the click.
        """
        if self.game_over:
            logger.debug("Ignoring click: game is already over")
            return

        # Attempt to place the stone
        if not self.board.place_stone(row, col, self.current_player):
            logger.debug(f"Invalid move at ({row}, {col})")
            return

        logger.info(f"Player {PLAYER_NAMES[self.current_player]} placed stone at ({row}, {col})")

        # Check for a win from the last move
        if self._check_and_handle_win(row, col):
            return

        # Check for a draw
        if self._check_and_handle_draw():
            return

        # Switch to the next player
        self._switch_player()
        self._refresh_view()

    def undo_move(self) -> None:
        """
        Undo the last move.
        
        If successful, updates the current player and clears any end-game state.
        If there are no moves to undo, this method returns early.
        """
        undone = self.board.undo()
        if undone is None:
            logger.debug("No moves to undo")
            return

        # The undone move was made by this player, so it's now their turn again
        _, _, player = undone
        self.current_player = player
        
        # Clear game-over state since the position has changed
        self.game_over = False
        self.winner = NO_WINNER
        self.winning_coords = None
        
        logger.info(f"Undone move by {PLAYER_NAMES[player]}")
        self._refresh_view()

    def redo_move(self) -> None:
        """
        Redo the most recently undone move.
        
        Recomputes win/draw conditions and updates game state accordingly.
        If there are no moves to redo or the game is over, this method returns early.
        """
        if self.game_over:
            logger.debug("Cannot redo: game is already over")
            return

        redone = self.board.redo()
        if redone is None:
            logger.debug("No moves to redo")
            return

        row, col, player = redone
        logger.info(f"Redone move by {PLAYER_NAMES[player]} at ({row}, {col})")

        # After redoing a move, it's now the other player's turn
        self.current_player = self._get_other_player(player)

        # Check for win or draw after the redo
        if self._check_and_handle_win(row, col):
            return

        if self._check_and_handle_draw():
            return

        self._refresh_view()

    def get_status_text(self) -> str:
        """
        Return a human-readable status string for the UI.
        
        Returns:
            A string describing the current game state (whose turn it is or game over status).
        """
        if self.game_over:
            if self.winner != NO_WINNER:
                return f"Game Over: {PLAYER_NAMES[self.winner]} wins!"
            else:
                return "Game Over: Draw."
        else:
            return f"Turn: {PLAYER_NAMES[self.current_player]}"

    def _refresh_view(self) -> None:
        """Notify the view to refresh its display with the current game state."""
        if self._view:
            self._view.refresh()

    def _switch_player(self) -> None:
        """Switch the current player to the other player."""
        self.current_player = self._get_other_player(self.current_player)

    @staticmethod
    def _get_other_player(player: int) -> int:
        """
        Get the other player given the current player.
        
        Args:
            player: The current player (BLACK_PLAYER or WHITE_PLAYER).
            
        Returns:
            The other player.
        """
        return WHITE_PLAYER if player == BLACK_PLAYER else BLACK_PLAYER

    def _check_and_handle_win(self, row: int, col: int) -> bool:
        """
        Check if the last move resulted in a win and handle the end-game state.
        
        Args:
            row: The row coordinate of the last move.
            col: The column coordinate of the last move.
            
        Returns:
            True if a win was detected, False otherwise.
        """
        winner, coords = self.board.check_win_from(row, col)
        if winner != NO_WINNER:
            self.game_over = True
            self.winner = winner
            self.winning_coords = coords
            logger.info(f"{PLAYER_NAMES[winner]} wins!")
            self._refresh_view()
            if self._view:
                self._view.show_winner(winner, coords)
            return True
        return False

    def _check_and_handle_draw(self) -> bool:
        """
        Check if the board is full (draw condition) and handle the end-game state.
        
        Returns:
            True if a draw was detected, False otherwise.
        """
        if self.board.is_full():
            self.game_over = True
            self.winner = NO_WINNER
            self.winning_coords = None
            logger.info("Game ended in a draw")
            self._refresh_view()
            return True
        return False