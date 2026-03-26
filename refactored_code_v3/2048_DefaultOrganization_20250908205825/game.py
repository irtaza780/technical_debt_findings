import logging
import random
from typing import List, Tuple, Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Game constants
DEFAULT_BOARD_SIZE = 4
INITIAL_TILES_COUNT = 2
NEW_TILE_VALUE_HIGH = 4
NEW_TILE_VALUE_LOW = 2
HIGH_VALUE_PROBABILITY = 0.1
EMPTY_CELL = 0
VALID_DIRECTIONS = {'up', 'down', 'left', 'right'}
HORIZONTAL_DIRECTIONS = {'left', 'right'}
VERTICAL_DIRECTIONS = {'up', 'down'}


class Game2048:
    """
    Core 2048 game mechanics on an NxN board (default 4x4).
    
    Manages board state, tile movements, merging logic, and scoring.
    """

    def __init__(
        self,
        size: int = DEFAULT_BOARD_SIZE,
        board: Optional[List[List[int]]] = None,
        score: int = 0,
        max_tile: int = 0,
    ) -> None:
        """
        Initialize a 2048 game instance.
        
        Args:
            size: Board dimensions (size x size). Defaults to 4.
            board: Optional existing board state. If None, creates new board.
            score: Initial score. Defaults to 0.
            max_tile: Initial max tile value. Defaults to 0.
        """
        self.size = size
        if board is None:
            self._initialize_new_game()
        else:
            self._initialize_from_state(board, score, max_tile)

    def _initialize_new_game(self) -> None:
        """Initialize a fresh game board with two random tiles."""
        self.board = self._create_empty_board()
        self.score = 0
        self.max_tile = 0
        for _ in range(INITIAL_TILES_COUNT):
            self.add_random_tile()

    def _initialize_from_state(
        self,
        board: List[List[int]],
        score: int,
        max_tile: int,
    ) -> None:
        """
        Initialize game from existing state.
        
        Args:
            board: Existing board configuration.
            score: Existing score.
            max_tile: Existing max tile value.
        """
        self.board = [row[:] for row in board]
        self.score = score
        self.max_tile = max(max_tile, self.get_max_tile())

    def _create_empty_board(self) -> List[List[int]]:
        """
        Create an empty board filled with zeros.
        
        Returns:
            A size x size board with all cells set to 0.
        """
        return [[EMPTY_CELL for _ in range(self.size)] for _ in range(self.size)]

    def reset(self) -> None:
        """Reset the game to initial state with two random tiles."""
        self._initialize_new_game()
        logger.info("Game reset to initial state")

    def add_random_tile(self) -> bool:
        """
        Add a new tile at a random empty position.
        
        Tile value is 4 with 10% probability, 2 with 90% probability.
        
        Returns:
            True if a tile was added, False if no empty cells exist.
        """
        empty_cells = self._get_empty_cells()
        if not empty_cells:
            logger.debug("No empty cells available for new tile")
            return False

        row, col = random.choice(empty_cells)
        tile_value = self._generate_new_tile_value()
        self.board[row][col] = tile_value
        self._update_max_tile(tile_value)
        logger.debug(f"Added tile {tile_value} at ({row}, {col})")
        return True

    def _get_empty_cells(self) -> List[Tuple[int, int]]:
        """
        Find all empty cells on the board.
        
        Returns:
            List of (row, col) tuples for empty cells.
        """
        return [
            (row, col)
            for row in range(self.size)
            for col in range(self.size)
            if self.board[row][col] == EMPTY_CELL
        ]

    def _generate_new_tile_value(self) -> int:
        """
        Generate a new tile value based on probability distribution.
        
        Returns:
            4 with 10% probability, 2 with 90% probability.
        """
        return (
            NEW_TILE_VALUE_HIGH
            if random.random() < HIGH_VALUE_PROBABILITY
            else NEW_TILE_VALUE_LOW
        )

    def _update_max_tile(self, tile_value: int) -> None:
        """
        Update the maximum tile value if the new tile exceeds current max.
        
        Args:
            tile_value: The value of the newly placed tile.
        """
        if tile_value > self.max_tile:
            self.max_tile = tile_value

    def move(self, direction: str) -> Tuple[bool, int]:
        """
        Execute a move in the given direction.
        
        Args:
            direction: One of 'up', 'down', 'left', 'right'.
        
        Returns:
            Tuple of (board_changed, score_gained).
        """
        if direction not in VALID_DIRECTIONS:
            logger.warning(f"Invalid direction: {direction}")
            return False, 0

        changed = False
        gained_total = 0

        if direction in HORIZONTAL_DIRECTIONS:
            changed, gained_total = self._move_horizontal(direction)
        else:
            changed, gained_total = self._move_vertical(direction)

        if changed:
            logger.debug(f"Move {direction}: changed={changed}, gained={gained_total}")

        return changed, gained_total

    def _move_horizontal(self, direction: str) -> Tuple[bool, int]:
        """
        Execute a horizontal move (left or right).
        
        Args:
            direction: Either 'left' or 'right'.
        
        Returns:
            Tuple of (board_changed, total_score_gained).
        """
        changed = False
        gained_total = 0

        for row_idx in range(self.size):
            row = self.board[row_idx][:]
            # Reverse for right movement to reuse left logic
            if direction == 'right':
                row = row[::-1]

            new_row, gained = self.move_line(row)

            # Reverse back for right movement
            if direction == 'right':
                new_row = new_row[::-1]

            if new_row != self.board[row_idx]:
                changed = True
                self.board[row_idx] = new_row

            if gained:
                self.score += gained
                self._update_max_tile(max(new_row))
                gained_total += gained

        return changed, gained_total

    def _move_vertical(self, direction: str) -> Tuple[bool, int]:
        """
        Execute a vertical move (up or down).
        
        Args:
            direction: Either 'up' or 'down'.
        
        Returns:
            Tuple of (board_changed, total_score_gained).
        """
        changed = False
        gained_total = 0

        for col_idx in range(self.size):
            col = [self.board[row_idx][col_idx] for row_idx in range(self.size)]
            # Reverse for down movement to reuse up logic
            if direction == 'down':
                col = col[::-1]

            new_col, gained = self.move_line(col)

            # Reverse back for down movement
            if direction == 'down':
                new_col = new_col[::-1]

            # Apply changes back to board
            for row_idx in range(self.size):
                if self.board[row_idx][col_idx] != new_col[row_idx]:
                    changed = True
                    self.board[row_idx][col_idx] = new_col[row_idx]

            if gained:
                self.score += gained
                self._update_max_tile(max(new_col))
                gained_total += gained

        return changed, gained_total

    def move_line(self, line: List[int]) -> Tuple[List[int], int]:
        """
        Process a single line (row/column) by compressing and merging tiles.
        
        Tiles are moved left, then adjacent equal tiles are merged.
        Example: [2, 0, 2, 4] -> [4, 4, 0, 0], gained=4.
        
        Args:
            line: A list of tile values to process.
        
        Returns:
            Tuple of (processed_line, score_gained_from_merges).
        """
        # Compress: remove zeros
        non_zero_tiles = [tile for tile in line if tile != EMPTY_CELL]
        gained = 0
        merged_tiles: List[int] = []
        skip_next = False

        for idx in range(len(non_zero_tiles)):
            if skip_next:
                skip_next = False
                continue

            # Check if current tile can merge with next tile
            if idx + 1 < len(non_zero_tiles) and non_zero_tiles[idx] == non_zero_tiles[idx + 1]:
                merged_value = non_zero_tiles[idx] * 2
                merged_tiles.append(merged_value)
                gained += merged_value
                skip_next = True  # Skip next tile as it has been merged
            else:
                merged_tiles.append(non_zero_tiles[idx])

        # Pad with zeros to maintain board size
        merged_tiles.extend([EMPTY_CELL] * (self.size - len(merged_tiles)))
        return merged_tiles, gained

    def can_move(self) -> bool:
        """
        Check if any valid move is possible.
        
        A move is possible if there are empty cells or adjacent equal tiles.
        
        Returns:
            True if at least one move is possible, False otherwise.
        """
        # Check for empty cells
        if self._get_empty_cells():
            return True

        # Check for possible horizontal merges
        if self._has_adjacent_equal_tiles_horizontal():
            return True

        # Check for possible vertical merges
        if self._has_adjacent_equal_tiles_vertical():
            return True

        return False

    def _has_adjacent_equal_tiles_horizontal(self) -> bool:
        """
        Check if any horizontally adjacent tiles are equal.
        
        Returns:
            True if horizontal merge is possible, False otherwise.
        """
        for row_idx in range(self.size):
            for col_idx in range(self.size - 1):
                if self.board[row_idx][col_idx] == self.board[row_idx][col_idx + 1]:
                    return True
        return False

    def _has_adjacent_equal_tiles_vertical(self) -> bool:
        """
        Check if any vertically adjacent tiles are equal.
        
        Returns:
            True if vertical merge is possible, False otherwise.
        """
        for col_idx in range(self.size):
            for row_idx in range(self.size - 1):
                if self.board[row_idx][col_idx] == self.board[row_idx + 1][col_idx]:
                    return True
        return False

    def get_max_tile(self) -> int:
        """
        Get the maximum tile value currently on the board.
        
        Returns:
            The highest tile value, or 0 if board is empty.
        """
        try:
            return max(max(row) for row in self.board) if self.board else 0
        except ValueError:
            logger.error("Error calculating max tile")
            return 0

    def to_state(self) -> Dict:
        """
        Serialize the current game state.
        
        Returns:
            Dictionary containing size, board, score, and max_tile.
        """
        return {
            'size': self.size,
            'board': [row[:] for row in self.board],
            'score': self.score,
            'max_tile': self.max_tile,
        }

    @staticmethod
    def from_state(state: Dict) -> 'Game2048':
        """
        Deserialize a game from a saved state dictionary.
        
        Args:
            state: Dictionary with keys 'size', 'board', 'score', 'max_tile'.
        
        Returns:
            A Game2048 instance restored from the state.
        """
        size = state.get('size', DEFAULT_BOARD_SIZE)
        board = state.get('board', [[EMPTY_CELL] * size for _ in range(size)])
        score = state.get('score', 0)
        max_tile = state.get('max_tile', 0)
        return Game2048(size=size, board=board, score=score, max_tile=max_tile)