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
            ValueError: If rows or cols is less than 4.
        """
        if rows < MIN_BOARD_DIMENSION or cols < MIN_BOARD_DIMENSION:
            raise ValueError(
                f"Connect Four requires at least {MIN_BOARD_DIMENSION} rows "
                f"and {MIN_BOARD_DIMENSION} columns."
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
        logger.info("Game reset to initial state.")

    def get_board(self) -> Tuple[Tuple[int, ...], ...]:
        """
        Return an immutable snapshot of the current board state.

        Returns:
            A tuple of tuples representing the board.
        """
        return tuple(tuple(row) for row in self.board)

    def get_current_player(self) -> int:
        """
        Return the current player's numeric ID.

        Returns:
            1 for player one, 2 for player two.
        """
        return self.current_player

    def get_winner(self) -> Optional[int]:
        """
        Return the winner's ID, or None if no winner yet.

        Returns:
            Player ID (1 or 2) if there is a winner, None otherwise.
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
            The row index of the lowest empty cell.

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

        Updates game state including checking for win/draw conditions and
        switching players if the game continues.

        Args:
            col: The column index where the disc should be dropped.

        Returns:
            The row index where the disc landed.

        Raises:
            ValueError: If the game is over, column is out of range, or column is full.
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

        logger.debug(f"Player {self.current_player} dropped disc at ({row}, {col}).")

        self._update_game_state(row, col)
        return row

    def _update_game_state(self, row: int, col: int) -> None:
        """
        Update game state after a disc is placed.

        Checks for win or draw conditions and switches players if the game
        continues.

        Args:
            row: The row index of the placed disc.
            col: The column index of the placed disc.
        """
        if self.check_win(row, col):
            self.winner = self.current_player
            self.game_over = True
            logger.info(f"Player {self.current_player} wins!")
        elif self.check_draw():
            self.game_over = True
            logger.info("Game ended in a draw.")
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

    def count_in_direction(
        self, row: int, col: int, dr: int, dc: int, player: int
    ) -> int:
        """
        Count consecutive discs for a player in both directions from a position.

        Counts the player's discs starting from (row, col) and extending in
        both the (dr, dc) direction and its opposite (-dr, -dc).

        Args:
            row: The starting row index.
            col: The starting column index.
            dr: The row direction delta (-1, 0, or 1).
            dc: The column direction delta (-1, 0, or 1).
            player: The player ID to count discs for.

        Returns:
            The total count of consecutive discs (including the starting position).
        """
        count = 1

        # Count in forward direction
        count += self._count_direction(row, col, dr, dc, player)

        # Count in backward direction
        count += self._count_direction(row, col, -dr, -dc, player)

        return count

    def _count_direction(self, row: int, col: int, dr: int, dc: int, player: int) -> int:
        """
        Count consecutive discs in a single direction from a position.

        Args:
            row: The starting row index.
            col: The starting column index.
            dr: The row direction delta.
            dc: The column direction delta.
            player: The player ID to count discs for.

        Returns:
            The count of consecutive discs in the specified direction (excluding start).
        """
        count = 0
        current_row, current_col = row + dr, col + dc

        while (
            0 <= current_row < self.rows
            and 0 <= current_col < self.cols
            and self.board[current_row][current_col] == player
        ):
            count += 1
            current_row += dr
            current_col += dc

        return count

    def check_win(self, row: int, col: int) -> bool:
        """
        Check if the move at (row, col) created a four-in-a-row.

        Examines all four directions (horizontal, vertical, and both diagonals)
        to determine if the placed disc completes a winning sequence.

        Args:
            row: The row index of the placed disc.
            col: The column index of the placed disc.

        Returns:
            True if the move creates a four-in-a-row, False otherwise.
        """
        player = self.board[row][col]
        if player == EMPTY_CELL:
            return False

        # Check all four directions for a winning sequence
        for dr, dc in WIN_CHECK_DIRECTIONS:
            if self.count_in_direction(row, col, dr, dc, player) >= WINNING_LENGTH:
                return True

        return False