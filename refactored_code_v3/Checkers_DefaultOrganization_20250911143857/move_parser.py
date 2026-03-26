import logging
from typing import List, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Board dimensions and coordinate constants
MIN_BOARD_COORD = 0
MAX_BOARD_COORD = 7
BOARD_SIZE = 8
MIN_FILE_CHAR = 'a'
MAX_FILE_CHAR = 'h'
MIN_RANK_CHAR = '1'
MAX_RANK_CHAR = '8'
ALGEBRAIC_SQUARE_LENGTH = 2
MIN_REQUIRED_SQUARES = 2

# Separator characters and keywords
MOVE_SEPARATORS = ['-', ':', 'x']
MOVE_KEYWORD = 'to'

# ASCII offsets for coordinate conversion
ASCII_OFFSET_FILE = ord(MIN_FILE_CHAR)
ASCII_OFFSET_RANK = int(MAX_RANK_CHAR)


class MoveParseError(Exception):
    """Exception raised when move notation parsing fails."""
    pass


class MoveParser:
    """Parser for checkers/draughts move notation in algebraic format."""

    @staticmethod
    def parse(text: str) -> List[Tuple[int, int]]:
        """
        Parse a move string into a list of board coordinates (row, col).

        Input squares are in algebraic notation (e.g., 'a3', 'h8').
        Columns a..h map to 0..7, rows 1..8 map to internal rows 7..0
        (row 1 is at the bottom).

        Supported input formats:
          - 'b6-c5' (hyphen separator)
          - 'c3:e5:g7' (colon separator for captures)
          - 'b6 to c5' (word separator)
          - 'B6 X A5 x C4' (case-insensitive, mixed separators)

        Args:
            text: Move notation string to parse.

        Returns:
            List of (row, col) tuples representing the move path.

        Raises:
            MoveParseError: If input is invalid or contains fewer than 2 squares.
        """
        MoveParser._validate_input(text)
        normalized_text = MoveParser._normalize_input(text)
        square_tokens = MoveParser._tokenize(normalized_text)
        coordinates = MoveParser._convert_tokens_to_coordinates(square_tokens)
        MoveParser._validate_move_length(coordinates)
        return coordinates

    @staticmethod
    def _validate_input(text: str) -> None:
        """
        Validate that input is a non-empty string.

        Args:
            text: Input to validate.

        Raises:
            MoveParseError: If input is not a string or is empty.
        """
        if not isinstance(text, str) or not text.strip():
            raise MoveParseError("Empty input.")

    @staticmethod
    def _normalize_input(text: str) -> str:
        """
        Normalize input by converting to lowercase and replacing separators.

        Replaces all common move separators (-, :, x) and the 'to' keyword
        with spaces to create a uniform token format.

        Args:
            text: Input text to normalize.

        Returns:
            Normalized text with consistent spacing.
        """
        normalized = text.lower().strip()

        # Replace separator characters with spaces
        for separator in MOVE_SEPARATORS:
            normalized = normalized.replace(separator, ' ')

        # Replace 'to' keyword with spaces (handles various spacing)
        normalized = normalized.replace(f' {MOVE_KEYWORD} ', ' ')
        normalized = normalized.replace(MOVE_KEYWORD, ' ')

        return normalized

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        Split normalized text into square tokens.

        Args:
            text: Normalized text to tokenize.

        Returns:
            List of non-empty tokens.
        """
        return [token for token in text.split() if token]

    @staticmethod
    def _convert_tokens_to_coordinates(tokens: List[str]) -> List[Tuple[int, int]]:
        """
        Convert algebraic square tokens to board coordinates.

        Args:
            tokens: List of algebraic square notations (e.g., ['b6', 'c5']).

        Returns:
            List of (row, col) coordinate tuples.

        Raises:
            MoveParseError: If any token is invalid.
        """
        coordinates: List[Tuple[int, int]] = []

        for token in tokens:
            coordinate = MoveParser._parse_square(token)
            coordinates.append(coordinate)

        return coordinates

    @staticmethod
    def _parse_square(square: str) -> Tuple[int, int]:
        """
        Parse a single algebraic square notation into (row, col) coordinates.

        Args:
            square: Algebraic square notation (e.g., 'a1', 'h8').

        Returns:
            Tuple of (row, col) where row and col are 0-7.

        Raises:
            MoveParseError: If square notation is invalid.
        """
        if len(square) != ALGEBRAIC_SQUARE_LENGTH:
            raise MoveParseError(f"Invalid token length: '{square}'")

        file_char, rank_char = square[0], square[1]

        # Validate file (column) is a-h
        if not (MIN_FILE_CHAR <= file_char <= MAX_FILE_CHAR):
            raise MoveParseError(f"Invalid square: {square}")

        # Validate rank (row) is 1-8
        if not (MIN_RANK_CHAR <= rank_char <= MAX_RANK_CHAR):
            raise MoveParseError(f"Invalid square: {square}")

        # Convert file character to column index (a->0, h->7)
        col = ord(file_char) - ASCII_OFFSET_FILE

        # Convert rank to row index (rank '1' at bottom -> row 7, rank '8' at top -> row 0)
        row = ASCII_OFFSET_RANK - int(rank_char)

        return (row, col)

    @staticmethod
    def _validate_move_length(coordinates: List[Tuple[int, int]]) -> None:
        """
        Validate that move contains at least source and destination squares.

        Args:
            coordinates: List of coordinate tuples.

        Raises:
            MoveParseError: If fewer than 2 squares are specified.
        """
        if len(coordinates) < MIN_REQUIRED_SQUARES:
            raise MoveParseError(
                f"Specify at least {MIN_REQUIRED_SQUARES} squares "
                "(source and destination)."
            )