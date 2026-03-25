import random
import logging
from typing import List, Tuple, Dict, Optional

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
DEFAULT_BOARD_SIZE: int = 4
TILE_VALUE_TWO: int = 2
TILE_VALUE_FOUR: int = 4
TILE_FOUR_PROBABILITY: float = 0.1  # 10 % chance of spawning a 4 instead of a 2
VALID_DIRECTIONS: Tuple[str, ...] = ("up", "down", "left", "right")
HORIZONTAL_DIRECTIONS: Tuple[str, ...] = ("left", "right")
VERTICAL_DIRECTIONS: Tuple[str, ...] = ("up", "down")
REVERSE_DIRECTIONS: Tuple[str, ...] = ("right", "down")  # directions that need line reversal

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)


class Game2048:
    """Core 2048 game mechanics on an NxN board (default 4×4).

    Attributes:
        size:     Side length of the square board.
        board:    2-D list of integers representing tile values (0 = empty).
        score:    Cumulative score for the current game.
        max_tile: Highest tile value currently on the board.
    """

    # ------------------------------------------------------------------
    # Construction / initialisation
    # ------------------------------------------------------------------

    def __init__(
        self,
        size: int = DEFAULT_BOARD_SIZE,
        board: Optional[List[List[int]]] = None,
        score: int = 0,
        max_tile: int = 0,
    ) -> None:
        """Initialise a new game or restore one from an existing state.

        Args:
            size:     Board side length (ignored when *board* is supplied).
            board:    Pre-existing board state.  When provided the game is
                      restored rather than started fresh.
            score:    Score to restore (only used together with *board*).
            max_tile: Max-tile hint to restore (only used together with *board*).
        """
        self.size = size

        if board is None:
            self._init_fresh_game()
        else:
            self._restore_game(board, score, max_tile)

    def _init_fresh_game(self) -> None:
        """Set up a brand-new game with an empty board and two starter tiles."""
        self.board = self._empty_board()
        self.score = 0
        self.max_tile = 0
        self.add_random_tile()
        self.add_random_tile()
        logger.debug("New game initialised (size=%d).", self.size)

    def _restore_game(
        self,
        board: List[List[int]],
        score: int,
        max_tile: int,
    ) -> None:
        """Restore game state from previously serialised data.

        Args:
            board:    Board to restore.
            score:    Score to restore.
            max_tile: Max-tile hint; the actual board maximum is also checked.
        """
        self.board = [row[:] for row in board]
        self.score = score
        # Ensure max_tile is consistent with the actual board contents.
        self.max_tile = max(max_tile, self.get_max_tile())
        logger.debug("Game restored (score=%d, max_tile=%d).", self.score, self.max_tile)

    # ------------------------------------------------------------------
    # Public game-control methods
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset the game to its initial state with two random starter tiles."""
        self._init_fresh_game()
        logger.info("Game reset.")

    def add_random_tile(self) -> bool:
        """Spawn a new tile on a random empty cell.

        The spawned value is :data:`TILE_VALUE_FOUR` with probability
        :data:`TILE_FOUR_PROBABILITY`, otherwise :data:`TILE_VALUE_TWO`.

        Returns:
            ``True`` if a tile was placed; ``False`` when the board is full.
        """
        empty_cells = self._get_empty_cells()
        if not empty_cells:
            logger.debug("add_random_tile: board is full, no tile added.")
            return False

        row, col = random.choice(empty_cells)
        value = self._choose_spawn_value()
        self.board[row][col] = value
        self._update_max_tile(value)
        logger.debug("Spawned tile %d at (%d, %d).", value, row, col)
        return True

    def move(self, direction: str) -> Tuple[bool, int]:
        """Execute a move in the requested direction.

        Args:
            direction: One of ``'up'``, ``'down'``, ``'left'``, ``'right'``.

        Returns:
            A ``(changed, gained_score)`` tuple where *changed* is ``True``
            when at least one tile moved or merged.
        """
        if direction not in VALID_DIRECTIONS:
            logger.warning("move: invalid direction '%s' ignored.", direction)
            return False, 0

        if direction in HORIZONTAL_DIRECTIONS:
            changed, gained_total = self._apply_move_to_rows(direction)
        else:
            changed, gained_total = self._apply_move_to_columns(direction)

        logger.debug(
            "Move '%s': changed=%s, gained=%d, score=%d.",
            direction, changed, gained_total, self.score,
        )
        return changed, gained_total

    # ------------------------------------------------------------------
    # Core line-processing logic
    # ------------------------------------------------------------------

    def move_line(self, line: List[int]) -> Tuple[List[int], int]:
        """Compress and merge a single line oriented towards the left.

        Non-zero tiles are shifted left, then adjacent equal tiles are merged
        (each pair only once per move).

        Args:
            line: A row or column of tile values.

        Returns:
            A ``(new_line, gained_score)`` tuple.

        Example::

            >>> game.move_line([2, 0, 2, 4])
            ([4, 4, 0, 0], 4)
        """
        compressed = self._compress_line(line)
        merged, gained = self._merge_line(compressed)
        padded = self._pad_line(merged)
        return padded, gained

    # ------------------------------------------------------------------
    # Game-state queries
    # ------------------------------------------------------------------

    def can_move(self) -> bool:
        """Return ``True`` if at least one valid move remains.

        A move is possible when there is an empty cell or two adjacent
        (horizontal or vertical) tiles share the same value.
        """
        return (
            self._has_empty_cell()
            or self._has_horizontal_merge()
            or self._has_vertical_merge()
        )

    def get_max_tile(self) -> int:
        """Return the highest tile value currently on the board.

        Returns:
            Maximum tile value, or ``0`` for an empty board.
        """
        return max(max(row) for row in self.board) if self.board else 0

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_state(self) -> Dict:
        """Serialise the current game state to a plain dictionary.

        Returns:
            A dictionary suitable for JSON serialisation or storage.
        """
        return {
            "size": self.size,
            "board": [row[:] for row in self.board],
            "score": self.score,
            "max_tile": self.max_tile,
        }

    @staticmethod
    def from_state(state: Dict) -> "Game2048":
        """Deserialise a :class:`Game2048` instance from a state dictionary.

        Args:
            state: Dictionary previously produced by :meth:`to_state`.

        Returns:
            A fully restored :class:`Game2048` instance.
        """
        size = state.get("size", DEFAULT_BOARD_SIZE)
        board = state.get("board", [[0] * size for _ in range(size)])
        score = state.get("score", 0)
        max_tile = state.get("max_tile", 0)
        return Game2048(size=size, board=board, score=score, max_tile=max_tile)

    # ------------------------------------------------------------------
    # Private helpers — board construction
    # ------------------------------------------------------------------

    def _empty_board(self) -> List[List[int]]:
        """Return a new all-zero board of the configured size."""
        return [[0] * self.size for _ in range(self.size)]

    # ------------------------------------------------------------------
    # Private helpers — tile spawning
    # ------------------------------------------------------------------

    def _get_empty_cells(self) -> List[Tuple[int, int]]:
        """Return a list of ``(row, col)`` coordinates for every empty cell."""
        return [
            (row, col)
            for row in range(self.size)
            for col in range(self.size)
            if self.board[row][col] == 0
        ]

    @staticmethod
    def _choose_spawn_value() -> int:
        """Return the value for a newly spawned tile.

        Returns:
            :data:`TILE_VALUE_FOUR` with probability
            :data:`TILE_FOUR_PROBABILITY`, otherwise :data:`TILE_VALUE_TWO`.
        """
        return TILE_VALUE_FOUR if random.random() < TILE_FOUR_PROBABILITY else TILE_VALUE_TWO

    def _update_max_tile(self, value: int) -> None:
        """Update :attr:`max_tile` if *value* exceeds the current maximum.

        Args:
            value: Tile value to compare against the current maximum.
        """
        if value > self.max_tile:
            self.max_tile = value

    # ------------------------------------------------------------------
    # Private helpers — move application
    # ------------------------------------------------------------------

    def _apply_move_to_rows(self, direction: str) -> Tuple[bool, int]:
        """Apply a horizontal move (left or right) to every row.

        Args:
            direction: ``'left'`` or ``'right'``.

        Returns:
            ``(changed, gained_total)`` aggregated across all rows.
        """
        changed = False
        gained_total = 0
        reverse = direction in REVERSE_DIRECTIONS

        for row_index in range(self.size):
            original_row = self.board[row_index][:]
            line = original_row[::-1] if reverse else original_row

            new_line, gained = self.move_line(line)

            if reverse:
                new_line = new_line[::-1]

            if new_line != self.board[row_index]:
                changed = True
                self.board[row_index] = new_line

            if gained:
                self.score += gained
                self._update_max_tile(max(new_line))
                gained_total += gained

        return changed, gained_total

    def _apply_move_to_columns(self, direction: str) -> Tuple[bool, int]:
        """Apply a vertical move (up or down) to every column.

        Args:
            direction: ``'up'`` or ``'down'``.

        Returns:
            ``(changed, gained_total)`` aggregated across all columns.
        """
        changed = False
        gained_total = 0
        reverse = direction in REVERSE_DIRECTIONS

        for col_index in range(self.size):
            # Extract the column as a list.
            col = [self.board[row_index][col_index] for row_index in range(self.size)]
            line = col[::-1] if reverse else col

            new_line, gained = self.move_line(line)

            if reverse:
                new_line = new_line[::-1]

            # Write the processed column back to the board.
            for row_index in range(self.size):
                if self.board[row_index][col_index] != new_line[row_index]:
                    changed = True
                    self.board[row_index][col_index] = new_line[row_index]

            if gained:
                self.score += gained
                self._update_max_tile(max(new_line))
                gained_total += gained

        return changed, gained_total

    # ------------------------------------------------------------------
    # Private helpers — line processing
    # ------------------------------------------------------------------

    @staticmethod
    def _compress_line(line: List[int]) -> List[int]:
        """Remove zeros from a line, shifting non-zero tiles to the left.

        Args:
            line: A row or column of tile values.

        Returns:
            A new list containing only the non-zero values.
        """
        return [tile for tile in line if tile != 0]

    @staticmethod
    def _merge_line(tiles: List[int]) -> Tuple[List[int], int]:
        """Merge adjacent equal tiles in a compressed (zero-free) line.

        Each tile can participate in at most one merge per call.  Merged
        tiles are doubled and the combined value is added to the score.

        Args:
            tiles: Zero-free list of tile values.

        Returns:
            A ``(merged_tiles, gained_score)`` tuple.
        """
        merged: List[int] = []
        gained = 0
        skip_next = False  # True when the next tile was already consumed by a merge

        for index in range(len(tiles)):
            if skip_next:
                skip_next = False
                continue

            next_index = index + 1
            tiles_can_merge = (
                next_index < len(tiles) and tiles[index] == tiles[next_index]
            )

            if tiles_can_merge:
                merged_value = tiles[index] * 2
                merged.append(merged_value)
                gained += merged_value
                skip_next = True  # consume the next tile
            else:
                merged.append(tiles[index])

        return merged, gained

    def _pad_line(self, tiles: List[int]) -> List[int]:
        """Pad a merged tile list with trailing zeros to restore full length.

        Args:
            tiles: Merged (and possibly shorter) list of tile values.

        Returns:
            A list of length :attr:`size` padded with zeros on the right.
        """
        padding_needed = self.size - len(tiles)
        return tiles + [0] * padding_needed

    # ------------------------------------------------------------------
    # Private helpers — can_move checks
    # ------------------------------------------------------------------

    def _has_empty_cell(self) -> bool:
        """Return ``True`` if the board contains at least one empty (zero) cell."""
        return any(
            self.board[row][col] == 0
            for row in range(self.size)
            for col in range(self.size)
        )

    def _has_horizontal_merge(self) -> bool:
        """Return ``True`` if any two horizontally adjacent tiles share a value."""
        return any(
            self.board[row][col] == self.board[row][col + 1]
            for row in range(self.size)
            for col in range(self.size - 1)
        )

    def _has_vertical_merge(self) -> bool:
        """Return ``True`` if any two vertically adjacent tiles share a value."""
        return any(
            self.board[row][col] == self.board[row + 1][col]
            for row in range(self.size - 1)
            for col in range(self.size)
        )
