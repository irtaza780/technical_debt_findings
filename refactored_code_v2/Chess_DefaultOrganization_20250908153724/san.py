import logging
import re
from typing import Dict, List, Optional

from board import Board
from move import Move
from utils import index_to_square, square_to_index

logger = logging.getLogger(__name__)

# Constants
PAWN_PIECE = 'P'
KING_PIECE = 'K'
QUEEN_PIECE = 'Q'
KINGSIDE_CASTLE_DEST_COL = 6
QUEENSIDE_CASTLE_DEST_COL = 2
KINGSIDE_CASTLE_SAN = "O-O"
QUEENSIDE_CASTLE_SAN = "O-O-O"
COORD_PATTERN = r'^[a-h][1-8][a-h][1-8][qrbnQRBN]?$'
COORD_RE = re.compile(COORD_PATTERN)
PROMOTION_PIECES = {'Q', 'R', 'B', 'N'}
CHECK_SUFFIX = '+'
CHECKMATE_SUFFIX = '#'
CAPTURE_SYMBOL = 'x'
PROMOTION_SEPARATOR = '='
CASTLING_VARIANTS = ["o-o", "0-0", "O-O", "0-0-0", "o-o-o", "O-O-O"]
CASTLING_KEYS = ("o-o", "o-o-o")
BOARD_COLS = 8
BOARD_ROWS = 8


def _piece_letter(piece: str) -> str:
    """
    Convert a piece character to its SAN letter representation.
    
    Args:
        piece: Single character representing a chess piece (e.g., 'P', 'N', 'K')
    
    Returns:
        Empty string for pawns, uppercase piece letter for other pieces
    """
    uppercase_piece = piece.upper()
    return '' if uppercase_piece == PAWN_PIECE else uppercase_piece


def _is_capture(move: Move) -> bool:
    """
    Determine if a move is a capture.
    
    Args:
        move: The move to check
    
    Returns:
        True if the move captures a piece or is en passant, False otherwise
    """
    return move.capture is not None or move.is_en_passant


def _normalize_castle(notation: str) -> str:
    """
    Normalize castling notation by converting zeros and lowercase 'o' to uppercase 'O'.
    
    Args:
        notation: Castling notation string (e.g., '0-0', 'o-o', 'O-O')
    
    Returns:
        Normalized castling notation with uppercase 'O'
    """
    normalized = notation.replace('0', 'O')
    normalized = normalized.replace('o', 'O')
    return normalized


def _get_file_and_rank(square_index: int) -> tuple[int, int]:
    """
    Extract file (column) and rank (row) from a square index.
    
    Args:
        square_index: Index of the square (0-63)
    
    Returns:
        Tuple of (file, rank) where file is 0-7 (a-h) and rank is 0-7 (1-8)
    """
    file = square_index % BOARD_COLS
    rank = square_index // BOARD_COLS
    return file, rank


def _find_disambiguation(move: Move, same_destination_moves: List[Move]) -> str:
    """
    Determine the disambiguation string needed for a move.
    
    When multiple pieces of the same type can move to the same destination,
    disambiguation is needed. Preference: file > rank > full square.
    
    Args:
        move: The move being disambiguated
        same_destination_moves: Other moves to the same destination with same piece type
    
    Returns:
        Disambiguation string (file letter, rank number, or full square notation)
    """
    if not same_destination_moves:
        return ''
    
    from_file, from_rank = _get_file_and_rank(move.from_sq)
    
    # Check if any conflicting move shares the same file
    file_conflict = any(
        _get_file_and_rank(m.from_sq)[0] == from_file 
        for m in same_destination_moves
    )
    
    # Check if any conflicting move shares the same rank
    rank_conflict = any(
        _get_file_and_rank(m.from_sq)[1] == from_rank 
        for m in same_destination_moves
    )
    
    # Determine disambiguation based on conflicts
    if file_conflict and rank_conflict:
        return index_to_square(move.from_sq)
    elif file_conflict:
        return index_to_square(move.from_sq)[1]  # rank
    elif rank_conflict:
        return index_to_square(move.from_sq)[0]  # file
    else:
        return index_to_square(move.from_sq)[0]  # file usually suffices


