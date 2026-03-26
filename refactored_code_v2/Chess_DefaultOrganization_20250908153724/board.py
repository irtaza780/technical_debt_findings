import logging
from typing import List, Optional, Dict, Tuple
from copy import deepcopy
from utils import index_to_coord, coord_to_index, is_white
from move import Move, MoveState

logger = logging.getLogger(__name__)

# Board dimensions and piece movement constants
BOARD_SIZE = 8
BOARD_SQUARES = 64
EMPTY_SQUARE = None

# Piece type constants
PAWN = 'P'
KNIGHT = 'N'
BISHOP = 'B'
ROOK = 'R'
QUEEN = 'Q'
KING = 'K'

# Direction vectors for piece movement
PAWN_CAPTURE_DIRECTIONS = [(-1, -1), (-1, 1)]
KNIGHT_MOVES = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
BISHOP_DIRECTIONS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
QUEEN_DIRECTIONS = BISHOP_DIRECTIONS + ROOK_DIRECTIONS
KING_DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# Promotion piece options
PROMOTION_PIECES = ['Q', 'R', 'B', 'N']

# Castling constants
WHITE_KING_START = coord_to_index(7, 4)
WHITE_ROOK_KINGSIDE = coord_to_index(7, 7)
WHITE_ROOK_QUEENSIDE = coord_to_index(7, 0)
BLACK_KING_START = coord_to_index(0, 4)
BLACK_ROOK_KINGSIDE = coord_to_index(0, 7)
BLACK_ROOK_QUEENSIDE = coord_to_index(0, 0)

# Castling target squares
WHITE_KINGSIDE_KING_TARGET = coord_to_index(7, 6)
WHITE_QUEENSIDE_KING_TARGET = coord_to_index(7, 2)
BLACK_KINGSIDE_KING_TARGET = coord_to_index(0, 6)
BLACK_QUEENSIDE_KING_TARGET = coord_to_index(0, 2)


