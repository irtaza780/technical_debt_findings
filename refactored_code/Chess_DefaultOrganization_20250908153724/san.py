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
COORD_PATTERN = r'^[a-h][1-8][a-h][1-8][qrbnQRBN]?$'
COORD_REGEX = re.compile(COORD_PATTERN)
CASTLING_VARIANTS = ["o-o", "0-0", "O-O", "0-0-0", "o-o-o", "O-O-O"]
KINGSIDE_CASTLE_SAN = "O-O"
QUEENSIDE_CASTLE_SAN = "O-O-O"
PROMOTION_SEPARATOR = "="
CHECK_SUFFIX = "+"
CHECKMATE_SUFFIX = "#"
CAPTURE_SYMBOL = "x"
BOARD_COLS = 8
BOARD_ROWS = 8
COORD_FROM_START = 0
COORD_FROM_END = 2
COORD_TO_START = 2
COORD_TO_END = 4
COORD_PROMO_INDEX = 4


def _piece_letter(piece: str) -> str:
    """
    Convert a piece character to its SAN letter representation.
    
    Pawns return empty string, all other pieces return uppercase letter.
    
    Args:
        piece: Single character representing a chess piece
        
    Returns:
        Empty string for pawns, uppercase piece letter for others
    """
    uppercase_piece = piece.upper()
    return '' if uppercase_piece == PAWN_PIECE else uppercase_piece


def _is_capture(move: Move) -> bool:
    """
    Determine if a move is a capture.
    
    Args:
        move: Move object to check
        
    Returns:
        True if move captures a piece or is en passant, False otherwise
    """
    return move.capture is not None or move.is_en_passant


def _normalize_castle(notation: str) -> str:
    """
    Normalize castling notation by converting zeros and lowercase o's to uppercase O.
    
    Args:
        notation: Castling notation string (e.g., "0-0", "o-o", "O-O")
        
    Returns:
        Normalized castling notation with uppercase O's
    """
    normalized = notation.replace('0', 'O')
    normalized = normalized.replace('o', 'O')
    return normalized


