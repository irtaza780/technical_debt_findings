import logging
from typing import Optional, List, Tuple

try:
    import pygame
except ImportError:
    pygame = None

from constants import (
    ROWS, COLS, SQUARE_SIZE, BOARD_SIZE,
    LIGHT_COLOR, DARK_COLOR, RED_COLOR, BLACK_COLOR,
    HILITE_MOVE_COLOR, HILITE_CAPTURE_COLOR, KING_TEXT_COLOR
)

logger = logging.getLogger(__name__)

# Board setup constants
INITIAL_BLACK_ROWS = 3
INITIAL_RED_START_ROW = 5
INITIAL_RED_END_ROW = 8
DARK_SQUARE_PARITY = 1

# Drawing constants
PIECE_RADIUS_RATIO = 0.4
PIECE_BORDER_WIDTH = 2
PIECE_BORDER_COLOR = (20, 20, 20)
HIGHLIGHT_BORDER_WIDTH = 3
CAPTURE_DISTANCE = 2

# Piece color constants
RED_PIECE = 'red'
BLACK_PIECE = 'black'

Position = Tuple[int, int]
Grid = List[List[Optional['Piece']]]


class Piece:
    """Represents a single checkers piece on the board.
    
    Attributes:
        color: The piece color ('red' or 'black').
        king: Whether the piece has been promoted to king status.
    """

    def __init__(self, color: str, king: bool = False) -> None:
        """Initialize a checkers piece.
        
        Args:
            color: The piece color ('red' or 'black').
            king: Whether the piece is a king. Defaults to False.
        """
        self.color = color
        self.king = king

    def clone(self) -> 'Piece':
        """Create a deep copy of this piece.
        
        Returns:
            A new Piece instance with identical attributes.
        """
        return Piece(self.color, self.king)


