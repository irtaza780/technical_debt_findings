import logging
from typing import List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Game constants
MIN_BOARD_DIMENSION = 4
DEFAULT_ROWS = 6
DEFAULT_COLS = 7
WINNING_LENGTH = 4
EMPTY_CELL = 0
PLAYER_1 = 1
PLAYER_2 = 2

# Direction vectors for win checking: (row_delta, col_delta)
WIN_CHECK_DIRECTIONS = [
    (0, 1),   # Horizontal
    (1, 0),   # Vertical
    (1, 1),   # Diagonal down-right
    (-1, 1),  # Diagonal up-right
]


class ConnectFourGame:
    """Encapsulates the game state and rules for Connect Four."""

    def __init__(self, rows: int = DEFAULT_ROWS, cols: int = DEFAULT_COLS) -> None:
        """
        Initialize a new Connect Four game with the given dimensions.

        Args:
            rows: Number of rows in the game board (minimum 4).
            cols: Number of columns in the game board (minimum 4).

        Raises:
            ValueError: If rows or cols is less than the minimum required dimension.
        """
        if rows < MIN_BOARD_DIMENSION or cols < MIN_BOARD_DIMENSION:
            raise ValueError(
                f"Connect Four requires at least {MIN_BOARD_DIMENSION} rows and "
                f"{MIN_BOARD_DIMENSION} columns."
            )
        self.rows = rows
        self.cols = cols
        self.board: List[List[int]] = []
        self.current_player: int = PLAYER_1
        self.winner: Optional[int] = None
        self.game_over: bool = False
        self.move_count: int = 0
        self.last_move: Optional[Tuple[int, int]] = None
        self.reset()

    def reset(self) -> None:
        """Reset the game to its initial state."""
        self.board = [[EMPTY_CELL for _ in range(self.cols)] for _ in range(self.rows)]
        self.current_player = PLAYER_1
        self.winner = None
        self.game_over = False
        self.move_count = 0
        self.last_move = None
        logger.info("Game reset to initial state")

    def get_board(self) -> Tuple[Tuple[int, ...], ...]:
        """
        Return an immutable snapshot of the current board state.

        Returns:
            A tuple of tuples representing the board, where each inner tuple
            is a row. Values are 0 (empty), 1 (player 1), or 2 (player 2).
        """
        return tuple(tuple(row) for row in self.board)

    def get_current_player(self) -> int:
        """
        Return the current player's numeric ID.

        Returns:
            1 for player 1, 2 for player 2.
        """
        return self.current_player

    def get_winner(self) -> Optional[int]:
        """
        Return the winner's ID, or None if no winner has been determined yet.

        Returns:
            1 or 2 if there is a winner, None otherwise.
        """
        return self.winner

    def is_valid_move(self, col: int) -> bool:
        """
        Check if a disc can be dropped in the given column.

        A move is valid if the column index is within bounds and the column
        is not full (i.e., the top cell is empty).

        Args:
            col: The column index to check.

        Returns:
            True if the move is valid, False otherwise.
        """
        if self.game_over:
            return False
        if not (0 <= col < self.cols):
            return False
        # If top cell is empty, column has space
        return self.board[0][col] == EMPTY_CELL

    def _find_available_row(self, col: int) -> int:
        """
        Find the lowest available row index in the specified column.

        Searches from the bottom of the board upward to find the first
        empty cell in the given column.

        Args:
            col: The column index to search.

        Returns:
            The row index of the lowest empty cell in the column.

        Raises:
            ValueError: If the column is completely full.
        """
        for row_idx in range(self.rows - 1, -1, -1):
            if self.board[row_idx][col] == EMPTY_CELL:
                return row_idx
        raise ValueError(f"Column {col} is full.")

    def drop_disc(self, col: int) -> int:
        """
        Drop a disc for the current player in the given column.

        Updates the board state, checks for win/draw conditions, and switches
        the current player if the game continues.

        Args:
            col: The column index where the disc should be dropped.

        Returns:
            The row index where the disc landed.

        Raises:
            ValueError: If the game is over, the column is out of range,
                       or the column is full.
        """
        if self.game_over:
            raise ValueError("The game is already over.")
        if not (0 <= col < self.cols):
            raise ValueError(f"Column must be between 0 and {self.cols - 1}.")
        if not self.is_valid_move(col):
            raise ValueError("Invalid move: column is full or out of range.")

        row = self._find_available_row(col)
        self.board[row][col] = self.current_player
        self.last_move = (row, col)
        self.move_count += 1

        logger.debug(f"Player {self.current_player} dropped disc at ({row}, {col})")

        self._process_move_outcome(row, col)
        return row

    def _process_move_outcome(self, row: int, col: int) -> None:
        """
        Process the outcome of a move: check for win, draw, or switch player.

        Args:
            row: The row index of the move.
            col: The column index of the move.
        """
        if self.check_win(row, col):
            self.winner = self.current_player
            self.game_over = True
            logger.info(f"Player {self.current_player} wins!")
        elif self.check_draw():
            self.game_over = True
            logger.info("Game ended in a draw")
        else:
            self.switch_player()

    def check_draw(self) -> bool:
        """
        Check if the game has ended in a draw.

        A draw occurs when the board is completely full and no player has won.

        Returns:
            True if the board is full and there is no winner, False otherwise.
        """
        return self.move_count >= self.rows * self.cols and self.winner is None

    def switch_player(self) -> None:
        """Switch the current player to the other player."""
        self.current_player = PLAYER_2 if self.current_player == PLAYER_1 else PLAYER_1

    def _count_in_direction(
        self, row: int, col: int, row_delta: int, col_delta: int, player: int
    ) -> int:
        """
        Count consecutive discs for a player in a given direction.

        Counts the player's discs starting from (row, col) and extending
        in both the forward (row_delta, col_delta) and backward directions.

        Args:
            row: The starting row index.
            col: The starting column index.
            row_delta: The row direction multiplier (-1, 0, or 1).
            col_delta: The column direction multiplier (-1, 0, or 1).
            player: The player ID to count (1 or 2).

        Returns:
            The total count of consecutive discs for the player in both directions.
        """
        count = 1

        # Count in forward direction
        current_row, current_col = row + row_delta, col + col_delta
        while (
            0 <= current_row < self.rows
            and 0 <= current_col < self.cols
            and self.board[current_row][current_col] == player
        ):
            count += 1
            current_row += row_delta
            current_col += col_delta

        # Count in backward direction
        current_row, current_col = row - row_delta, col - col_delta
        while (
            0 <= current_row < self.rows
            and 0 <= current_col < self.cols
            and self.board[current_row][current_col] == player
        ):
            count += 1
            current_row -= row_delta
            current_col -= col_delta

        return count

    def check_win(self, row: int, col: int) -> bool:
        """
        Check if the move at (row, col) created a winning four-in-a-row.

        Checks all four directions (horizontal, vertical, and both diagonals)
        to determine if the current player has won.

        Args:
            row: The row index of the move to check.
            col: The column index of the move to check.

        Returns:
            True if the move created a four-in-a-row, False otherwise.
        """
        player = self.board[row][col]
        if player == EMPTY_CELL:
            return False

        # Check all four directions for a winning sequence
        for row_delta, col_delta in WIN_CHECK_DIRECTIONS:
            if self._count_in_direction(row, col, row_delta, col_delta, player) >= WINNING_LENGTH:
                return True

        return False