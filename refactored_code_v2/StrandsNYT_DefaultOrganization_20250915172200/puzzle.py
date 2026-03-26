import logging
from typing import List, Tuple, Dict, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type aliases
Coord = Tuple[int, int]

# Grid dimensions
DEFAULT_ROWS = 6
DEFAULT_COLS = 8

# Adjacency constants
MAX_ADJACENCY_DISTANCE = 1
ADJACENCY_DIRECTIONS = 8  # 8-directional adjacency


class Puzzle:
    """
    Represents a Strands-like word puzzle with a spangram and themed words.
    
    The puzzle consists of a grid where all cells are covered exactly once by
    solution paths (spangram + theme words) with no overlaps.
    """

    def __init__(
        self,
        rows: int,
        cols: int,
        grid: List[List[str]],
        theme: str,
        spangram: str,
        spangram_path: List[Coord],
        word_paths: Dict[str, List[Coord]],
    ):
        """
        Initialize a puzzle instance.
        
        Args:
            rows: Number of rows in the grid
            cols: Number of columns in the grid
            grid: 2D list of letters
            theme: Theme description for the puzzle
            spangram: The spangram word that spans the puzzle
            spangram_path: List of coordinates forming the spangram path
            word_paths: Dictionary mapping words to their coordinate paths
        """
        self.rows = rows
        self.cols = cols
        self.grid = grid
        self.theme = theme
        self.spangram = spangram
        self.spangram_path = spangram_path
        self.word_paths = word_paths
        # Build theme words list from word_paths excluding spangram
        self.theme_words = [w for w in word_paths.keys() if w != spangram]
        self.validate_integrity()

    def get_letter(self, row: int, col: int) -> str:
        """
        Retrieve a letter from the grid at the specified coordinates.
        
        Args:
            row: Row index
            col: Column index
            
        Returns:
            The letter at the given position
        """
        return self.grid[row][col]

    def all_solution_cells(self) -> Set[Coord]:
        """
        Get all cells that are part of any solution path.
        
        Returns:
            Set of coordinates covered by spangram and theme words
        """
        cells = set()
        cells.update(self.spangram_path)
        for word in self.theme_words:
            cells.update(self.word_paths[word])
        return cells

    def _validate_grid_dimensions(self) -> None:
        """Validate that grid dimensions match declared rows and columns."""
        if len(self.grid) != self.rows:
            raise AssertionError(f"Grid has {len(self.grid)} rows, expected {self.rows}")
        
        for row_idx, row in enumerate(self.grid):
            if len(row) != self.cols:
                raise AssertionError(
                    f"Row {row_idx} has {len(row)} columns, expected {self.cols}"
                )

    def _validate_spangram_path(self) -> None:
        """Validate that the spangram path spells the correct word."""
        spelled = "".join(self.get_letter(r, c) for (r, c) in self.spangram_path)
        if spelled != self.spangram:
            raise AssertionError(
                f"Spangram path does not spell '{self.spangram}', got '{spelled}'"
            )

    def _validate_word_paths(self, used_cells: Set[Coord]) -> None:
        """
        Validate that each word path spells the correct word and has no overlaps.
        
        Args:
            used_cells: Set to accumulate all used cells (modified in place)
            
        Raises:
            AssertionError: If any word path is invalid or overlaps
        """
        for word, path in self.word_paths.items():
            if word == self.spangram:
                continue
            
            # Verify path spells the word
            spelled = "".join(self.get_letter(r, c) for (r, c) in path)
            if spelled != word:
                raise AssertionError(
                    f"Path for '{word}' does not match letters (got '{spelled}')"
                )
            
            # Check for overlaps with previously used cells
            for coord in path:
                if coord in used_cells:
                    raise AssertionError(f"Overlap detected for word '{word}' at {coord}")
                used_cells.add(coord)

    def _validate_complete_coverage(self, used_cells: Set[Coord]) -> None:
        """
        Validate that all cells in the grid are covered exactly once.
        
        Args:
            used_cells: Set of all used cells
            
        Raises:
            AssertionError: If not all cells are covered
        """
        total_cells = self.rows * self.cols
        if len(used_cells) != total_cells:
            raise AssertionError(
                f"Not all cells are used (used {len(used_cells)} of {total_cells})"
            )

    @staticmethod
    def _are_adjacent(coord_a: Coord, coord_b: Coord) -> bool:
        """
        Check if two coordinates are adjacent (8-directional).
        
        Args:
            coord_a: First coordinate
            coord_b: Second coordinate
            
        Returns:
            True if coordinates are adjacent, False otherwise
        """
        row_diff = abs(coord_a[0] - coord_b[0])
        col_diff = abs(coord_a[1] - coord_b[1])
        # Chebyshev distance of 1 means adjacent in 8 directions
        return max(row_diff, col_diff) == MAX_ADJACENCY_DISTANCE

    def _validate_path_adjacency(self, path: List[Coord], word: str) -> None:
        """
        Validate that all consecutive steps in a path are adjacent.
        
        Args:
            path: List of coordinates forming the path
            word: Word name for error messages
            
        Raises:
            AssertionError: If any consecutive steps are not adjacent
        """
        for i in range(1, len(path)):
            if not self._are_adjacent(path[i - 1], path[i]):
                raise AssertionError(
                    f"Non-adjacent step in path for '{word}' "
                    f"between {path[i-1]} and {path[i]}"
                )

    def validate_integrity(self) -> None:
        """
        Perform comprehensive validation of puzzle integrity.
        
        Checks:
        - Grid dimensions match declared size
        - Spangram path spells the spangram word
        - All word paths spell their respective words
        - No overlaps between paths
        - All cells are covered exactly once
        - All paths have adjacent consecutive steps
        
        Raises:
            AssertionError: If any validation check fails
        """
        self._validate_grid_dimensions()
        self._validate_spangram_path()
        self._validate_path_adjacency(self.spangram_path, self.spangram)
        
        used_cells = set(self.spangram_path)
        self._validate_word_paths(used_cells)
        self._validate_complete_coverage(used_cells)
        
        # Validate adjacency for all theme word paths
        for word in self.theme_words:
            self._validate_path_adjacency(self.word_paths[word], word)
        
        logger.info("Puzzle integrity validation passed")


