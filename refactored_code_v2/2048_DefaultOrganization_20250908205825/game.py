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
MERGE_MULTIPLIER = 2

# Direction constants
DIRECTION_UP = 'up'
DIRECTION_DOWN = 'down'
DIRECTION_LEFT = 'left'
DIRECTION_RIGHT = 'right'
VALID_DIRECTIONS = {DIRECTION_UP, DIRECTION_DOWN, DIRECTION_LEFT, DIRECTION_RIGHT}
HORIZONTAL_DIRECTIONS = {DIRECTION_LEFT, DIRECTION_RIGHT}
VERTICAL_DIRECTIONS = {DIRECTION_UP, DIRECTION_DOWN}


class Game2048:
    """
    Core 2048 game mechanics on an NxN board (default 4x4).
    
    Manages game state including board configuration, scoring, and move mechanics.
    """

    def __init__(self, size: int = DEFAULT_BOARD_SIZE, 
                 board: Optional[List[List[int]]] = None,
                 score: int = 0, max_tile: int = 0) -> None:
        """
        Initialize a 2048 game instance.
        
        Args:
            size: Board dimension (NxN grid).
            board: Optional existing board state. If None, creates new board with initial tiles.
            score: Initial score value.
            max_tile: Initial maximum tile value.
        """
        self.size = size
        if board is None:
            self._initialize_new_game()
        else:
            self._initialize_from_state(board, score, max_tile)

    def _initialize_new_game(self) -> None:
        """Initialize a fresh game with empty board and spawn initial tiles."""
        self.board = self._create_empty_board()
        self.score = 0
        self.max_tile = 0
        for _ in range(INITIAL_TILES_COUNT):
            self.add_random_tile()

    def _initialize_from_state(self, board: List[List[int]], 
                               score: int, max_tile: int) -> None:
        """
        Initialize game from existing state.
        
        Args:
            board: Existing board configuration.
            score: Existing score.
            max_tile: Existing maximum tile value.
        """
        self.board = [row[:] for row in board]
        self.score = score
        self.max_tile = max(max_tile, self.get_max_tile())

    def _create_empty_board(self) -> List[List[int]]:
        """
        Create an empty NxN board filled with zeros.
        
        Returns:
            Empty board of size NxN.
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
        empty_positions = self._get_empty_positions()
        if not empty_positions:
            logger.debug("No empty positions available for new tile")
            return False
        
        row, col = random.choice(empty_positions)
        tile_value = self._generate_new_tile_value()
        self.board[row][col] = tile_value
        self._update_max_tile(tile_value)
        logger.debug(f"Added tile {tile_value} at position ({row}, {col})")
        return True

    def _get_empty_positions(self) -> List[Tuple[int, int]]:
        """
        Find all empty cell positions on the board.
        
        Returns:
            List of (row, col) tuples for empty cells.
        """
        return [(r, c) for r in range(self.size) for c in range(self.size) 
                if self.board[r][c] == EMPTY_CELL]

    def _generate_new_tile_value(self) -> int:
        """
        Generate a new tile value based on probability distribution.
        
        Returns:
            4 with 10% probability, 2 with 90% probability.
        """
        return NEW_TILE_VALUE_HIGH if random.random() < HIGH_VALUE_PROBABILITY else NEW_TILE_VALUE_LOW

    def _update_max_tile(self, value: int) -> None:
        """
        Update maximum tile if new value exceeds current maximum.
        
        Args:
            value: Tile value to compare against current maximum.
        """
        if value > self.max_tile:
            self.max_tile = value

    def move(self, direction: str) -> Tuple[bool, int]:
        """
        Execute a move in the given direction.
        
        Args:
            direction: One of 'up', 'down', 'left', 'right'.
            
        Returns:
            Tuple of (board_changed, points_gained).
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
            logger.debug(f"Move {direction}: changed={changed}, score_gained={gained_total}")
        
        return changed, gained_total

    def _move_horizontal(self, direction: str) -> Tuple[bool, int]:
        """
        Execute horizontal move (left or right).
        
        Args:
            direction: Either 'left' or 'right'.
            
        Returns:
            Tuple of (board_changed, points_gained).
        """
        changed = False
        gained_total = 0

        for row_idx in range(self.size):
            row = self.board[row_idx][:]
            # Reverse for right movement to reuse left logic
            if direction == DIRECTION_RIGHT:
                row = row[::-1]
            
            new_row, gained = self.move_line(row)
            
            # Reverse back for right movement
            if direction == DIRECTION_RIGHT:
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
        Execute vertical move (up or down).
        
        Args:
            direction: Either 'up' or 'down'.
            
        Returns:
            Tuple of (board_changed, points_gained).
        """
        changed = False
        gained_total = 0

        for col_idx in range(self.size):
            col = [self.board[row_idx][col_idx] for row_idx in range(self.size)]
            # Reverse for down movement to reuse up logic
            if direction == DIRECTION_DOWN:
                col = col[::-1]
            
            new_col, gained = self.move_line(col)
            
            # Reverse back for down movement
            if direction == DIRECTION_DOWN:
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
            line: List of tile values to process.
            
        Returns:
            Tuple of (processed_line, points_gained_from_merges).
        """
        # Compress: remove empty cells
        non_empty_tiles = [tile for tile in line if tile != EMPTY_CELL]
        
        gained = 0
        merged_tiles: List[int] = []
        skip_next = False

        for idx in range(len(non_empty_tiles)):
            if skip_next:
                skip_next = False
                continue
            
            # Check if current tile can merge with next tile
            if idx + 1 < len(non_empty_tiles) and non_empty_tiles[idx] == non_empty_tiles[idx + 1]:
                merged_value = non_empty_tiles[idx] * MERGE_MULTIPLIER
                merged_tiles.append(merged_value)
                gained += merged_value
                skip_next = True  # Skip next tile as it has been merged
            else:
                merged_tiles.append(non_empty_tiles[idx])

        # Pad with empty cells to maintain board size
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
        if self._get_empty_positions():
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
            True if horizontal merge is possible.
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
            True if vertical merge is possible.
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
            Maximum tile value, or 0 if board is empty.
        """
        try:
            return max(max(row) for row in self.board) if self.board else EMPTY_CELL
        except ValueError:
            logger.error("Error calculating max tile")
            return EMPTY_CELL

    def to_state(self) -> Dict:
        """
        Serialize the current game state.
        
        Returns:
            Dictionary containing board, score, and metadata.
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
            state: Dictionary containing serialized game state.
            
        Returns:
            Game2048 instance restored from state.
        """
        size = state.get('size', DEFAULT_BOARD_SIZE)
        board = state.get('board', [[EMPTY_CELL] * size for _ in range(size)])
        score = state.get('score', 0)
        max_tile = state.get('max_tile', 0)
        
        return Game2048(size=size, board=board, score=score, max_tile=max_tile)