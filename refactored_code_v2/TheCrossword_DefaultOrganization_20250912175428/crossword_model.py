import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Constants
BLOCK_CHAR = "#"
EMPTY_CELL = ""
ACROSS_DIRECTION = "A"
DOWN_DIRECTION = "D"
DEFAULT_TITLE = "Crossword"
MIN_GRID_SIZE = 0
DEFAULT_ACROSS_CLUE_TEMPLATE = "Across word ({length})"
DEFAULT_DOWN_CLUE_TEMPLATE = "Down word ({length})"


@dataclass
class CrosswordEntry:
    """Represents a single crossword entry (clue with answer)."""
    number: int
    direction: str
    row: int
    col: int
    length: int
    answer: str
    clue: str
    filled: bool = False


class CrosswordModel:
    """
    Manages the state and logic of a crossword puzzle.
    
    Handles:
    - Grid initialization and validation
    - Dynamic entry numbering based on grid structure
    - Answer placement and validation
    - Completion tracking
    - Clue resolution from number-based or answer-based dictionaries
    """

    def __init__(
        self,
        solution_rows: List[str],
        across_clues_by_answer: Optional[Dict[str, str]] = None,
        down_clues_by_answer: Optional[Dict[str, str]] = None,
        across_clues_by_number: Optional[Dict[int, str]] = None,
        down_clues_by_number: Optional[Dict[int, str]] = None,
        title: str = DEFAULT_TITLE,
    ):
        """
        Initialize the crossword model.
        
        Args:
            solution_rows: List of strings representing the solution grid.
                          '#' represents blocked cells.
            across_clues_by_answer: Optional dict mapping answers to across clues.
            down_clues_by_answer: Optional dict mapping answers to down clues.
            across_clues_by_number: Optional dict mapping entry numbers to across clues.
            down_clues_by_number: Optional dict mapping entry numbers to down clues.
            title: Title of the crossword puzzle.
            
        Raises:
            ValueError: If solution rows have inconsistent lengths.
        """
        self.title = title
        self.solution_rows = [row.upper() for row in solution_rows]
        self.rows = len(self.solution_rows)
        self.cols = len(self.solution_rows[0]) if self.rows > MIN_GRID_SIZE else 0

        self._validate_grid_dimensions()
        self._initialize_grids()
        self._store_clue_dictionaries(
            across_clues_by_answer,
            down_clues_by_answer,
            across_clues_by_number,
            down_clues_by_number,
        )
        self.entries: List[CrosswordEntry] = []
        self.entry_map: Dict[Tuple[int, str], CrosswordEntry] = {}
        self._compute_entries()

    def _validate_grid_dimensions(self) -> None:
        """Validate that all solution rows have consistent length."""
        for row in self.solution_rows:
            if len(row) != self.cols:
                raise ValueError("All solution rows must have the same length.")

    def _initialize_grids(self) -> None:
        """Initialize solution grid, block grid, and current grid."""
        self.solution_grid: List[List[Optional[str]]] = []
        self.block_grid: List[List[bool]] = []
        self.current_grid: List[List[Optional[str]]] = []

        for row_idx in range(self.rows):
            solution_row: List[Optional[str]] = []
            block_row: List[bool] = []
            current_row: List[Optional[str]] = []

            for col_idx in range(self.cols):
                char = self.solution_rows[row_idx][col_idx]
                is_block = char == BLOCK_CHAR

                solution_row.append(None if is_block else char)
                block_row.append(is_block)
                current_row.append(None if is_block else EMPTY_CELL)

            self.solution_grid.append(solution_row)
            self.block_grid.append(block_row)
            self.current_grid.append(current_row)

    def _store_clue_dictionaries(
        self,
        across_clues_by_answer: Optional[Dict[str, str]],
        down_clues_by_answer: Optional[Dict[str, str]],
        across_clues_by_number: Optional[Dict[int, str]],
        down_clues_by_number: Optional[Dict[int, str]],
    ) -> None:
        """Store clue dictionaries with defaults for None values."""
        self.across_clues_by_answer = across_clues_by_answer or {}
        self.down_clues_by_answer = down_clues_by_answer or {}
        self.across_clues_by_number = across_clues_by_number or {}
        self.down_clues_by_number = down_clues_by_number or {}

    def _compute_entries(self) -> None:
        """
        Compute all crossword entries by scanning the grid.
        
        Assigns numbers to cells that start across or down entries,
        reads entry answers, resolves clues, and builds entry map.
        """
        entry_number = 1

        for row_idx in range(self.rows):
            for col_idx in range(self.cols):
                if self.block_grid[row_idx][col_idx]:
                    continue

                starts_across = self._starts_across(row_idx, col_idx)
                starts_down = self._starts_down(row_idx, col_idx)

                if not (starts_across or starts_down):
                    continue

                if starts_across:
                    self._add_entry(
                        entry_number,
                        ACROSS_DIRECTION,
                        row_idx,
                        col_idx,
                    )

                if starts_down:
                    self._add_entry(
                        entry_number,
                        DOWN_DIRECTION,
                        row_idx,
                        col_idx,
                    )

                entry_number += 1

        # Sort entries by number then direction for consistent display
        self.entries.sort(key=lambda e: (e.number, e.direction))

    def _starts_across(self, row_idx: int, col_idx: int) -> bool:
        """Check if a cell starts an across entry."""
        return col_idx == 0 or self.block_grid[row_idx][col_idx - 1]

    def _starts_down(self, row_idx: int, col_idx: int) -> bool:
        """Check if a cell starts a down entry."""
        return row_idx == 0 or self.block_grid[row_idx - 1][col_idx]

    def _add_entry(
        self,
        entry_number: int,
        direction: str,
        row_idx: int,
        col_idx: int,
    ) -> None:
        """
        Create and register an entry.
        
        Args:
            entry_number: The clue number for this entry.
            direction: 'A' for across or 'D' for down.
            row_idx: Starting row index.
            col_idx: Starting column index.
        """
        length, answer = (
            self._read_across(row_idx, col_idx)
            if direction == ACROSS_DIRECTION
            else self._read_down(row_idx, col_idx)
        )

        clue = self._resolve_clue(entry_number, direction, answer, length)
        entry = CrosswordEntry(
            number=entry_number,
            direction=direction,
            row=row_idx,
            col=col_idx,
            length=length,
            answer=answer,
            clue=clue,
        )
        self.entries.append(entry)
        self.entry_map[(entry_number, direction)] = entry

    def _resolve_clue(
        self,
        entry_number: int,
        direction: str,
        answer: str,
        length: int,
    ) -> str:
        """
        Resolve a clue from available dictionaries.
        
        Prefers number-based clues, falls back to answer-based clues,
        then returns a default template.
        
        Args:
            entry_number: The clue number.
            direction: 'A' for across or 'D' for down.
            answer: The answer text.
            length: The answer length.
            
        Returns:
            The resolved clue text.
        """
        if direction == ACROSS_DIRECTION:
            if entry_number in self.across_clues_by_number:
                return self.across_clues_by_number[entry_number]
            if answer in self.across_clues_by_answer:
                return self.across_clues_by_answer[answer]
            return DEFAULT_ACROSS_CLUE_TEMPLATE.format(length=length)

        # Down direction
        if entry_number in self.down_clues_by_number:
            return self.down_clues_by_number[entry_number]
        if answer in self.down_clues_by_answer:
            return self.down_clues_by_answer[answer]
        return DEFAULT_DOWN_CLUE_TEMPLATE.format(length=length)

    def _read_across(self, row_idx: int, col_idx: int) -> Tuple[int, str]:
        """
        Read an across entry starting from the given position.
        
        Args:
            row_idx: Starting row index.
            col_idx: Starting column index.
            
        Returns:
            Tuple of (length, answer_string).
        """
        chars: List[str] = []
        current_col = col_idx

        while current_col < self.cols and not self.block_grid[row_idx][current_col]:
            char = self.solution_grid[row_idx][current_col]
            if char is None:
                break
            chars.append(char)
            current_col += 1

        return len(chars), "".join(chars)

    def _read_down(self, row_idx: int, col_idx: int) -> Tuple[int, str]:
        """
        Read a down entry starting from the given position.
        
        Args:
            row_idx: Starting row index.
            col_idx: Starting column index.
            
        Returns:
            Tuple of (length, answer_string).
        """
        chars: List[str] = []
        current_row = row_idx

        while current_row < self.rows and not self.block_grid[current_row][col_idx]:
            char = self.solution_grid[current_row][col_idx]
            if char is None:
                break
            chars.append(char)
            current_row += 1

        return len(chars), "".join(chars)

    def get_entries(self, direction: Optional[str] = None) -> List[CrosswordEntry]:
        """
        Get entries, optionally filtered by direction.
        
        Args:
            direction: Optional 'A' for across or 'D' for down.
            
        Returns:
            List of CrosswordEntry objects.
        """
        if direction in (ACROSS_DIRECTION, DOWN_DIRECTION):
            return [e for e in self.entries if e.direction == direction]
        return list(self.entries)

    def get_entry(self, number: int, direction: str) -> Optional[CrosswordEntry]:
        """
        Get a specific entry by number and direction.
        
        Args:
            number: The clue number.
            direction: 'A' for across or 'D' for down.
            
        Returns:
            CrosswordEntry if found, None otherwise.
        """
        return self.entry_map.get((number, direction.upper()))

    def place_answer(self, number: int, direction: str, word: str) -> Tuple[bool, str]:
        """
        Attempt to place an answer for a given clue.
        
        Validates that the entry exists, word length matches, and word
        matches the solution. On success, fills the current grid and
        marks the entry as filled.
        
        Args:
            number: The clue number.
            direction: 'A' for across or 'D' for down.
            word: The user's answer.
            
        Returns:
            Tuple of (success: bool, message: str).
        """
        direction = direction.upper().strip()
        if direction not in (ACROSS_DIRECTION, DOWN_DIRECTION):
            return False, "Direction must be 'A' (Across) or 'D' (Down)."

        entry = self.get_entry(number, direction)
        if not entry:
            return False, f"No entry found for {number}{direction}."

        user_answer = word.upper().strip()
        if len(user_answer) != entry.length:
            return False, f"Answer length mismatch: expected {entry.length} letters."

        if user_answer != entry.answer:
            mismatch_details = self._check_conflicts(entry, user_answer, direction)
            if mismatch_details:
                return False, f"Letters conflict with filled cells ({mismatch_details})."
            return False, "Incorrect answer."

        # Fill the grid with the correct answer
        self._fill_entry(entry, user_answer, direction)
        entry.filled = True
        logger.info(f"Placed answer for {number}{direction}")
        return True, f"Placed {number}{direction}."

    def _check_conflicts(
        self,
        entry: CrosswordEntry,
        user_answer: str,
        direction: str,
    ) -> str:
        """
        Check for conflicts between user answer and existing grid cells.
        
        Args:
            entry: The CrosswordEntry being filled.
            user_answer: The user's proposed answer.
            direction: 'A' for across or 'D' for down.
            
        Returns:
            Formatted conflict details string, or empty string if no conflicts.
        """
        mismatch_positions: List[Tuple[int, str, str]] = []

        for position_idx in range(entry.length):
            row_idx = entry.row + (position_idx if direction == DOWN_DIRECTION else 0)
            col_idx = entry.col + (position_idx if direction == ACROSS_DIRECTION else 0)
            existing = self.current_grid[row_idx][col_idx]

            if existing and existing != EMPTY_CELL and existing != user_answer[position_idx]:
                mismatch_positions.append(
                    (position_idx + 1, existing, user_answer[position_idx])
                )

        if mismatch_positions:
            details = "; ".join(
                [
                    f"pos {pos}: grid has '{grid_char}', you typed '{user_char}'"
                    for (pos, grid_char, user_char) in mismatch_positions
                ]
            )
            return details

        return ""

    def _fill_entry(
        self,
        entry: CrosswordEntry,
        answer: str,
        direction: str,
    ) -> None:
        """
        Fill grid cells for an entry with the given answer.
        
        Args:
            entry: The CrosswordEntry to fill.
            answer: The answer string.
            direction: 'A' for across or 'D' for down.
        """
        for position_idx in range(entry.length):
            row_idx = entry.row + (position_idx if direction == DOWN_DIRECTION else 0)
            col_idx = entry.col + (position_idx if direction == ACROSS_DIRECTION else 0)
            self.current_grid[row_idx][col_idx] = answer[position_idx]

    def is_block(self, row_idx: int, col_idx: int) -> bool:
        """
        Check if a cell is a block.
        
        Args:
            row_idx: Row index.
            col_idx: Column index.
            
        Returns:
            True if the cell is blocked, False otherwise.
        """
        return self.block_grid[row_idx][col_idx]

    def get_cell(self, row_idx: int,