import logging
from typing import List, Tuple, Dict, Optional

try:
    from .wordlist import WORDS as NON_THEME_WORDS
except ImportError:
    from wordlist import WORDS as NON_THEME_WORDS

logger = logging.getLogger(__name__)

Coord = Tuple[int, int]

MIN_WORD_LENGTH = 2
MIN_DICTIONARY_WORD_LENGTH = 4
HINT_ACCUMULATION_THRESHOLD = 3
ADJACENCY_DISTANCE = 1


class GameState:
    """Manages game state for Strands puzzle including word validation, tracking, and hints."""

    def __init__(self, puzzle):
        """
        Initialize game state for a puzzle.

        Args:
            puzzle: The puzzle object containing theme words, spangram, and paths.
        """
        self.puzzle = puzzle
        self.found_words = set()
        self.claimed: Dict[Coord, Dict[str, str]] = {}
        self.non_theme_words = set()
        self.hints = 0

    @staticmethod
    def is_adjacent(a: Coord, b: Coord) -> bool:
        """
        Check if two coordinates are adjacent (including diagonals).

        Args:
            a: First coordinate (row, col).
            b: Second coordinate (row, col).

        Returns:
            True if coordinates are adjacent, False otherwise.
        """
        return max(abs(a[0] - b[0]), abs(a[1] - b[1])) == ADJACENCY_DISTANCE and a != b

    def can_select_cell(self, coord: Coord) -> bool:
        """
        Check if a cell is available for selection.

        Args:
            coord: The coordinate to check.

        Returns:
            True if cell is unclaimed, False otherwise.
        """
        return coord not in self.claimed

    def selection_to_word(self, coords: List[Coord]) -> str:
        """
        Convert a list of coordinates to the word they spell.

        Args:
            coords: List of coordinates in order.

        Returns:
            The word spelled by the coordinates.
        """
        return "".join(self.puzzle.get_letter(r, c) for (r, c) in coords)

    def _claim_word(self, word: str, coords: List[Coord], kind: str) -> None:
        """
        Mark cells as claimed by a word and record the word as found.

        Args:
            word: The word being claimed.
            coords: List of coordinates the word occupies.
            kind: Type of word ('theme', 'spangram', or 'non-theme').
        """
        for coord in coords:
            self.claimed[coord] = {'word': word, 'type': kind}
        self.found_words.add(word)

    def is_completed(self) -> bool:
        """
        Check if the puzzle is fully completed.

        Returns:
            True if all theme words and spangram are found, False otherwise.
        """
        return self.puzzle.spangram in self.found_words and all(
            w in self.found_words for w in self.puzzle.theme_words
        )

    def _validate_selection_path(self, coords: List[Coord]) -> Optional[Dict[str, Optional[str]]]:
        """
        Validate that a selection path is valid (adjacent, unclaimed cells).

        Args:
            coords: List of coordinates to validate.

        Returns:
            Error dict if invalid, None if valid.
        """
        if not coords or len(coords) < MIN_WORD_LENGTH:
            return {'type': 'invalid', 'word': None, 'coords': coords}

        for i in range(1, len(coords)):
            if coords[i] in self.claimed:
                return {'type': 'invalid', 'word': None, 'coords': coords}
            if not self.is_adjacent(coords[i - 1], coords[i]):
                return {'type': 'invalid', 'word': None, 'coords': coords}

        return None

    def _check_spangram(self, word: str, coords: List[Coord]) -> Optional[Dict[str, Optional[str]]]:
        """
        Check if selection matches the spangram on its canonical path.

        Args:
            word: The word spelled by the selection.
            coords: The coordinates of the selection.

        Returns:
            Result dict if matched, None otherwise.
        """
        if word == self.puzzle.spangram and coords == self.puzzle.spangram_path:
            if self.puzzle.spangram not in self.found_words:
                self._claim_word(self.puzzle.spangram, coords, 'spangram')
                return {'type': 'spangram', 'word': word, 'coords': coords}
            else:
                return {'type': 'invalid', 'word': None, 'coords': coords}
        return None

    def _check_theme_word(self, word: str, coords: List[Coord]) -> Optional[Dict[str, Optional[str]]]:
        """
        Check if selection matches a theme word on its canonical path.

        Args:
            word: The word spelled by the selection.
            coords: The coordinates of the selection.

        Returns:
            Result dict if matched, None otherwise.
        """
        for theme_word in self.puzzle.theme_words:
            if word == theme_word and coords == self.puzzle.word_paths[theme_word]:
                if theme_word not in self.found_words:
                    self._claim_word(theme_word, coords, 'theme')
                    return {'type': 'theme', 'word': word, 'coords': coords}
                else:
                    return {'type': 'invalid', 'word': None, 'coords': coords}
        return None

    def _check_non_theme_word(self, word: str, coords: List[Coord]) -> Optional[Dict[str, Optional[str]]]:
        """
        Check if selection is a valid non-theme dictionary word and award hints.

        Args:
            word: The word spelled by the selection.
            coords: The coordinates of the selection.

        Returns:
            Result dict if valid, None otherwise.
        """
        if len(word) >= MIN_DICTIONARY_WORD_LENGTH and word.lower() in NON_THEME_WORDS:
            if word not in self.non_theme_words:
                self.non_theme_words.add(word)
                # Award hint every N non-theme words found
                if len(self.non_theme_words) % HINT_ACCUMULATION_THRESHOLD == 0:
                    self.hints += 1
            return {'type': 'non-theme', 'word': word, 'coords': coords}
        return None

    def try_commit_selection(self, coords: List[Coord]) -> Dict[str, Optional[str]]:
        """
        Attempt to commit a selection as a valid word.

        Validates path, checks against theme words and spangram on canonical paths,
        and awards hints for non-theme dictionary words.

        Args:
            coords: List of coordinates representing the selection.

        Returns:
            Dict with 'type' (invalid/theme/spangram/non-theme), 'word', and 'coords'.
        """
        # Validate path structure
        path_error = self._validate_selection_path(coords)
        if path_error:
            return path_error

        word = self.selection_to_word(coords)

        # Check spangram
        spangram_result = self._check_spangram(word, coords)
        if spangram_result:
            return spangram_result

        # Check theme words
        theme_result = self._check_theme_word(word, coords)
        if theme_result:
            return theme_result

        # Reject if word matches theme or spangram but not on canonical path
        if word in self.puzzle.theme_words or word == self.puzzle.spangram:
            return {'type': 'invalid', 'word': None, 'coords': coords}

        # Check non-theme dictionary word
        non_theme_result = self._check_non_theme_word(word, coords)
        if non_theme_result:
            return non_theme_result

        return {'type': 'invalid', 'word': None, 'coords': coords}

    def _get_next_unrevealed_theme_word(self) -> Optional[Tuple[str, List[Coord]]]:
        """
        Find the next unrevealed theme word.

        Returns:
            Tuple of (word, coords) or None if all theme words are found.
        """
        for theme_word in self.puzzle.theme_words:
            if theme_word not in self.found_words:
                coords = self.puzzle.word_paths[theme_word]
                # Verify cells are unclaimed
                if not any(c in self.claimed for c in coords):
                    return (theme_word, coords)
        return None

    def _reveal_word(self, word: str, coords: List[Coord], kind: str) -> Tuple[str, List[Coord], str]:
        """
        Reveal a word by claiming its cells and decrementing hints.

        Args:
            word: The word to reveal.
            coords: The coordinates of the word.
            kind: The type of word ('theme' or 'spangram').

        Returns:
            Tuple of (word, coords, kind).
        """
        self._claim_word(word, coords, kind)
        self.hints -= 1
        return (word, coords, kind)

    def reveal_hint(self) -> Optional[Tuple[str, List[Coord], str]]:
        """
        Reveal the next hint by uncovering an unrevealed word.

        Prioritizes theme words over spangram. Requires available hints.

        Returns:
            Tuple of (word, coords, kind) if hint revealed, None otherwise.
        """
        if self.hints <= 0:
            return None

        # Try to reveal next theme word
        theme_result = self._get_next_unrevealed_theme_word()
        if theme_result:
            word, coords = theme_result
            return self._reveal_word(word, coords, 'theme')

        # If all themes found, try to reveal spangram
        if self.puzzle.spangram not in self.found_words:
            coords = self.puzzle.spangram_path
            if not any(c in self.claimed for c in coords):
                return self._reveal_word(self.puzzle.spangram, coords, 'spangram')

        return None