class Board:
    """
    Represents a chess board with move generation, legality checking, and move execution.
    
    The board is stored as a 64-element list where index 0 = a8 and index 63 = h1.
    Pieces are represented as uppercase letters for white and lowercase for black.
    """

    def __init__(self):
        """Initialize an empty chess board."""
        self.squares: List[Optional[str]] = [EMPTY_SQUARE] * BOARD_SQUARES
        self.white_to_move: bool = True
        self.castling: Dict[str, bool] = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant: Optional[int] = EMPTY_SQUARE

    def setup_start_position(self) -> None:
        """Set up the standard chess starting position."""
        setup = [
            'r', 'n', 'b', 'q', 'k', 'b', 'n', 'r',
            'p', 'p', 'p', 'p', 'p', 'p', 'p', 'p',
            EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE,
            EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE,
            EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE,
            EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE, EMPTY_SQUARE,
            'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P',
            'R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R',
        ]
        self.squares = setup
        self.white_to_move = True
        self.castling = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant = EMPTY_SQUARE

    def print_board(self) -> None:
        """Print an ASCII representation of the board to the logger."""
        logger.info("  +------------------------+")
        for row in range(BOARD_SIZE):
            rank = BOARD_SIZE - row
            line = f"{rank} |"
            for col in range(BOARD_SIZE):
                idx = row * BOARD_SIZE + col
                piece = self.squares[idx]
                char = piece if piece is not None else '.'
                line += f" {char} "
            line += "|"
            logger.info(line)
        logger.info("  +------------------------+")
        logger.info("    a  b  c  d  e  f  g  h")

    def get_king_square(self, white: bool) -> int:
        """
        Find the square index of the king for the given side.
        
        Args:
            white: True to find white king, False for black king.
            
        Returns:
            The square index of the king.
            
        Raises:
            RuntimeError: If the king is not found on the board.
        """
        target = KING if white else KING.lower()
        for idx, piece in enumerate(self.squares):
            if piece == target:
                return idx
        raise RuntimeError(f"{'White' if white else 'Black'} king not found on board")

    def _is_square_attacked_by_pawn(self, square: int, by_white: bool) -> bool:
        """
        Check if a square is attacked by an enemy pawn.
        
        Args:
            square: The square index to check.
            by_white: True if checking for white pawn attacks, False for black.
            
        Returns:
            True if the square is attacked by a pawn of the specified color.
        """
        row, col = index_to_coord(square)
        pawn_dirs = PAWN_CAPTURE_DIRECTIONS if by_white else [(1, -1), (1, 1)]
        pawn_piece = PAWN if by_white else PAWN.lower()
        
        for dr, dc in pawn_dirs:
            attack_row, attack_col = row + dr, col + dc
            if 0 <= attack_row < BOARD_SIZE and 0 <= attack_col < BOARD_SIZE:
                attack_idx = attack_row * BOARD_SIZE + attack_col
                if self.squares[attack_idx] == pawn_piece:
                    return True
        return False

    def _is_square_attacked_by_knight(self, square: int, by_white: bool) -> bool:
        """
        Check if a square is attacked by an enemy knight.
        
        Args:
            square: The square index to check.
            by_white: True if checking for white knight attacks, False for black.
            
        Returns:
            True if the square is attacked by a knight of the specified color.
        """
        row, col = index_to_coord(square)
        knight_piece = KNIGHT if by_white else KNIGHT.lower()
        
        for dr, dc in KNIGHT_MOVES:
            knight_row, knight_col = row + dr, col + dc
            if 0 <= knight_row < BOARD_SIZE and 0 <= knight_col < BOARD_SIZE:
                knight_idx = knight_row * BOARD_SIZE + knight_col
                if self.squares[knight_idx] == knight_piece:
                    return True
        return False

    def _is_square_attacked_by_sliding_piece(self, square: int, by_white: bool, 
                                             directions: List[Tuple[int, int]], 
                                             piece_types: List[str]) -> bool:
        """
        Check if a square is attacked by a sliding piece (bishop, rook, or queen).
        
        Args:
            square: The square index to check.
            by_white: True if checking for white piece attacks, False for black.
            directions: List of direction tuples to check.
            piece_types: List of piece type characters to match.
            
        Returns:
            True if the square is attacked by a sliding piece of the specified type.
        """
        row, col = index_to_coord(square)
        
        for dr, dc in directions:
            attack_row, attack_col = row + dr, col + dc
            while 0 <= attack_row < BOARD_SIZE and 0 <= attack_col < BOARD_SIZE:
                attack_idx = attack_row * BOARD_SIZE + attack_col
                piece = self.squares[attack_idx]
                
                if piece is not None:
                    # Check if piece matches type and color
                    piece_upper = piece.upper()
                    if piece_upper in piece_types and is_white(piece) == by_white:
                        return True
                    break
                
                attack_row += dr
                attack_col += dc
        
        return False

    def _is_square_attacked_by_king(self, square: int, by_white: bool) -> bool:
        """
        Check if a square is attacked by an enemy king.
        
        Args:
            square: The square index to check.
            by_white: True if checking for white king attacks, False for black.
            
        Returns:
            True if the square is attacked by a king of the specified color.
        """
        row, col = index_to_coord(square)
        king_piece = KING if by_white else KING.lower()
        
        for dr, dc in KING_DIRECTIONS:
            king_row, king_col = row + dr, col + dc
            if 0 <= king_row < BOARD_SIZE and 0 <= king_col < BOARD_SIZE:
                king_idx = king_row * BOARD_SIZE + king_col
                if self.squares[king_idx] == king_piece:
                    return True
        return False

    def is_square_attacked(self, square: int, by_white: bool) -> bool:
        """
        Check if a square is attacked by the specified side.
        
        Args:
            square: The square index to check.
            by_white: True to check for white attacks, False for black.
            
        Returns:
            True if the square is attacked by the specified side.
        """
        if self._is_square_attacked_by_pawn(square, by_white):
            return True
        if self._is_square_attacked_by_knight(square, by_white):
            return True
        if self._is_square_attacked_by_sliding_piece(square, by_white, BISHOP_DIRECTIONS, [BISHOP, QUEEN]):
            return True
        if self._is_square_attacked_by_sliding_piece(square, by_white, ROOK_DIRECTIONS, [ROOK, QUEEN]):
            return True
        if self._is_square_attacked_by_king(square, by_white):
            return True
        return False

    def in_check(self, white: bool) -> bool:
        """
        Check if the specified side is in check.
        
        Args:
            white: True to check if white is in check, False for black.
            
        Returns:
            True if the specified side is in check.
        """
        king_sq = self.get_king_square(white)
        return self.is_square_attacked(king_sq, not white)

    def _add_move(self, moves: List[Move], from_idx: int, to_idx: int, 
                  promotion: Optional[str] = None, is_en_passant: bool = False, 
                  is_castling: bool = False) -> None:
        """
        Add a move to the move list.
        
        Args:
            moves: The list to add the move to.
            from_idx: Source square index.
            to_idx: Destination square index.
            promotion: Promotion piece if applicable.
            is_en_passant: True if the move is an en passant capture.
            is_castling: True if the move is a castling move.
        """
        piece = self.squares[from_idx]
        capture_piece = self.squares[to_idx]
        
        if is_en_passant:
            # For en passant, the captured pawn is not on the destination square
            capture_piece = PAWN.lower() if piece.isupper() else PAWN
        
        moves.append(Move(
            from_sq=from_idx,
            to_sq=to_idx,
            piece=piece,
            capture=capture_piece,
            promotion=promotion,
            is_en_passant=is_en_passant,
            is_castling=is_castling
        ))

    def _generate_pawn_moves(self, moves: List[Move], from_idx: int, piece: str) -> None:
        """
        Generate all pseudo-legal pawn moves from a square.
        
        Args:
            moves: The list to add moves to.
            from_idx: Source square index.
            piece: The pawn piece character.
        """
        is_white_pawn = piece.isupper()
        direction = -1 if is_white_pawn else 1
        start_row = 6 if is_white_pawn else 1
        promotion_row = 0 if is_white_pawn else 7
        
        row, col = index_to_coord(from_idx)
        
        # Single square forward
        forward_row = row + direction
        if 0 <= forward_row < BOARD_SIZE:
            forward_idx = forward_row * BOARD_SIZE + col
            if self.squares[forward_idx] is EMPTY_SQUARE:
                if forward_row == promotion_row:
                    # Add promotion moves
                    for promo_type in PROMOTION_PIECES:
                        promo_piece = promo_type if is_white_pawn else promo_type.lower()
                        self._add_move(moves, from_idx, forward_idx, promotion=promo_piece)
                else:
                    self._add_move(moves, from_idx, forward_idx)
                
                # Double square forward from starting position
                if row == start_row:
                    double_forward_row = row + 2 * direction
                    between_idx = (row + direction) * BOARD_SIZE + col
                    double_forward_idx = double_forward_row * BOARD_SIZE + col
                    if (self.squares[between_idx] is EMPTY_SQUARE and 
                        self.squares[double_forward_idx] is EMPTY_SQUARE):
                        self._add_move(moves, from_idx, double_forward_idx)
        
        # Captures
        for dc in [-1, 1]:
            capture_row = row + direction
            capture_col = col + dc
            if 0 <= capture_row < BOARD_SIZE and 0 <= capture_col < BOARD_SIZE:
                capture_idx = capture_row * BOARD_SIZE + capture_col
                target_piece = self.squares[capture_idx]
                if target_piece is not EMPTY_SQUARE and is_white(target_piece) != is_white_pawn:
                    if capture_row == promotion_row:
                        for promo_type in PROMOTION_PIECES:
                            promo_piece = promo_type if is_white_pawn else promo_type.lower()
                            self._add_move(moves, from_idx, capture_idx, promotion=promo_piece)
                    