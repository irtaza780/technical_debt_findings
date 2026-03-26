import logging
import random
import time
from typing import List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
GRID_SIZE = 9
BOX_SIZE = 3
MIN_VALUE = 1
MAX_VALUE = 9
EMPTY_CELL = 0
EASY_REMOVAL_MIN = 30
EASY_REMOVAL_MAX = 36
MEDIUM_REMOVAL_MIN = 40
MEDIUM_REMOVAL_MAX = 48
HARD_REMOVAL_MIN = 50
HARD_REMOVAL_MAX = 58
MIN_REMOVALS_FALLBACK = 20
DEFAULT_MAX_TIME = 3.0

Grid = List[List[int]]


class SudokuBoard:
    """
    Represents a 9x9 Sudoku board and provides solving and generation utilities.
    Empty cells are denoted by 0.
    """

    def __init__(self, grid: Optional[Grid] = None):
        """
        Initialize a Sudoku board.

        Args:
            grid: Optional 9x9 list of lists. If None, creates an empty board.

        Raises:
            ValueError: If grid is not a valid 9x9 structure.
        """
        if grid is None:
            self.grid = [[EMPTY_CELL for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        else:
            self._validate_grid(grid)
            self.grid = [[int(x) for x in row] for row in grid]

    @staticmethod
    def _validate_grid(grid: Grid) -> None:
        """
        Validate that grid is a proper 9x9 structure.

        Args:
            grid: Grid to validate.

        Raises:
            ValueError: If grid structure is invalid.
        """
        if not isinstance(grid, list) or len(grid) != GRID_SIZE:
            raise ValueError(f"Grid must be a {GRID_SIZE}x{GRID_SIZE} list of lists.")
        if any(not isinstance(row, list) or len(row) != GRID_SIZE for row in grid):
            raise ValueError(f"Grid must be a {GRID_SIZE}x{GRID_SIZE} list of lists.")

    def copy(self) -> "SudokuBoard":
        """
        Create a deep copy of the board.

        Returns:
            A new SudokuBoard instance with copied grid data.
        """
        return SudokuBoard([row[:] for row in self.grid])

    def to_list(self) -> Grid:
        """
        Export board as a list-of-lists representation.

        Returns:
            A deep copy of the grid.
        """
        return [row[:] for row in self.grid]

    def set_value(self, row: int, col: int, num: int) -> None:
        """
        Set a value at the specified cell.

        Args:
            row: Row index (0-8).
            col: Column index (0-8).
            num: Value to set (0-9).
        """
        self.grid[row][col] = num

    def clear_value(self, row: int, col: int) -> None:
        """
        Clear a cell to empty (0).

        Args:
            row: Row index (0-8).
            col: Column index (0-8).
        """
        self.grid[row][col] = EMPTY_CELL

    def find_empty(self, grid: Optional[Grid] = None) -> Optional[Tuple[int, int]]:
        """
        Find the next empty cell in the grid.

        Args:
            grid: Optional grid to search. If None, uses self.grid.

        Returns:
            Tuple of (row, col) for first empty cell, or None if none exist.
        """
        target_grid = self.grid if grid is None else grid
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if target_grid[row][col] == EMPTY_CELL:
                    return row, col
        return None

    def is_complete(self, grid: Optional[Grid] = None) -> bool:
        """
        Check if the grid has no empty cells.

        Args:
            grid: Optional grid to check. If None, uses self.grid.

        Returns:
            True if all cells are filled, False otherwise.
        """
        target_grid = self.grid if grid is None else grid
        return all(all(val != EMPTY_CELL for val in row) for row in target_grid)

    def is_solved(self, solution: Grid) -> bool:
        """
        Check if current board matches the provided solution.

        Args:
            solution: Solution grid to compare against.

        Returns:
            True if grids are identical, False otherwise.
        """
        return self.grid == solution

    def _is_valid_in_row(self, num: int, row: int, col: int, grid: Grid) -> bool:
        """
        Check if num is valid in the given row.

        Args:
            num: Number to check (1-9).
            row: Row index.
            col: Column index (to exclude current cell).
            grid: Grid to check against.

        Returns:
            True if num doesn't exist elsewhere in row.
        """
        for c in range(GRID_SIZE):
            if c != col and grid[row][c] == num:
                return False
        return True

    def _is_valid_in_column(self, num: int, row: int, col: int, grid: Grid) -> bool:
        """
        Check if num is valid in the given column.

        Args:
            num: Number to check (1-9).
            row: Row index (to exclude current cell).
            col: Column index.
            grid: Grid to check against.

        Returns:
            True if num doesn't exist elsewhere in column.
        """
        for r in range(GRID_SIZE):
            if r != row and grid[r][col] == num:
                return False
        return True

    def _is_valid_in_box(self, num: int, row: int, col: int, grid: Grid) -> bool:
        """
        Check if num is valid in the 3x3 box containing (row, col).

        Args:
            num: Number to check (1-9).
            row: Row index.
            col: Column index.
            grid: Grid to check against.

        Returns:
            True if num doesn't exist elsewhere in the 3x3 box.
        """
        # Calculate top-left corner of the 3x3 box
        box_row = (row // BOX_SIZE) * BOX_SIZE
        box_col = (col // BOX_SIZE) * BOX_SIZE

        for r in range(box_row, box_row + BOX_SIZE):
            for c in range(box_col, box_col + BOX_SIZE):
                if (r != row or c != col) and grid[r][c] == num:
                    return False
        return True

    def is_valid(self, num: int, row: int, col: int, grid: Optional[Grid] = None) -> bool:
        """
        Check if placing num at (row, col) satisfies all Sudoku rules.

        Args:
            num: Number to place (0-9, where 0 is always valid).
            row: Row index (0-8).
            col: Column index (0-8).
            grid: Optional grid to check. If None, uses self.grid.

        Returns:
            True if placement is valid, False otherwise.
        """
        if num == EMPTY_CELL:
            return True
        if num < MIN_VALUE or num > MAX_VALUE:
            return False

        target_grid = self.grid if grid is None else grid

        # Check row, column, and 3x3 box constraints
        return (
            self._is_valid_in_row(num, row, col, target_grid)
            and self._is_valid_in_column(num, row, col, target_grid)
            and self._is_valid_in_box(num, row, col, target_grid)
        )

    def solve(self, grid: Optional[Grid] = None) -> bool:
        """
        Solve the Sudoku using backtracking algorithm.

        Args:
            grid: Optional grid to solve in-place. If None, uses self.grid.

        Returns:
            True if puzzle is solvable, False otherwise.
        """
        target_grid = self.grid if grid is None else grid
        empty_cell = self.find_empty(target_grid)

        if not empty_cell:
            return True

        row, col = empty_cell
        # Try each number 1-9
        for num in range(MIN_VALUE, MAX_VALUE + 1):
            if self.is_valid(num, row, col, target_grid):
                target_grid[row][col] = num
                if self.solve(target_grid):
                    return True
                # Backtrack
                target_grid[row][col] = EMPTY_CELL

        return False

    def count_solutions(self, grid: Optional[Grid] = None, max_solutions: int = 2) -> int:
        """
        Count the number of solutions up to max_solutions using backtracking.

        Args:
            grid: Optional grid to analyze. If None, uses self.grid.
            max_solutions: Stop counting after reaching this number.

        Returns:
            Number of solutions found (capped at max_solutions).
        """
        target_grid = self.grid if grid is None else grid
        solution_count = [0]  # Use list to allow modification in nested function

        def backtrack() -> None:
            """Recursively count solutions with early termination."""
            if solution_count[0] >= max_solutions:
                return

            empty_cell = self.find_empty(target_grid)
            if not empty_cell:
                solution_count[0] += 1
                return

            row, col = empty_cell
            for num in range(MIN_VALUE, MAX_VALUE + 1):
                if self.is_valid(num, row, col, target_grid):
                    target_grid[row][col] = num
                    backtrack()
                    target_grid[row][col] = EMPTY_CELL

        backtrack()
        return solution_count[0]

    def generate_full(self) -> Grid:
        """
        Generate a complete valid Sudoku solution using randomized backtracking.

        Returns:
            A solved 9x9 grid.
        """
        full_grid = [[EMPTY_CELL] * GRID_SIZE for _ in range(GRID_SIZE)]

        def fill_grid() -> bool:
            """Recursively fill grid with random valid placements."""
            empty_cell = self.find_empty(full_grid)
            if not empty_cell:
                return True

            row, col = empty_cell
            # Randomize order of numbers to try
            numbers = list(range(MIN_VALUE, MAX_VALUE + 1))
            random.shuffle(numbers)

            for num in numbers:
                if self.is_valid(num, row, col, full_grid):
                    full_grid[row][col] = num
                    if fill_grid():
                        return True
                    # Backtrack
                    full_grid[row][col] = EMPTY_CELL

            return False

        fill_grid()
        self.grid = full_grid
        return self.to_list()

    def _get_removal_target(self, difficulty: str) -> int:
        """
        Determine the target number of cells to remove based on difficulty.

        Args:
            difficulty: One of 'easy', 'medium', or 'hard'.

        Returns:
            Target number of cells to remove.
        """
        difficulty = (difficulty or "medium").lower()
        if difficulty == "easy":
            return random.randint(EASY_REMOVAL_MIN, EASY_REMOVAL_MAX)
        elif difficulty == "hard":
            return random.randint(HARD_REMOVAL_MIN, HARD_REMOVAL_MAX)
        else:
            return random.randint(MEDIUM_REMOVAL_MIN, MEDIUM_REMOVAL_MAX)

    def generate_puzzle(
        self, difficulty: str = "medium", max_time: float = DEFAULT_MAX_TIME
    ) -> Tuple[Grid, Grid]:
        """
        Generate a Sudoku puzzle with a unique solution.

        Args:
            difficulty: Puzzle difficulty ('easy', 'medium', 'hard').
            max_time: Maximum time in seconds to spend ensuring uniqueness.

        Returns:
            Tuple of (puzzle, solution) grids.
        """
        # Generate a complete valid solution
        solution = self.generate_full()
        target_removals = self._get_removal_target(difficulty)

        # Start with full solution and remove cells
        puzzle = [row[:] for row in solution]
        cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
        random.shuffle(cells)

        removed_count = 0
        start_time = time.time()

        # Attempt to remove cells while preserving unique solution
        for row, col in cells:
            # Check time budget
            if time.time() - start_time > max_time:
                logger.warning("Time budget exceeded during puzzle generation")
                break

            if puzzle[row][col] == EMPTY_CELL:
                continue

            saved_value = puzzle[row][col]
            puzzle[row][col] = EMPTY_CELL

            # Verify uniqueness of solution
            test_grid = [row[:] for row in puzzle]
            solution_count = self.count_solutions(test_grid, max_solutions=2)

            if solution_count != 1:
                # Not unique, restore the cell
                puzzle[row][col] = saved_value
            else:
                removed_count += 1
                if removed_count >= target_removals:
                    break

        # Fallback if insufficient removals
        if removed_count < MIN_REMOVALS_FALLBACK:
            logger.info("Insufficient removals; using sample puzzle")
            return get_sample_puzzle()

        return puzzle, solution


def get_sample_puzzle() -> Tuple[Grid, Grid]:
    """
    Provide a predefined puzzle/solution pair as a reliable fallback.

    Returns:
        Tuple of (puzzle, solution) grids.
    """
    puzzle = [
        [0, 0, 0, 2, 6, 0, 7, 0, 1],
        [6, 8, 0, 0, 7, 0, 0, 9, 0],
        [1, 9, 0, 0, 0, 4, 5, 0, 0],
        [8, 2, 0, 1, 0, 0, 0, 4, 0],
        [0, 0, 4, 6, 0, 2, 9, 0, 0],
        [0, 5, 0, 0, 0, 3, 0, 2, 8],
        [0, 0, 9, 3, 0, 0, 0, 7, 4],
        [0, 4, 0, 0, 5, 0, 0, 3, 6],
        [7, 0, 3, 0, 1, 8, 0, 0, 0],
    ]
    solution = [
        [4, 3, 5, 2, 6, 9, 7, 8, 1],
        [6, 8, 2, 5, 7, 1, 4, 9, 3],
        [1, 9, 7, 8, 3, 4, 5, 6, 2],
        [8, 2, 6, 1, 9, 5, 3, 4, 7],
        [3, 7, 4, 6, 8, 2, 9, 1, 5],
        [9, 5, 1, 7, 4, 3, 6, 2, 8],
        [5, 1, 9, 3, 2, 6, 8, 7, 4],
        [2, 4, 8, 9, 5, 7, 1, 3, 6],
        [7, 6, 3, 4, 1, 8, 