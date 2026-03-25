import logging
from dataclasses import dataclass
from typing import List, Tuple, Set, Optional
import random
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MIN_BOARD_DIMENSION = 1
MINE_SENTINEL_VALUE = -1
NEIGHBOR_OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
GAME_STATE_PLAYING = "playing"
GAME_STATE_WON = "won"
GAME_STATE_LOST = "lost"
REVEAL_RESULT_HIT_MINE = "hit_mine"
REVEAL_RESULT_REVEALED = "revealed"
REVEAL_RESULT_IGNORE = "ignore"
REVEAL_RESULT_OK = "ok"
LEFT_CLICK_RESULT_LOST = "lost"
LEFT_CLICK_RESULT_WON = "won"


@dataclass
class Cell:
    """
    Represents a single cell in the Minesweeper grid.
    
    Attributes:
        has_mine: Whether this cell contains a mine.
        revealed: Whether this cell has been revealed to the player.
        flagged: Whether this cell has been flagged by the player.
        adjacent: Number of adjacent mines (-1 if this cell has a mine).
    """
    has_mine: bool = False
    revealed: bool = False
    flagged: bool = False
    adjacent: int = 0


class Board:
    """
    Encapsulates the Minesweeper board: cells, mine placement, and reveal/flag logic.
    
    Attributes:
        width: Number of columns in the board.
        height: Number of rows in the board.
        num_mines: Total number of mines to place on the board.
        grid: 2D list of Cell objects.
        mines_placed: Whether mines have been placed on the board.
    """
    
    def __init__(self, width: int, height: int, num_mines: int):
        """
        Initialize a Minesweeper board.
        
        Args:
            width: Number of columns (must be positive).
            height: Number of rows (must be positive).
            num_mines: Number of mines to place (must be between 1 and width*height-1).
            
        Raises:
            ValueError: If dimensions are invalid or mine count is out of range.
        """
        self._validate_board_parameters(width, height, num_mines)
        self.width = width
        self.height = height
        self.num_mines = num_mines
        self.grid: List[List[Cell]] = self._create_empty_grid()
        self.mines_placed = False

    @staticmethod
    def _validate_board_parameters(width: int, height: int, num_mines: int) -> None:
        """
        Validate board initialization parameters.
        
        Args:
            width: Board width.
            height: Board height.
            num_mines: Number of mines.
            
        Raises:
            ValueError: If any parameter is invalid.
        """
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive.")
        total_cells = width * height
        if not (0 < num_mines < total_cells):
            raise ValueError(f"Number of mines must be between 1 and {total_cells - 1}.")

    def _create_empty_grid(self) -> List[List[Cell]]:
        """
        Create an empty grid of cells.
        
        Returns:
            A 2D list of Cell objects with default values.
        """
        return [[Cell() for _ in range(self.width)] for _ in range(self.height)]

    def reset(self) -> None:
        """Reset the board to its initial empty state."""
        self.grid = self._create_empty_grid()
        self.mines_placed = False
        logger.info("Board reset to initial state")

    def in_bounds(self, x: int, y: int) -> bool:
        """
        Check if coordinates are within board boundaries.
        
        Args:
            x: Column coordinate.
            y: Row coordinate.
            
        Returns:
            True if coordinates are valid, False otherwise.
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """
        Get all valid neighboring cell coordinates for a given cell.
        
        Args:
            x: Column coordinate.
            y: Row coordinate.
            
        Yields:
            Tuples of (x, y) for each valid neighbor.
        """
        for dx, dy in NEIGHBOR_OFFSETS:
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny):
                yield nx, ny

    def place_mines(self, first_click: Tuple[int, int]) -> None:
        """
        Randomly place mines across the board, avoiding the first clicked cell.
        
        Args:
            first_click: Coordinates of the first clicked cell (must be safe).
            
        Raises:
            ValueError: If too many mines are requested for the board.
        """
        all_cells = [(x, y) for y in range(self.height) for x in range(self.width)]
        
        # Exclude the first clicked cell to ensure it's always safe
        if first_click in all_cells:
            all_cells.remove(first_click)
        
        if self.num_mines > len(all_cells):
            raise ValueError("Too many mines for the board configuration.")
        
        mine_positions = set(random.sample(all_cells, self.num_mines))
        for mx, my in mine_positions:
            self.grid[my][mx].has_mine = True
        
        self._compute_adjacents()
        self.mines_placed = True
        logger.info(f"Placed {self.num_mines} mines on {self.width}x{self.height} board")

    def _compute_adjacents(self) -> None:
        """
        Compute the number of adjacent mines for each non-mine cell.
        Mine cells are marked with adjacent = -1.
        """
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                if cell.has_mine:
                    cell.adjacent = MINE_SENTINEL_VALUE
                else:
                    # Count neighboring mines
                    mine_count = sum(
                        1 for nx, ny in self.neighbors(x, y)
                        if self.grid[ny][nx].has_mine
                    )
                    cell.adjacent = mine_count

    def reveal(
        self,
        x: int,
        y: int,
        first_click: Optional[Tuple[int, int]] = None
    ) -> Tuple[str, Set[Tuple[int, int]], Optional[Tuple[int, int]]]:
        """
        Reveal the cell at (x, y).
        
        Args:
            x: Column coordinate.
            y: Row coordinate.
            first_click: Coordinates of first click (triggers mine placement if provided).
            
        Returns:
            Tuple of (result, changed_cells, exploded_at):
            - result: 'hit_mine', 'revealed', or 'ignore'
            - changed_cells: Set of coordinates that changed visibility
            - exploded_at: (x, y) if a mine was hit, else None
        """
        if not self.in_bounds(x, y):
            return REVEAL_RESULT_IGNORE, set(), None
        
        # Place mines on first reveal if not already placed
        if not self.mines_placed:
            if first_click is None:
                first_click = (x, y)
            self.place_mines(first_click)
        
        cell = self.grid[y][x]
        
        # Cannot reveal flagged or already revealed cells
        if cell.flagged or cell.revealed:
            return REVEAL_RESULT_IGNORE, set(), None
        
        # Hit a mine
        if cell.has_mine:
            cell.revealed = True
            logger.warning(f"Mine hit at ({x}, {y})")
            return REVEAL_RESULT_HIT_MINE, {(x, y)}, (x, y)
        
        # Reveal safe cell(s) using flood fill
        changed = set()
        self._flood_reveal(x, y, changed)
        return REVEAL_RESULT_REVEALED, changed, None

    def _flood_reveal(self, x: int, y: int, changed: Set[Tuple[int, int]]) -> None:
        """
        Reveal cells using depth-first search flood fill.
        Reveals all zero-adjacent cells and their borders.
        
        Args:
            x: Starting column coordinate.
            y: Starting row coordinate.
            changed: Set to accumulate changed cell coordinates.
        """
        stack = [(x, y)]
        
        while stack:
            cx, cy = stack.pop()
            
            if not self.in_bounds(cx, cy):
                continue
            
            cell = self.grid[cy][cx]
            
            # Skip already processed cells
            if cell.revealed or cell.flagged:
                continue
            
            cell.revealed = True
            changed.add((cx, cy))
            
            # Continue flood fill only from zero-adjacent cells
            if cell.adjacent == 0 and not cell.has_mine:
                for nx, ny in self.neighbors(cx, cy):
                    ncell = self.grid[ny][nx]
                    if not ncell.revealed and not ncell.flagged and (nx, ny) not in changed:
                        stack.append((nx, ny))

    def toggle_flag(self, x: int, y: int) -> bool:
        """
        Toggle a flag on the cell at (x, y).
        
        Args:
            x: Column coordinate.
            y: Row coordinate.
            
        Returns:
            The new flagged state of the cell, or False if cell is out of bounds or revealed.
        """
        if not self.in_bounds(x, y):
            return False
        
        cell = self.grid[y][x]
        
        # Cannot flag revealed cells
        if cell.revealed:
            return cell.flagged
        
        cell.flagged = not cell.flagged
        return cell.flagged

    def reveal_all_mines(self) -> Set[Tuple[int, int]]:
        """
        Reveal all mines on the board.
        
        Returns:
            Set of coordinates that were changed (mines not previously revealed).
        """
        changed = set()
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                if cell.has_mine and not cell.revealed:
                    cell.revealed = True
                    changed.add((x, y))
        return changed

    def all_safe_cells_revealed(self) -> bool:
        """
        Check if all non-mine cells have been revealed.
        
        Returns:
            True if all safe cells are revealed, False otherwise.
        """
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                if not cell.has_mine and not cell.revealed:
                    return False
        return True

    def get_cell(self, x: int, y: int) -> Cell:
        """
        Get the cell at the specified coordinates.
        
        Args:
            x: Column coordinate.
            y: Row coordinate.
            
        Returns:
            The Cell object at (x, y).
        """
        return self.grid[y][x]

    def flag_count(self) -> int:
        """
        Count the number of currently flagged cells.
        
        Returns:
            Number of flagged cells on the board.
        """
        return sum(
            1 for y in range(self.height)
            for x in range(self.width)
            if self.grid[y][x].flagged
        )


class MinesweeperGame:
    """
    High-level game controller: manages state, integrates Board with timer and win/loss logic.
    
    Attributes:
        board: The underlying Board instance.
        state: Current game state ('playing', 'won', or 'lost').
        start_time: Timestamp when the game started.
        end_time: Timestamp when the game ended.
        started: Whether the game has been started.
        exploded_at: Coordinates of the mine that was hit, if any.
    """
    
    def __init__(self, width: int, height: int, mines: int):
        """
        Initialize a Minesweeper game.
        
        Args:
            width: Board width.
            height: Board height.
            mines: Number of mines.
        """
        self.board = Board(width, height, mines)
        self.state = GAME_STATE_PLAYING
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.started = False
        self.exploded_at: Optional[Tuple[int, int]] = None

    def left_click(self, x: int, y: int) -> Tuple[str, Set[Tuple[int, int]], Optional[Tuple[int, int]]]:
        """
        Handle a left-click at (x, y).
        
        Args:
            x: Column coordinate.
            y: Row coordinate.
            
        Returns:
            Tuple of (result, changed_cells, exploded_at):
            - result: 'ok', 'won', 'lost', or 'ignore'
            - changed_cells: Set of coordinates that changed visibility
            - exploded_at: (x, y) if a mine was hit, else None
        """
        if self.state != GAME_STATE_PLAYING:
            return REVEAL_RESULT_IGNORE, set(), None
        
        # Initialize game on first click
        first_click = None
        if not self.board.mines_placed:
            first_click = (x, y)
            self.started = True
            self.start_time = time.time()
            logger.info(f"Game started with first click at ({x}, {y})")
        
        result, changed, exploded_at = self.board.reveal(x, y, first_click=first_click)
        
        # Handle mine hit
        if result == REVEAL_RESULT_HIT_MINE:
            self.state = GAME_STATE_LOST
            self.exploded_at = exploded_at
            self.end_time = time.time()
            # Reveal all remaining mines
            changed |= self.board.reveal_all_mines()
            logger.info(f"Game lost at ({x}, {y})")
            return LEFT_CLICK_RESULT_LOST, changed, exploded_at
        
        # Check for win condition
        if self.board.all_safe_cells_revealed():
            self.state = GAME_STATE_WON
            self.end_time = time.time()
            logger.info("Game won!")
            return LEFT_CLICK_RESULT_WON, changed, None
        
        # Normal reveal
        if result == REVEAL_RESULT_REVEALED:
            return REVEAL_RESULT_OK, changed, None
        
        return REVEAL_RESULT_IGNORE, set(), None

    def right_click(self, x: int, y: int) -> bool:
        """
        Handle a right-click at (x, y) to toggle a flag.
        
        Args:
            x: Column coordinate.
            y: Row coordinate.
            
        Returns:
            The new flagged state of the cell.
        """
        if self.state != GAME_STATE_PLAYING:
            return False
        
        flagged = self.board.toggle_flag(x, y)
        return flagged

    def elapsed_time(self) -> float:
        """
        Get the elapsed time since game start.
        Time is frozen when the game ends.
        
        Returns:
            Elapsed time in seconds.
        """
        if not self.started or self.start_time is None:
            return 0.0
        
        # Freeze time at game end
        if self.state in (GAME_STATE_WON, GAME_STATE_LOST):