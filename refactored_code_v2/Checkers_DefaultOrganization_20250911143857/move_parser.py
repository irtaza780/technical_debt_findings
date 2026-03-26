import logging
from typing import List, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Board dimensions and coordinate mappings
MIN_COLUMN = 'a'
MAX_COLUMN = 'h'
MIN_ROW = '1'
MAX_ROW = '8'
BOARD_SIZE = 8
COLUMN_RANGE = ord(MAX_COLUMN) - ord(MIN_COLUMN) + 1
ROW_RANGE = int(MAX_ROW) - int(MIN_ROW) + 1

# Move notation separators
MOVE_SEPARATORS = ['-', ':', 'x']
MOVE_KEYWORD = 'to'
SQUARE_TOKEN_LENGTH = 2
MIN_SQUARES_IN_MOVE = 2


class MoveParseError(Exception):
    """Exception raised when move notation parsing fails."""
    pass


class MoveParser:
    """Parser for checkers/draughts move notation in algebraic format."""

    @staticmethod
    def parse(text: str) -> List[Tuple[int, int]]:
        """
        Parse a move string into a list of board coordinates (row, col).

        Input squares are in algebraic notation (a-h for columns, 1-8 for rows).
        Columns a..h map to 0..7, rows 1..8 map to internal rows 7..0
        (row 1 is at the bottom).

        Supported input formats:
          - 'b6-c5' (single move with dash)
          - 'c3:e5:g7' (multi-capture with colons)
          - 'b6 to c5' (with 'to' keyword)
          - 'B6 X A5 x C4' (case-insensitive, mixed separators)

        Args:
            text: Move notation string to parse.

        Returns:
            List of (row, col) tuples representing the move path.

        Raises:
            MoveParseError: If input is invalid or malformed.
        """
        MoveParser._validate_input(text)
        normalized_text = MoveParser._normalize_input(text)
        square_tokens = MoveParser._extract_tokens(normalized_text)
        coordinates = MoveParser._convert_tokens_to_coordinates(square_tokens)
        MoveParser._validate_move(coordinates)

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
        Normalize input by converting to lowercase and standardizing separators.

        Replaces all move separators (-, :, x) and the 'to' keyword with spaces
        to create a uniform token-separated format.

        Args:
            text: Raw input text.

        Returns:
            Normalized text with consistent spacing.
        """
        normalized = text.lower().strip()

        # Replace all separator characters with spaces
        for separator in MOVE_SEPARATORS:
            normalized = normalized.replace(separator, ' ')

        # Replace 'to' keyword with space (handles various spacing scenarios)
        normalized = normalized.replace(f' {MOVE_KEYWORD} ', ' ')
        normalized = normalized.replace(MOVE_KEYWORD, ' ')

        return normalized

    @staticmethod
    def _extract_tokens(normalized_text: str) -> List[str]:
        """
        Extract square tokens from normalized text.

        Splits on whitespace and filters out empty strings.

        Args:
            normalized_text: Text with normalized separators.

        Returns:
            List of non-empty tokens.
        """
        return [token for token in normalized_text.split() if token]

    @staticmethod
    def _convert_tokens_to_coordinates(tokens: List[str]) -> List[Tuple[int, int]]:
        """
        Convert square notation tokens to board coordinates.

        Each token must be exactly 2 characters: a file letter (a-h) and a rank
        digit (1-8). Converts to internal (row, col) format where row 0 is at
        the top and row 7 is at the bottom.

        Args:
            tokens: List of square notation strings (e.g., ['b6', 'c5']).

        Returns:
            List of (row, col) tuples.

        Raises:
            MoveParseError: If any token is invalid.
        """
        coordinates = []

        for token in tokens:
            coordinate = MoveParser._parse_square(token)
            coordinates.append(coordinate)

        return coordinates

    @staticmethod
    def _parse_square(square: str) -> Tuple[int, int]:
        """
        Parse a single square in algebraic notation to (row, col) coordinates.

        Args:
            square: Square notation string (e.g., 'a1', 'h8').

        Returns:
            Tuple of (row, col) where both are 0-based indices.

        Raises:
            MoveParseError: If square notation is invalid.
        """
        if len(square) != SQUARE_TOKEN_LENGTH:
            raise MoveParseError(f"Invalid token length: '{square}'")

        column_char = square[0]
        row_char = square[1]

        # Validate column (file) is in range a-h
        if not (MIN_COLUMN <= column_char <= MAX_COLUMN):
            raise MoveParseError(f"Invalid square: {square}")

        # Validate row (rank) is in range 1-8
        if not (MIN_ROW <= row_char <= MAX_ROW):
            raise MoveParseError(f"Invalid square: {square}")

        # Convert column letter to 0-based index (a->0, h->7)
        column_index = ord(column_char) - ord(MIN_COLUMN)

        # Convert row number to 0-based index (1->7, 8->0)
        # Row 1 is at the bottom, so we invert: 8 - rank_number
        row_index = BOARD_SIZE - int(row_char)

        return (row_index, column_index)

    @staticmethod
    def _validate_move(coordinates: List[Tuple[int, int]]) -> None:
        """
        Validate that the move contains at least source and destination squares.

        Args:
            coordinates: List of (row, col) tuples.

        Raises:
            MoveParseError: If fewer than 2 squares are specified.
        """
        if len(coordinates) < MIN_SQUARES_IN_MOVE:
            raise MoveParseError(
                "Specify at least source and destination squares."
            )