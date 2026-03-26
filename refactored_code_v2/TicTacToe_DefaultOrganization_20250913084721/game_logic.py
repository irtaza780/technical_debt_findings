import logging
from typing import List, Optional, Tuple

from constants import GRID_SIZE, SYMBOL_X, SYMBOL_O

logger = logging.getLogger(__name__)

EMPTY_CELL = ""
MAX_MOVES = GRID_SIZE * GRID_SIZE


class TicTacToeGame:
    """Game state and logic for a standard 3x3 Tic-Tac-Toe."""

    def __init__(self) -> None:
        """Initialize a new Tic-Tac-Toe game with X as the starting player."""
        self.grid_size: int = GRID_SIZE
        self.symbols = (SYMBOL_X, SYMBOL_O)
        self.board: List[List[str]] = []
        self.current_player: str = SYMBOL_X
        self.move_count: int = 0
        self.winner: Optional[str] = None
        self.winning_line: Optional[List[Tuple[int, int]]] = None
        self.next_starting_player: str = SYMBOL_X
        self.reset(alternate=False)

    def reset(self, alternate: bool = False) -> None:
        """Reset the game to its initial state.

        Args:
            alternate: If True, alternate who starts compared to the last game.
                       If False, X starts (used for initial game).
        """
        self.board = [[EMPTY_CELL for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.move_count = 0
        self.winner = None
        self.winning_line = None

        # Set current player based on alternation preference
        if alternate:
            self.current_player = self.next_starting_player
        else:
            self.current_player = SYMBOL_X

        # Prepare the next starting player for subsequent resets
        self.next_starting_player = self._get_opponent(self.current_player)

    def make_move(self, row: int, col: int) -> bool:
        """Attempt to place the current player's symbol at (row, col).

        Args:
            row: The row index (0-based).
            col: The column index (0-based).

        Returns:
            True if the move is successful; False otherwise.
        """
        # Check if game is already over
        if self.winner is not None or self.is_draw():
            logger.debug("Cannot make move: game is already over")
            return False

        # Validate move coordinates
        if not self._is_valid_position(row, col):
            logger.debug(f"Invalid position: ({row}, {col})")
            return False

        # Check if cell is empty
        if self.board[row][col] != EMPTY_CELL:
            logger.debug(f"Cell ({row}, {col}) is already occupied")
            return False

        # Place the symbol
        self.board[row][col] = self.current_player
        self.move_count += 1
        logger.debug(f"Move made: {self.current_player} at ({row}, {col})")

        # Check for winner
        winner, line = self.check_winner()
        if winner:
            self.winner = winner
            self.winning_line = line
            logger.info(f"Winner: {winner}")
            return True

        # Check for draw
        if self.is_draw():
            logger.info("Game is a draw")
            return True

        # Switch to next player
        self.current_player = self._get_opponent(self.current_player)
        return True

    def get_cell(self, row: int, col: int) -> str:
        """Get the symbol at a given cell.

        Args:
            row: The row index (0-based).
            col: The column index (0-based).

        Returns:
            The symbol at the cell ('X', 'O') or empty string if unoccupied or out of bounds.
        """
        if self._is_valid_position(row, col):
            return self.board[row][col]
        return EMPTY_CELL

    def available_moves(self) -> List[Tuple[int, int]]:
        """Return a list of available (row, col) moves.

        Returns:
            List of tuples representing empty cells on the board.
        """
        moves: List[Tuple[int, int]] = []
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.board[row][col] == EMPTY_CELL:
                    moves.append((row, col))
        return moves

    def is_draw(self) -> bool:
        """Check if the game is a draw.

        Returns:
            True if the board is full and there is no winner; False otherwise.
        """
        return self.winner is None and self.move_count >= MAX_MOVES

    def check_winner(self) -> Tuple[Optional[str], Optional[List[Tuple[int, int]]]]:
        """Check the board for a winner.

        Returns:
            Tuple of (winner_symbol, winning_line) where winner_symbol is 'X', 'O', or None,
            and winning_line is a list of (row, col) tuples or None.
        """
        # Check rows
        winner_line = self._check_rows()
        if winner_line:
            return self.board[winner_line[0][0]][winner_line[0][1]], winner_line

        # Check columns
        winner_line = self._check_columns()
        if winner_line:
            return self.board[winner_line[0][0]][winner_line[0][1]], winner_line

        # Check main diagonal
        winner_line = self._check_main_diagonal()
        if winner_line:
            return self.board[winner_line[0][0]][winner_line[0][1]], winner_line

        # Check anti-diagonal
        winner_line = self._check_anti_diagonal()
        if winner_line:
            return self.board[winner_line[0][0]][winner_line[0][1]], winner_line

        return None, None

    def _is_valid_position(self, row: int, col: int) -> bool:
        """Check if a position is within the board boundaries.

        Args:
            row: The row index.
            col: The column index.

        Returns:
            True if the position is valid; False otherwise.
        """
        return 0 <= row < self.grid_size and 0 <= col < self.grid_size

    def _get_opponent(self, player: str) -> str:
        """Get the opponent symbol for a given player.

        Args:
            player: The current player symbol ('X' or 'O').

        Returns:
            The opponent's symbol.
        """
        return SYMBOL_O if player == SYMBOL_X else SYMBOL_X

    def _check_rows(self) -> Optional[List[Tuple[int, int]]]:
        """Check all rows for a winning line.

        Returns:
            List of (row, col) tuples if a row is won; None otherwise.
        """
        for row in range(self.grid_size):
            if self.board[row][0] != EMPTY_CELL:
                # Check if all cells in the row match the first cell
                if all(self.board[row][col] == self.board[row][0] for col in range(self.grid_size)):
                    return [(row, col) for col in range(self.grid_size)]
        return None

    def _check_columns(self) -> Optional[List[Tuple[int, int]]]:
        """Check all columns for a winning line.

        Returns:
            List of (row, col) tuples if a column is won; None otherwise.
        """
        for col in range(self.grid_size):
            if self.board[0][col] != EMPTY_CELL:
                # Check if all cells in the column match the first cell
                if all(self.board[row][col] == self.board[0][col] for row in range(self.grid_size)):
                    return [(row, col) for row in range(self.grid_size)]
        return None

    def _check_main_diagonal(self) -> Optional[List[Tuple[int, int]]]:
        """Check the main diagonal (top-left to bottom-right) for a winning line.

        Returns:
            List of (row, col) tuples if the diagonal is won; None otherwise.
        """
        if self.board[0][0] != EMPTY_CELL:
            # Check if all diagonal cells match the first cell
            if all(self.board[i][i] == self.board[0][0] for i in range(self.grid_size)):
                return [(i, i) for i in range(self.grid_size)]
        return None

    def _check_anti_diagonal(self) -> Optional[List[Tuple[int, int]]]:
        """Check the anti-diagonal (top-right to bottom-left) for a winning line.

        Returns:
            List of (row, col) tuples if the anti-diagonal is won; None otherwise.
        """
        if self.board[0][self.grid_size - 1] != EMPTY_CELL:
            # Check if all anti-diagonal cells match the first cell
            if all(
                self.board[i][self.grid_size - 1 - i] == self.board[0][self.grid_size - 1]
                for i in range(self.grid_size)
            ):
                return [(i, self.grid_size - 1 - i) for i in range(self.grid_size)]
        return None