def _find_same_destination_moves(
    board: Board,
    move: Move,
    piece: str,
    legal_moves: List[Move]
) -> List[Move]:
    """
    Find all legal moves with the same destination and piece type (excluding the given move).
    
    Args:
        board: The current board state
        move: The reference move
        piece: The piece type to match
        legal_moves: List of all legal moves
    
    Returns:
        List of moves with same destination and piece type, excluding the given move
    """
    return [
        m for m in legal_moves
        if m.to_sq == move.to_sq
        and m.piece.upper() == piece.upper()
        and m.from_sq != move.from_sq
    ]


def _generate_castling_san(move: Move) -> str:
    """
    Generate SAN notation for a castling move.
    
    Args:
        move: A castling move
    
    Returns:
        'O-O' for kingside castling, 'O-O-O' for queenside castling
    """
    destination_col = move.to_sq % BOARD_COLS
    return KINGSIDE_CASTLE_SAN if destination_col == KINGSIDE_CASTLE_DEST_COL else QUEENSIDE_CASTLE_SAN


def _generate_pawn_capture_san(move: Move, destination: str) -> str:
    """
    Generate SAN notation for a pawn capture.
    
    Args:
        move: A pawn capture move
        destination: Destination square in algebraic notation
    
    Returns:
        SAN string for pawn capture (e.g., 'exd4')
    """
    source_file = index_to_square(move.from_sq)[0]
    return f"{source_file}{CAPTURE_SYMBOL}{destination}"


def _generate_piece_san(
    move: Move,
    piece_letter: str,
    disambiguation: str,
    is_capture: bool,
    destination: str
) -> str:
    """
    Generate SAN notation for a non-pawn, non-castling move.
    
    Args:
        move: The move
        piece_letter: SAN letter for the piece
        disambiguation: Disambiguation string if needed
        is_capture: Whether the move is a capture
        destination: Destination square in algebraic notation
    
    Returns:
        SAN string for the move
    """
    capture_symbol = CAPTURE_SYMBOL if is_capture else ''
    san = f"{piece_letter}{disambiguation}{capture_symbol}{destination}"
    
    # Add promotion notation if applicable
    if move.promotion:
        san += f"{PROMOTION_SEPARATOR}{move.promotion.upper()}"
    
    return san


def _add_check_or_checkmate_suffix(board: Board, move: Move, san: str) -> str:
    """
    Add check or checkmate suffix to SAN notation.
    
    Args:
        board: The board state
        move: The move to evaluate
        san: The SAN string to augment
    
    Returns:
        SAN string with check/checkmate suffix if applicable
    """
    state = board.make_move(move)
    try:
        if board.is_checkmate():
            san += CHECKMATE_SUFFIX
        elif board.in_check(board.white_to_move):
            san += CHECK_SUFFIX
    finally:
        board.undo_move(move, state)
    
    return san


def generate_san_for_move(
    board: Board,
    move: Move,
    legal_moves: Optional[List[Move]] = None
) -> str:
    """
    Generate Standard Algebraic Notation (SAN) for a legal move.
    
    Args:
        board: The current board state (before making the move)
        move: The move to generate SAN for
        legal_moves: Optional list of legal moves (generated if not provided)
    
    Returns:
        SAN string representation of the move
    """
    piece = move.piece
    
    # Handle castling
    if move.is_castling and piece.upper() == KING_PIECE:
        san = _generate_castling_san(move)
    else:
        # Generate SAN for regular moves
        is_capture = _is_capture(move)
        piece_letter = _piece_letter(piece)
        
        # Determine disambiguation for non-pawn moves
        disambiguation = ''
        if piece_letter:
            if legal_moves is None:
                legal_moves = board.generate_legal_moves()
            
            same_destination_moves = _find_same_destination_moves(
                board, move, piece, legal_moves
            )
            disambiguation = _find_disambiguation(move, same_destination_moves)
        
        destination = index_to_square(move.to_sq)
        
        # Generate appropriate SAN based on move type
        if piece.upper() == PAWN_PIECE and is_capture:
            san = _generate_pawn_capture_san(move, destination)
        else:
            san = _generate_piece_san(
                move, piece_letter, disambiguation, is_capture, destination
            )
    
    # Add check/checkmate suffix
    san = _add_check_or_checkmate_suffix(board, move, san)
    
    return san