def _create_horizontal_path(row: int, start_col: int, length: int) -> List[Coord]:
    """
    Create a horizontal path of coordinates.
    
    Args:
        row: Row index
        start_col: Starting column index
        length: Number of cells in the path
        
    Returns:
        List of coordinates forming a horizontal path
    """
    return [(row, col) for col in range(start_col, start_col + length)]


def default_puzzle() -> Puzzle:
    """
    Create the default puzzle instance.
    
    Theme: Programming Languages
    Spangram: SOFTWARE (spans top row, touching left and right edges)
    
    Returns:
        A fully initialized and validated Puzzle instance
    """
    rows = DEFAULT_ROWS
    cols = DEFAULT_COLS
    
    # Grid letters (uppercase)
    # Row 0: SOFTWARE (spangram)
    # Row 1: PYTHONGO
    # Row 2: KOTLINLU
    # Row 3: SWIFTRUA
    # Row 4: SCALARBY
    # Row 5: JULIAUST
    grid = [
        list("SOFTWARE"),
        list("PYTHONGO"),
        list("KOTLINLU"),
        list("SWIFTRUA"),
        list("SCALARBY"),
        list("JULIAUST"),
    ]
    
    theme = "Programming Languages"
    spangram = "SOFTWARE"
    spangram_path = _create_horizontal_path(0, 0, cols)
    
    # Predefined canonical paths for each themed word to ensure
    # a single, non-overlapping fill of the entire grid
    word_paths: Dict[str, List[Coord]] = {
        spangram: spangram_path,
        "PYTHON": _create_horizontal_path(1, 0, 6),
        "GO": _create_horizontal_path(1, 6, 2),
        "KOTLIN": _create_horizontal_path(2, 0, 6),
        # LUA: L (2,6) -> U (2,7) -> A (3,7)
        "LUA": [(2, 6), (2, 7), (3, 7)],
        "SWIFT": _create_horizontal_path(3, 0, 5),
        # RUBY: R (3,5) -> U (3,6) -> B (4,6) -> Y (4,7)
        "RUBY": [(3, 5), (3, 6), (4, 6), (4, 7)],
        "SCALA": _create_horizontal_path(4, 0, 5),
        # RUST: R (4,5) -> U (5,5) -> S (5,6) -> T (5,7)
        "RUST": [(4, 5), (5, 5), (5, 6), (5, 7)],
        "JULIA": _create_horizontal_path(5, 0, 5),
    }
    
    return Puzzle(
        rows=rows,
        cols=cols,
        grid=grid,
        theme=theme,
        spangram=spangram,
        spangram_path=spangram_path,
        word_paths=word_paths,
    )