class Board:
    """Represents the checkers game board and manages piece placement.
    
    The board is an 8x8 grid where pieces are placed only on dark squares.
    Pieces are initialized in their starting positions for a standard game.
    """

    def __init__(self) -> None:
        """Initialize an empty board and set up initial piece positions."""
        self.grid: Grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.setup_initial()

    def setup_initial(self) -> None:
        """Place all pieces in their starting positions.
        
        Black pieces occupy rows 0-2 (top), red pieces occupy rows 5-7 (bottom).
        Pieces are placed only on dark squares (where row + col is odd).
        """
        self._place_pieces_for_color(BLACK_PIECE, 0, INITIAL_BLACK_ROWS)
        self._place_pieces_for_color(RED_PIECE, INITIAL_RED_START_ROW, INITIAL_RED_END_ROW)

    def _place_pieces_for_color(self, color: str, start_row: int, end_row: int) -> None:
        """Place pieces of a specific color in their starting rows.
        
        Args:
            color: The piece color ('red' or 'black').
            start_row: The first row to place pieces in (inclusive).
            end_row: The last row to place pieces in (exclusive).
        """
        for row in range(start_row, end_row):
            for col in range(COLS):
                # Only place pieces on dark squares
                if (row + col) % 2 == DARK_SQUARE_PARITY:
                    self.grid[row][col] = Piece(color, king=False)

    def copy(self) -> 'Board':
        """Create a deep copy of the board.
        
        Returns:
            A new Board instance with cloned pieces at identical positions.
        """
        board_copy = Board.__new__(Board)
        board_copy.grid = [
            [piece.clone() if piece else None for piece in row]
            for row in self.grid
        ]
        return board_copy

    @staticmethod
    def in_bounds(row: int, col: int) -> bool:
        """Check if a position is within the board boundaries.
        
        Args:
            row: The row coordinate.
            col: The column coordinate.
            
        Returns:
            True if the position is valid, False otherwise.
        """
        return 0 <= row < ROWS and 0 <= col < COLS

    def get(self, row: int, col: int) -> Optional[Piece]:
        """Retrieve the piece at a given position.
        
        Args:
            row: The row coordinate.
            col: The column coordinate.
            
        Returns:
            The Piece at the position, or None if empty or out of bounds.
        """
        if not self.in_bounds(row, col):
            return None
        return self.grid[row][col]

    def set(self, row: int, col: int, piece: Optional[Piece]) -> None:
        """Place or remove a piece at a given position.
        
        Args:
            row: The row coordinate.
            col: The column coordinate.
            piece: The Piece to place, or None to clear the square.
        """
        if self.in_bounds(row, col):
            self.grid[row][col] = piece

    def move_piece(self, from_pos: Position, to_pos: Position) -> None:
        """Move a piece from one position to another.
        
        Args:
            from_pos: A tuple (row, col) of the source position.
            to_pos: A tuple (row, col) of the destination position.
        """
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.get(from_row, from_col)
        self.set(from_row, from_col, None)
        self.set(to_row, to_col, piece)

    def remove_piece(self, row: int, col: int) -> None:
        """Remove the piece at a given position.
        
        Args:
            row: The row coordinate.
            col: The column coordinate.
        """
        self.set(row, col, None)

    def draw(self, surface, font, last_move: Optional[List[Position]] = None) -> None:
        """Render the board and all pieces to a pygame surface.
        
        This method is a no-op if pygame is not available (headless environments).
        
        Args:
            surface: The pygame surface to draw on.
            font: The pygame font object for rendering king text.
            last_move: Optional list of positions representing the last move path.
        """
        if pygame is None:
            logger.debug("Pygame unavailable; skipping board rendering")
            return

        self._draw_board_squares(surface)
        self._draw_move_highlights(surface, last_move)
        self._draw_pieces(surface, font)

    def _draw_board_squares(self, surface) -> None:
        """Draw the checkerboard pattern.
        
        Args:
            surface: The pygame surface to draw on.
        """
        for row in range(ROWS):
            for col in range(COLS):
                rect = pygame.Rect(
                    col * SQUARE_SIZE,
                    row * SQUARE_SIZE,
                    SQUARE_SIZE,
                    SQUARE_SIZE
                )
                # Alternate between light and dark squares
                color = DARK_COLOR if (row + col) % 2 == DARK_SQUARE_PARITY else LIGHT_COLOR
                pygame.draw.rect(surface, color, rect)

    def _draw_move_highlights(self, surface, last_move: Optional[List[Position]]) -> None:
        """Highlight the squares involved in the last move.
        
        Args:
            surface: The pygame surface to draw on.
            last_move: List of positions representing the move path.
        """
        if not last_move or len(last_move) < 2:
            return

        # Highlight each step in the move path
        for i in range(len(last_move) - 1):
            from_row, from_col = last_move[i]
            to_row, to_col = last_move[i + 1]

            # Determine highlight color based on move type
            is_capture = abs(to_row - from_row) == CAPTURE_DISTANCE
            highlight_color = HILITE_CAPTURE_COLOR if is_capture else HILITE_MOVE_COLOR

            # Draw highlight rectangles
            from_rect = pygame.Rect(
                from_col * SQUARE_SIZE,
                from_row * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE
            )
            to_rect = pygame.Rect(
                to_col * SQUARE_SIZE,
                to_row * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE
            )
            pygame.draw.rect(surface, highlight_color, from_rect, HIGHLIGHT_BORDER_WIDTH)
            pygame.draw.rect(surface, highlight_color, to_rect, HIGHLIGHT_BORDER_WIDTH)

    def _draw_pieces(self, surface, font) -> None:
        """Draw all pieces on the board.
        
        Args:
            surface: The pygame surface to draw on.
            font: The pygame font object for rendering king text.
        """
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.grid[row][col]
                if piece:
                    self._draw_single_piece(surface, font, row, col, piece)

    def _draw_single_piece(self, surface, font, row: int, col: int, piece: Piece) -> None:
        """Draw a single piece at the specified board position.
        
        Args:
            surface: The pygame surface to draw on.
            font: The pygame font object for rendering king text.
            row: The row coordinate of the piece.
            col: The column coordinate of the piece.
            piece: The Piece object to draw.
        """
        center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
        center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
        center = (center_x, center_y)

        # Draw piece circle
        radius = int(SQUARE_SIZE * PIECE_RADIUS_RATIO)
        piece_color = RED_COLOR if piece.color == RED_PIECE else BLACK_COLOR
        pygame.draw.circle(surface, piece_color, center, radius)
        pygame.draw.circle(surface, PIECE_BORDER_COLOR, center, radius, PIECE_BORDER_WIDTH)

        # Draw king indicator if applicable
        if piece.king:
            king_text = font.render("K", True, KING_TEXT_COLOR)
            text_rect = king_text.get_rect(center=center)
            surface.blit(king_text, text_rect)