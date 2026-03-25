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
EASY_REMOVAL_RANGE = (30, 36)
MEDIUM_REMOVAL_RANGE = (40, 48)
HARD_REMOVAL_RANGE = (50, 58)
MIN_REMOVALS_FALLBACK = 20
DEFAULT_MAX_TIME = 3.0
DEFAULT_DIFFICULTY = "medium"

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
        Export board as a list-of-lists.

        Returns:
            A copy of the internal grid representation.
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
        Check if num already exists in the row (excluding current cell).

        Args:
            num: Number to check.
            row: Row index.
            col: Column index.
            grid: Grid to check against.

        Returns:
            True if num is not in row, False otherwise.
        """
        for c in range(GRID_SIZE):
            if c != col and grid[row][c] == num:
                return False
        return True

    def _is_valid_in_column(self, num: int, row: int, col: int, grid: Grid) -> bool:
        """
        Check if num already exists in the column (excluding current cell).

        Args:
            num: Number to check.
            row: Row index.
            col: Column index.
            grid: Grid to check against.

        Returns:
            True if num is not in column, False otherwise.
        """
        for r in range(GRID_SIZE):
            if r != row and grid[r][col] == num:
                return False
        return True

    def _is_valid_in_box(self, num: int, row: int, col: int, grid: Grid) -> bool:
        """
        Check if num already exists in the 3x3 box (excluding current cell).

        Args:
            num: Number to check.
            row: Row index.
            col: Column index.
            grid: Grid to check against.

        Returns:
            True if num is not in box, False otherwise.
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
        Check if placing num at (row, col) satisfies all Sudoku constraints.

        Args:
            num: Number to validate (1-9, or 0 for empty).
            row: Row index (0-8).
            col: Column index (0-8).
            grid: Optional grid to validate against. If None, uses self.grid.

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
            grid: Optional grid to solve in-place. If None, solves self.grid.

        Returns:
            True if puzzle is solvable, False otherwise.
        """
        target_grid = self.grid if grid is None else grid
        empty_cell = self.find_empty(target_grid)

        if not empty_cell:
            return True

        row, col = empty_cell
        # Try numbers in order for deterministic solving
        for num in range(MIN_VALUE, MAX_VALUE + 1):
            if self.is_valid(num, row, col, target_grid):
                target_grid[row][col] = num
                if self.solve(target_grid):
                    return True
                target_grid[row][col] = EMPTY_CELL

        return False

    def count_solutions(self, grid: Optional[Grid] = None, max_solutions: int = 2) -> int:
        """
        Count the number of solutions for a puzzle up to a maximum.

        Uses backtracking with early termination when max_solutions is reached.

        Args:
            grid: Optional grid to analyze. If None, uses self.grid.
            max_solutions: Maximum solutions to count before stopping.

        Returns:
            Number of solutions found (capped at max_solutions).
        """
        target_grid = self.grid if grid is None else grid
        solution_count = [0]  # Use list to allow modification in nested function

        def backtrack() -> None:
            """Recursively count solutions via backtracking."""
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

    def _fill_grid_randomly(self, grid: Grid) -> bool:
        """
        Fill an empty grid with a valid solution using randomized backtracking.

        Args:
            grid: Empty grid to fill in-place.

        Returns:
            True if successfully filled, False otherwise.
        """
        empty_cell = self.find_empty(grid)
        if not empty_cell:
            return True

        row, col = empty_cell
        # Randomize number order for variety
        numbers = list(range(MIN_VALUE, MAX_VALUE + 1))
        random.shuffle(numbers)

        for num in numbers:
            if self.is_valid(num, row, col, grid):
                grid[row][col] = num
                if self._fill_grid_randomly(grid):
                    return True
                grid[row][col] = EMPTY_CELL

        return False

    def generate_full(self) -> Grid:
        """
        Generate a complete valid Sudoku solution.

        Uses randomized backtracking to create variety.

        Returns:
            A solved 9x9 grid.
        """
        new_grid = [[EMPTY_CELL] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._fill_grid_randomly(new_grid)
        self.grid = new_grid
        return self.to_list()

    def _get_removal_target(self, difficulty: str) -> int:
        """
        Determine the target number of cells to remove based on difficulty.

        Args:
            difficulty: One of 'easy', 'medium', or 'hard'.

        Returns:
            Target number of cells to remove.
        """
        difficulty = (difficulty or DEFAULT_DIFFICULTY).lower()
        if difficulty == "easy":
            return random.randint(*EASY_REMOVAL_RANGE)
        elif difficulty == "hard":
            return random.randint(*HARD_REMOVAL_RANGE)
        else:
            return random.randint(*MEDIUM_REMOVAL_RANGE)

    def _attempt_cell_removal(self, puzzle: Grid, solution: Grid, row: int, col: int) -> bool:
        """
        Attempt to remove a cell from the puzzle while maintaining unique solution.

        Args:
            puzzle: Puzzle grid to modify.
            solution: Known solution grid.
            row: Row of cell to remove.
            col: Column of cell to remove.

        Returns:
            True if cell was successfully removed, False if removal breaks uniqueness.
        """
        if puzzle[row][col] == EMPTY_CELL:
            return False

        saved_value = puzzle[row][col]
        puzzle[row][col] = EMPTY_CELL

        # Check if puzzle still has unique solution
        test_grid = [row[:] for row in puzzle]
        solution_count = self.count_solutions(test_grid, max_solutions=2)

        if solution_count != 1:
            # Restore value if uniqueness is lost
            puzzle[row][col] = saved_value
            return False

        return True

    def generate_puzzle(
        self, difficulty: str = DEFAULT_DIFFICULTY, max_time: float = DEFAULT_MAX_TIME
    ) -> Tuple[Grid, Grid]:
        """
        Generate a Sudoku puzzle with a unique solution.

        Strategy:
        1. Generate a complete valid solution.
        2. Randomly remove cells while preserving uniqueness.
        3. Stop when target removals reached or time budget exceeded.
        4. Fall back to sample puzzle if insufficient removals achieved.

        Args:
            difficulty: Puzzle difficulty ('easy', 'medium', 'hard').
            max_time: Maximum time in seconds to spend on uniqueness checks.

        Returns:
            Tuple of (puzzle_grid, solution_grid).
        """
        # Generate complete solution
        solution = self.generate_full()
        target_removals = self._get_removal_target(difficulty)

        # Create puzzle as copy of solution
        puzzle = [row[:] for row in solution]

        # Shuffle cell indices for random removal order
        cell_indices = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
        random.shuffle(cell_indices)

        removed_count = 0
        start_time = time.time()

        # Attempt to remove cells
        for row, col in cell_indices:
            # Check time budget
            if time.time() - start_time > max_time:
                logger.warning("Puzzle generation time budget exceeded; using current puzzle")
                break

            if self._attempt_cell_removal(puzzle, solution, row, col):
                removed_count += 1
                if removed_count >= target_removals:
                    break

        # Fallback if insufficient removals
        if removed_count < MIN_REMOVALS_FALLBACK:
            logger.warning(
                f"Only {removed_count} cells removed; using sample puzzle as fallback"
            )
            return get_sample_puzzle()

        return puzzle, solution


def get_sample_puzzle() -> Tuple[Grid, Grid]:
    """
    Provide a predefined puzzle and solution as a reliable fallback.

    Returns:
        Tuple of (puzzle_grid, solution_grid).
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
        [4, 3, 5