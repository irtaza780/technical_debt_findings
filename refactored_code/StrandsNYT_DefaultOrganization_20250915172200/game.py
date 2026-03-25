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
        Mark a word as found and claim its cells.

        Args:
            word: The word to claim.
            coords: The coordinates the word occupies.
            kind: The type of word ('theme', 'spangram', or 'non-theme').
        """
        for coord in coords:
            self.claimed[coord] = {'word': word, 'type': kind}
        self.found_words.add(word)

    def _is_valid_selection(self, coords: List[Coord]) -> bool:
        """
        Validate that a selection meets basic requirements.

        Args:
            coords: List of coordinates to validate.

        Returns:
            True if selection is valid, False otherwise.
        """
        if not coords or len(coords) < MIN_WORD_LENGTH:
            return False

        for i in range(1, len(coords)):
            if coords[i] in self.claimed:
                return False
            if not self.is_adjacent(coords[i - 1], coords[i]):
                return False

        return True

    def _check_spangram_match(self, word: str, coords: List[Coord]) -> Optional[Dict]:
        """
        Check if selection matches the spangram.

        Args:
            word: The word spelled by the selection.
            coords: The coordinates of the selection.

        Returns:
            Result dict if spangram matches, None otherwise.
        """
        if word == self.puzzle.spangram and coords == self.puzzle.spangram_path:
            if self.puzzle.spangram not in self.found_words:
                self._claim_word(self.puzzle.spangram, coords, 'spangram')
                return {'type': 'spangram', 'word': word, 'coords': coords}
            else:
                logger.debug(f"Spangram '{word}' already found")
                return {'type': 'invalid', 'word': None, 'coords': coords}
        return None

    def _check_theme_word_match(self, word: str, coords: List[Coord]) -> Optional[Dict]:
        """
        Check if selection matches a theme word.

        Args:
            word: The word spelled by the selection.
            coords: The coordinates of the selection.

        Returns:
            Result dict if theme word matches, None otherwise.
        """
        for theme_word in self.puzzle.theme_words:
            if word == theme_word and coords == self.puzzle.word_paths[theme_word]:
                if theme_word not in self.found_words:
                    self._claim_word(theme_word, coords, 'theme')
                    return {'type': 'theme', 'word': word, 'coords': coords}
                else:
                    logger.debug(f"Theme word '{word}' already found")
                    return {'type': 'invalid', 'word': None, 'coords': coords}
        return None

    def _check_non_theme_word(self, word: str, coords: List[Coord]) -> Optional[Dict]:
        """
        Check if selection is a valid non-theme dictionary word.

        Args:
            word: The word spelled by the selection.
            coords: The coordinates of the selection.

        Returns:
            Result dict if valid non-theme word, None otherwise.
        """
        if len(word) >= MIN_DICTIONARY_WORD_LENGTH and word.lower() in NON_THEME_WORDS:
            if word not in self.non_theme_words:
                self.non_theme_words.add(word)
                # Award hint every N non-theme words
                if len(self.non_theme_words) % HINT_ACCUMULATION_THRESHOLD == 0:
                    self.hints += 1
                    logger.debug(f"Hint awarded. Total hints: {self.hints}")
            return {'type': 'non-theme', 'word': word, 'coords': coords}
        return None

    def try_commit_selection(self, coords: List[Coord]) -> Dict[str, Optional[str]]:
        """
        Attempt to commit a word selection to the game state.

        Validates the selection path, checks against theme words and spangram,
        and awards hints for non-theme dictionary words.

        Args:
            coords: List of coordinates representing the selection path.

        Returns:
            Dict with keys 'type', 'word', and 'coords' indicating the result.
        """
        if not self._is_valid_selection(coords):
            return {'type': 'invalid', 'word': None, 'coords': coords}

        word = self.selection_to_word(coords)

        # Check spangram
        spangram_result = self._check_spangram_match(word, coords)
        if spangram_result is not None:
            return spangram_result

        # Check theme words
        theme_result = self._check_theme_word_match(word, coords)
        if theme_result is not None:
            return theme_result

        # Reject themed/spangram words not on canonical path
        if word in self.puzzle.theme_words or word == self.puzzle.spangram:
            logger.debug(f"Word '{word}' matches theme/spangram but not on canonical path")
            return {'type': 'invalid', 'word': None, 'coords': coords}

        # Check non-theme dictionary word
        non_theme_result = self._check_non_theme_word(word, coords)
        if non_theme_result is not None:
            return non_theme_result

        return {'type': 'invalid', 'word': None, 'coords': coords}

    def is_completed(self) -> bool:
        """
        Check if the puzzle is fully completed.

        Returns:
            True if all theme words and spangram are found, False otherwise.
        """
        return self.puzzle.spangram in self.found_words and all(
            w in self.found_words for w in self.puzzle.theme_words
        )

    def _reveal_theme_word_hint(self) -> Optional[Tuple]:
        """
        Reveal the next unfound theme word as a hint.

        Returns:
            Tuple of (word, coords, type) if hint revealed, None otherwise.
        """
        for theme_word in self.puzzle.theme_words:
            if theme_word not in self.found_words:
                coords = self.puzzle.word_paths[theme_word]
                # Verify cells are unclaimed
                if any(c in self.claimed for c in coords):
                    logger.warning(f"Theme word '{theme_word}' has claimed cells; skipping")
                    continue
                self._claim_word(theme_word, coords, 'theme')
                self.hints -= 1
                logger.info(f"Revealed theme word hint: '{theme_word}'")
                return (theme_word, coords, 'theme')
        return None

    def _reveal_spangram_hint(self) -> Optional[Tuple]:
        """
        Reveal the spangram as a hint if not yet found.

        Returns:
            Tuple of (word, coords, type) if spangram revealed, None otherwise.
        """
        if self.puzzle.spangram not in self.found_words:
            coords = self.puzzle.spangram_path
            if any(c in self.claimed for c in coords):
                logger.warning("Spangram has claimed cells; cannot reveal")
                return None
            self._claim_word(self.puzzle.spangram, coords, 'spangram')
            self.hints -= 1
            logger.info("Revealed spangram hint")
            return (self.puzzle.spangram, coords, 'spangram')
        return None

    def reveal_hint(self) -> Optional[Tuple]:
        """
        Reveal the next available hint.

        Prioritizes unrevealed theme words, then the spangram.

        Returns:
            Tuple of (word, coords, type) if hint revealed, None if no hints available.
        """
        if self.hints <= 0:
            logger.debug("No hints available")
            return None

        # Try to reveal a theme word first
        theme_hint = self._reveal_theme_word_hint()
        if theme_hint is not None:
            return theme_hint

        # If all themes found, try spangram
        spangram_hint = self._reveal_spangram_hint()
        if spangram_hint is not None:
            return spangram_hint

        logger.debug("No unrevealed words available for hint")
        return None