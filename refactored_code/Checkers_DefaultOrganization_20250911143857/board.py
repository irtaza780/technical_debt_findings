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
    Attributes:
        grid: 2D list representing the board state, with Piece objects or None.
    """

    def __init__(self) -> None:
        """Initialize an empty board and set up initial piece positions."""
        self.grid: List[List[Optional[Piece]]] = [
            [None for _ in range(COLS)] for _ in range(ROWS)
        ]
        self.setup_initial()

    def setup_initial(self) -> None:
        """Place pieces in their starting positions.
        
        Black pieces occupy rows 0-2, red pieces occupy rows 5-7.
        Pieces are placed only on dark squares (where row + col is odd).
        """
        # Place black pieces in top rows
        self._place_pieces_in_rows(
            start_row=0,
            end_row=INITIAL_BLACK_ROWS,
            color=BLACK_PIECE
        )
        # Place red pieces in bottom rows
        self._place_pieces_in_rows(
            start_row=INITIAL_RED_START_ROW,
            end_row=INITIAL_RED_END_ROW,
            color=RED_PIECE
        )

    def _place_pieces_in_rows(
        self,
        start_row: int,
        end_row: int,
        color: str
    ) -> None:
        """Place pieces of a given color in a range of rows.
        
        Args:
            start_row: The starting row index (inclusive).
            end_row: The ending row index (exclusive).
            color: The color of pieces to place ('red' or 'black').
        """
        for row in range(start_row, end_row):
            for col in range(COLS):
                # Only place on dark squares
                if (row + col) % 2 == DARK_SQUARE_PARITY:
                    self.grid[row][col] = Piece(color, king=False)

    def copy(self) -> 'Board':
        """Create a deep copy of the board.
        
        Returns:
            A new Board instance with cloned pieces.
        """
        new_board = Board.__new__(Board)
        new_board.grid = [
            [piece.clone() if piece else None for piece in row]
            for row in self.grid
        ]
        return new_board

    @staticmethod
    def in_bounds(row: int, col: int) -> bool:
        """Check if coordinates are within board boundaries.
        
        Args:
            row: The row index.
            col: The column index.
            
        Returns:
            True if coordinates are valid, False otherwise.
        """
        return 0 <= row < ROWS and 0 <= col < COLS

    def get(self, row: int, col: int) -> Optional[Piece]:
        """Retrieve a piece at the given position.
        
        Args:
            row: The row index.
            col: The column index.
            
        Returns:
            The Piece at the position, or None if empty or out of bounds.
        """
        if not self.in_bounds(row, col):
            return None
        return self.grid[row][col]

    def set(self, row: int, col: int, piece: Optional[Piece]) -> None:
        """Place or remove a piece at the given position.
        
        Args:
            row: The row index.
            col: The column index.
            piece: The Piece to place, or None to clear the square.
        """
        if self.in_bounds(row, col):
            self.grid[row][col] = piece

    def move_piece(
        self,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int]
    ) -> None:
        """Move a piece from one position to another.
        
        Args:
            from_pos: Tuple of (row, col) for source position.
            to_pos: Tuple of (row, col) for destination position.
        """
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.get(from_row, from_col)
        self.set(from_row, from_col, None)
        self.set(to_row, to_col, piece)

    def remove_piece(self, row: int, col: int) -> None:
        """Remove a piece from the board.
        
        Args:
            row: The row index.
            col: The column index.
        """
        self.set(row, col, None)

    def draw(
        self,
        surface: 'pygame.Surface',
        font: 'pygame.font.Font',
        last_move: Optional[List[Tuple[int, int]]] = None
    ) -> None:
        """Render the board and pieces to a pygame surface.
        
        If pygame is unavailable, this method is a no-op.
        
        Args:
            surface: The pygame surface to draw on.
            font: The pygame font for rendering king text.
            last_move: Optional list of (row, col) tuples representing the last move path.
        """
        if pygame is None:
            logger.debug("Pygame unavailable; skipping board rendering")
            return

        self._draw_board_squares(surface)
        self._draw_move_highlights(surface, last_move)
        self._draw_pieces(surface, font)

    def _draw_board_squares(self, surface: 'pygame.Surface') -> None:
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
                # Alternate colors based on square parity
                color = (
                    DARK_COLOR if (row + col) % 2 == DARK_SQUARE_PARITY
                    else LIGHT_COLOR
                )
                pygame.draw.rect(surface, color, rect)

    def _draw_move_highlights(
        self,
        surface: 'pygame.Surface',
        last_move: Optional[List[Tuple[int, int]]]
    ) -> None:
        """Highlight the squares involved in the last move.
        
        Args:
            surface: The pygame surface to draw on.
            last_move: List of (row, col) tuples representing the move path.
        """
        if not last_move or len(last_move) < 2:
            return

        # Highlight each segment of the move path
        for i in range(len(last_move) - 1):
            from_row, from_col = last_move[i]
            to_row, to_col = last_move[i + 1]

            # Determine highlight color based on move type
            highlight_color = self._get_highlight_color(from_row, from_col, to_row, to_col)

            # Draw highlights on both source and destination squares
            self._draw_square_highlight(surface, from_row, from_col, highlight_color)
            self._draw_square_highlight(surface, to_row, to_col, highlight_color)

    @staticmethod
    def _get_highlight_color(
        from_row: int,
        from_col: int,
        to_row: int,
        to_col: int
    ) -> Tuple[int, int, int]:
        """Determine the highlight color based on move type.
        
        Args:
            from_row: Source row.
            from_col: Source column.
            to_row: Destination row.
            to_col: Destination column.
            
        Returns:
            RGB color tuple for the highlight.
        """
        # Capture moves span 2 squares diagonally
        if abs(to_row - from_row) == CAPTURE_DISTANCE and abs(to_col - from_col) == CAPTURE_DISTANCE:
            return HILITE_CAPTURE_COLOR
        return HILITE_MOVE_COLOR

    @staticmethod
    def _draw_square_highlight(
        surface: 'pygame.Surface',
        row: int,
        col: int,
        color: Tuple[int, int, int]
    ) -> None:
        """Draw a highlight border around a square.
        
        Args:
            surface: The pygame surface to draw on.
            row: The row index.
            col: The column index.
            color: RGB color tuple for the highlight.
        """
        rect = pygame.Rect(
            col * SQUARE_SIZE,
            row * SQUARE_SIZE,
            SQUARE_SIZE,
            SQUARE_SIZE
        )
        pygame.draw.rect(surface, color, rect, HIGHLIGHT_BORDER_WIDTH)

    def _draw_pieces(
        self,
        surface: 'pygame.Surface',
        font: 'pygame.font.Font'
    ) -> None:
        """Draw all pieces on the board.
        
        Args:
            surface: The pygame surface to draw on.
            font: The pygame font for rendering king text.
        """
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.grid[row][col]
                if piece:
                    self._draw_single_piece(surface, font, row, col, piece)

    @staticmethod
    def _draw_single_piece(
        surface: 'pygame.Surface',
        font: 'pygame.font.Font',
        row: int,
        col: int,
        piece: Piece
    ) -> None:
        """Draw a single piece on the board.
        
        Args:
            surface: The pygame surface to draw on.
            font: The pygame font for rendering king text.
            row: The row index.
            col: The column index.
            piece: The Piece object to draw.
        """
        # Calculate piece center position
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
            text = font.render("K", True, KING_TEXT_COLOR)
            text_rect = text.get_rect(center=center)
            surface.blit(text, text_rect)