def _get_disambiguation_suffix(move: Move, same_destination_moves: List[Move]) -> str:
    """
    Generate disambiguation suffix for moves with same destination square.
    
    When multiple pieces of the same type can move to the same square,
    disambiguation is needed. Prefers file, then rank, then full square.
    
    Args:
        move: The move being disambiguated
        same_destination_moves: Other moves to same destination by same piece type
        
    Returns:
        Disambiguation string (file, rank, or full square notation)
    """
    if not same_destination_moves:
        return ''
    
    from_file = move.from_sq % BOARD_COLS
    from_rank = move.from_sq // BOARD_COLS
    
    # Check if any conflicting moves share the same file or rank
    file_conflict = any(m.from_sq % BOARD_COLS == from_file for m in same_destination_moves)
    rank_conflict = any(m.from_sq // BOARD_COLS == from_rank for m in same_destination_moves)
    
    # Determine minimal disambiguation needed
    if file_conflict and rank_conflict:
        return index_to_square(move.from_sq)
    elif file_conflict:
        return index_to_square(move.from_sq)[1]  # rank
    elif rank_conflict:
        return index_to_square(move.from_sq)[0]  # file
    else:
        return index_to_square(move.from_sq)[0]  # file usually suffices


def _generate_san_for_non_castling_move(
    board: Board,
    move: Move,
    legal_moves: List[Move]
) -> str:
    """
    Generate SAN notation for non-castling moves.
    
    Args:
        board: Current board state
        move: Move to generate SAN for
        legal_moves: List of all legal moves in current position
        
    Returns:
        SAN string for the move (without check/checkmate suffix)
    """
    is_capture = _is_capture(move)
    piece_letter = _piece_letter(move.piece)
    
    # Find other moves to same destination by same piece type
    same_destination_moves = [
        m for m in legal_moves
        if m.to_sq == move.to_sq
        and m.piece.upper() == move.piece.upper()
        and m.from_sq != move.from_sq
    ]
    
    disambiguation = _get_disambiguation_suffix(move, same_destination_moves)
    destination = index_to_square(move.to_sq)
    
    # Pawn captures require source file
    if move.piece.upper() == PAWN_PIECE and is_capture:
        source_file = index_to_square(move.from_sq)[0]
        san = f"{source_file}{CAPTURE_SYMBOL}{destination}"
    else:
        capture_symbol = CAPTURE_SYMBOL if is_capture else ''
        san = f"{piece_letter}{disambiguation}{capture_symbol}{destination}"
    
    # Add promotion notation
    if move.promotion:
        san += f"{PROMOTION_SEPARATOR}{move.promotion.upper()}"
    
    return san


def _generate_san_for_castling(move: Move) -> str:
    """
    Generate SAN notation for castling moves.
    
    Args:
        move: Castling move
        
    Returns:
        "O-O" for kingside castling, "O-O-O" for queenside
    """
    destination_col = move.to_sq % BOARD_COLS
    return KINGSIDE_CASTLE_SAN if destination_col == KINGSIDE_CASTLE_DEST_COL else QUEENSIDE_CASTLE_SAN


def _add_check_or_checkmate_suffix(board: Board, move: Move, san: str) -> str:
    """
    Add check or checkmate suffix to SAN notation.
    
    Args:
        board: Board state (will be modified and restored)
        move: Move to check for check/checkmate
        san: Current SAN string
        
    Returns:
        SAN string with appropriate suffix added
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
    
    Generates complete SAN including piece letter, disambiguation,
    capture symbol, destination, promotion, and check/checkmate suffix.
    
    Args:
        board: Current board state (will be temporarily modified)
        move: Legal move to generate SAN for
        legal_moves: Optional list of legal moves (generated if not provided)
        
    Returns:
        Complete SAN string for the move
    """
    if legal_moves is None:
        legal_moves = board.generate_legal_moves()
    
    # Handle castling
    if move.is_castling and move.piece.upper() == KING_PIECE:
        san = _generate_san_for_castling(move)
    else:
        san = _generate_san_for_non_castling_move(board, move, legal_moves)
    
    # Add check/checkmate suffix
    san = _add_check_or_checkmate_suffix(board, move, san)
    
    return san


def legal_moves_san_map(board: Board) -> Dict[str, Move]:
    """
    Create mapping of SAN notation variants to legal moves.
    
    Generates multiple notation variants for each move to handle
    different input formats (with/without check suffix, castling variants, etc).
    
    Args:
        board: Current board state
        
    Returns:
        Dictionary mapping lowercase SAN strings to Move objects
    """
    moves = board.generate_legal_moves()
    mapping: Dict[str, Move] = {}
    
    for move in moves:
        san = generate_san_for_move(board, move, moves)
        canonical_key = san.lower()
        mapping[canonical_key] = move
        
        # Allow notation without check/checkmate suffix
        base_san = san.rstrip(f'{CHECK_SUFFIX}{CHECKMATE_SUFFIX}').lower()
        mapping[base_san] = move
        
        # For castling, accept multiple notation variants
        if base_san in ("o-o", "o-o-o"):
            for variant in CASTLING_VARIANTS:
                mapping[variant.lower()] = move
        
        # For promotion, accept notation without '=' separator
        if PROMOTION_SEPARATOR in base_san:
            without_separator = base_san.replace(PROMOTION_SEPARATOR, '')
            mapping[without_separator] = move
    
    return mapping


def _parse_coordinate_notation(board: Board, coordinate: str) -> Optional[Move]:
    """
    Parse coordinate notation (e.g., "e2e4" or "g7g8q") into a Move.
    
    Args:
        board: Current board state
        coordinate: Coordinate notation string
        
    Returns:
        Matching legal Move, or None if no match found
    """
    source_square = square_to_index(coordinate[COORD_FROM_START:COORD_FROM_END])
    destination_square = square_to_index(coordinate[COORD_TO_START:COORD_TO_END])
    
    promotion_piece = None
    if len(coordinate) == 5:
        promotion_char = coordinate[COORD_PROMO_INDEX].upper()
        promotion_piece = promotion_char if board.white_to_move else promotion_char.lower()
    
    # Find matching legal move
    for move in board.generate_legal_moves():
        if move.from_sq != source_square or move.to_sq != destination_square:
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
            return move
    
    return None


def _parse_san_with_default_promotion(san_map: Dict[str, Move], base_notation: str) -> Optional[Move]:
    """
    Attempt to parse SAN notation with default queen promotion.
    
    Handles cases where promotion piece is omitted (e.g., "e8" instead of "e8=Q").
    
    Args:
        san_map: Mapping of SAN strings to moves
        base_notation: Base notation without check/checkmate suffix
        
    Returns:
        Move if found with default queen promotion, None otherwise
    """
    if not base_notation:
        return None
    
    # Try with '=' separator
    with_separator = f"{base_notation}{PROMOTION_SEPARATOR}{QUEEN_PIECE.lower()}"
    if with_separator in san_map:
        return san_map[with_separator]
    
    # Try without separator
    without_separator = f"{base_notation}{QUEEN_PIECE.lower()}"
    if without_separator in san_map:
        return san_map[without_separator]
    
    return None


def parse_user_input(board: Board, text: str) -> Optional[Move]:
    """
    Parse user input into a legal Move.
    
    Accepts multiple formats:
    - Standard Algebraic Notation (SAN): e.g., "e4", "Nf3", "O-O"
    - Coordinate notation: e.g., "e2e4", "g7g8q"
    - Castling variants: "0-0", "o-o", "O-O", etc.
    - Promotion without piece: defaults to queen
    
    Args:
        board: Current board state
        text: User input string
        
    Returns:
        Matching legal Move, or None if input is invalid or ambiguous
    """
    user_input = text.strip()
    if not user_input:
        return None
    
    # Try SAN notation first
    san_map = legal_moves_san_map(board)
    normalized_input = _normalize_castle(user_input).strip()
    lowercase_input = normalized_input.lower()
    
    if lowercase_input in san_map:
        return san_map[lowercase_input]
    
    # Try coordinate notation
    if COORD_REGEX.match(lowercase_input):
        move = _parse_coordinate_notation(board, lowercase_input)
        if move is not None:
            return move
    
    # Try SAN with default queen promotion
    base_notation = lowercase_input.rstrip(f'{CHECK_SUFFIX}{CHECKMATE_SUFFIX}')
    move = _parse_san_with_default_promotion(san_map, base_notation)
    if move is not None:
        return move
    
    return None