def _add_san_variants_to_map(
    san_map: Dict[str, Move],
    san: str,
    move: Move
) -> None:
    """
    Add all variants of a SAN string to the mapping.
    
    Includes canonical form, form without check/mate suffix, castling variants,
    and promotion variants without the '=' separator.
    
    Args:
        san_map: Dictionary to populate with SAN variants
        san: The canonical SAN string
        move: The move object to map to
    """
    # Canonical form
    san_map[san.lower()] = move
    
    # Without check/mate suffix
    base = san.rstrip(f'{CHECK_SUFFIX}{CHECKMATE_SUFFIX}').lower()
    san_map[base] = move
    
    # Castling variants
    if base in CASTLING_KEYS:
        for variant in CASTLING_VARIANTS:
            san_map[variant.lower()] = move
    
    # Promotion without '=' separator
    if PROMOTION_SEPARATOR in base:
        no_equals = base.replace(PROMOTION_SEPARATOR, '')
        san_map[no_equals] = move


def legal_moves_san_map(board: Board) -> Dict[str, Move]:
    """
    Generate a mapping of SAN notation variants to legal moves.
    
    Includes multiple acceptable formats for each move (e.g., with/without check suffix,
    castling variants, promotion variants).
    
    Args:
        board: The current board state
    
    Returns:
        Dictionary mapping lowercase SAN strings to Move objects
    """
    moves = board.generate_legal_moves()
    san_map: Dict[str, Move] = {}
    
    for move in moves:
        san = generate_san_for_move(board, move, moves)
        _add_san_variants_to_map(san_map, san, move)
    
    return san_map


def _match_coordinate_notation(board: Board, coordinate: str) -> Optional[Move]:
    """
    Parse and match a move in coordinate notation (e.g., 'e2e4', 'g7g8q').
    
    Args:
        board: The current board state
        coordinate: Coordinate notation string
    
    Returns:
        The matching legal move, or None if no match found
    """
    source_index = square_to_index(coordinate[0:2])
    destination_index = square_to_index(coordinate[2:4])
    promotion_piece = None
    
    # Extract promotion piece if specified
    if len(coordinate) == 5:
        promotion_char = coordinate[4].upper()
        promotion_piece = promotion_char if board.white_to_move else promotion_char.lower()
    
    # Find matching legal move
    for move in board.generate_legal_moves():
        if move.from_sq != source_index or move.to_sq != destination_index:
            continue
        
        # Handle promotion moves
        if move.promotion is not None:
            if promotion_piece is None:
                # Default to queen if promotion not specified
                if move.promotion.upper() == QUEEN_PIECE:
                    return move
            elif promotion_piece == move.promotion:
                return move
        else:
            # Non-promotion move
            return move
    
    return None


def _try_default_queen_promotion(san_map: Dict[str, Move], base: str) -> Optional[Move]:
    """
    Attempt to match a move by defaulting to queen promotion.
    
    Used when a promotion move is specified without the promotion piece.
    
    Args:
        san_map: Mapping of SAN strings to moves
        base: Base SAN string without check/mate suffix
    
    Returns:
        The matching move with queen promotion, or None if not found
    """
    for variant in [f"{base}{PROMOTION_SEPARATOR}{QUEEN_PIECE.lower()}", f"{base}{QUEEN_PIECE.lower()}"]:
        if variant in san_map:
            return san_map[variant]
    
    return None


def parse_user_input(board: Board, text: str) -> Optional[Move]:
    """
    Parse user input and return the corresponding legal move.
    
    Accepts multiple formats:
    - Standard Algebraic Notation (SAN): e.g., 'e4', 'Nf3', 'O-O', 'e8=Q'
    - Coordinate notation: e.g., 'e2e4', 'g7g8q'
    - Castling variants: '0-0', 'o-o', 'O-O', etc.
    
    Args:
        board: The current board state
        text: User input string
    
    Returns:
        The matching legal Move object, or None if input is invalid or ambiguous
    """
    user_input = text.strip()
    if not user_input:
        return None
    
    # Try SAN mapping
    san_map = legal_moves_san_map(board)
    normalized_input = _normalize_castle(user_input).strip()
    input_key = normalized_input.lower()
    
    if input_key in san_map:
        return san_map[input_key]
    
    # Try coordinate notation
    if COORD_RE.match(input_key):
        return _match_coordinate_notation(board, input_key)
    
    # Try defaulting to queen promotion for incomplete promotion notation
    base = input_key.rstrip(f'{CHECK_SUFFIX}{CHECKMATE_SUFFIX}')
    if base:
        return _try_default_queen_promotion(san_map, base)
    
    return None