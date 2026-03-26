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
KINGSIDE_CASTLE_DEST_COL = 6
QUEENSIDE_CASTLE_DEST_COL = 2
QUEEN_PROMOTION = 'Q'
COORD_PATTERN = re.compile(r'^[a-h][1-8][a-h][1-8][qrbnQRBN]?$')
CASTLING_VARIANTS = ["o-o", "0-0", "O-O", "0-0-0", "o-o-o", "O-O-O"]
KINGSIDE_CASTLE_SAN = "O-O"
QUEENSIDE_CASTLE_SAN = "O-O-O"
CHECKMATE_SUFFIX = "#"
CHECK_SUFFIX = "+"
PROMOTION_SEPARATOR = "="
CAPTURE_SYMBOL = "x"
BOARD_COLS = 8
BOARD_ROWS = 8
COORD_FROM_INDEX = slice(0, 2)
COORD_TO_INDEX = slice(2, 4)
COORD_PROMOTION_INDEX = 4


def _piece_letter(piece: str) -> str:
    """
    Convert a piece character to its SAN letter representation.
    
    Args:
        piece: A single character representing a chess piece (e.g., 'P', 'N', 'K')
        
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


def _normalize_castle_notation(notation: str) -> str:
    """
    Normalize castling notation by converting zeros and lowercase 'o' to uppercase 'O'.
    
    Args:
        notation: Castling notation string (e.g., '0-0', 'o-o', 'O-O')
        
    Returns:
        Normalized castling notation with uppercase 'O'
    """
    notation = notation.replace('0', 'O')
    notation = notation.replace('o', 'O')
    return notation


def _get_destination_square(move: Move) -> str:
    """
    Get the destination square in algebraic notation.
    
    Args:
        move: The move to get destination for
        
    Returns:
        Destination square in algebraic notation (e.g., 'e4')
    """
    return index_to_square(move.to_sq)


def _get_source_file(move: Move) -> str:
    """
    Get the source file (column) of a move in algebraic notation.
    
    Args:
        move: The move to get source file for
        
    Returns:
        Source file letter (e.g., 'e')
    """
    return index_to_square(move.from_sq)[0]


def _get_source_rank(move: Move) -> str:
    """
    Get the source rank (row) of a move in algebraic notation.
    
    Args:
        move: The move to get source rank for
        
    Returns:
        Source rank number (e.g., '4')
    """
    return index_to_square(move.from_sq)[1]


def _find_conflicting_moves(
    legal_moves: List[Move],
    target_square: int,
    piece_type: str,
    exclude_from_square: int
) -> List[Move]:
    """
    Find all legal moves that move the same piece type to the same destination.
    
    Args:
        legal_moves: List of all legal moves in the position
        target_square: Destination square index
        piece_type: Uppercase piece character (e.g., 'N', 'R')
        exclude_from_square: Source square to exclude from results
        
    Returns:
        List of conflicting moves
    """
    return [
        move for move in legal_moves
        if move.to_sq == target_square
        and move.piece.upper() == piece_type
        and move.from_sq != exclude_from_square
    ]


def _calculate_disambiguation(
    move: Move,
    conflicting_moves: List[Move]
) -> str:
    """
    Calculate the disambiguation string needed for a move in SAN notation.
    
    Args:
        move: The move to disambiguate
        conflicting_moves: Other moves moving the same piece to the same square
        
    Returns:
        Disambiguation string (empty, file letter, rank number, or full square)
    """
    if not conflicting_moves:
        return ''
    
    source_file = move.from_sq % BOARD_COLS
    source_rank = move.from_sq // BOARD_COLS
    
    # Check if any conflicting move shares the same file
    file_conflict = any(m.from_sq % BOARD_COLS == source_file for m in conflicting_moves)
    # Check if any conflicting move shares the same rank
    rank_conflict = any(m.from_sq // BOARD_COLS == source_rank for m in conflicting_moves)
    
    if file_conflict and rank_conflict:
        # Both file and rank conflict: use full square
        return index_to_square(move.from_sq)
    elif file_conflict:
        # File conflict: use rank
        return _get_source_rank(move)
    elif rank_conflict:
        # Rank conflict: use file
        return _get_source_file(move)
    else:
        # Default to file
        return _get_source_file(move)


def _generate_pawn_capture_san(move: Move) -> str:
    """
    Generate SAN for a pawn capture move.
    
    Args:
        move: A pawn capture move
        
    Returns:
        SAN string for the pawn capture (e.g., 'exd4')
    """
    source_file = _get_source_file(move)
    destination = _get_destination_square(move)
    return f"{source_file}{CAPTURE_SYMBOL}{destination}"


def _generate_castling_san(move: Move) -> str:
    """
    Generate SAN for a castling move.
    
    Args:
        move: A castling move
        
    Returns:
        SAN string for castling ('O-O' or 'O-O-O')
    """
    destination_col = move.to_sq % BOARD_COLS
    return KINGSIDE_CASTLE_SAN if destination_col == KINGSIDE_CASTLE_DEST_COL else QUEENSIDE_CASTLE_SAN


def _generate_standard_san(
    move: Move,
    piece_letter: str,
    disambiguation: str,
    is_capture: bool
) -> str:
    """
    Generate SAN for a standard (non-pawn, non-castling) move.
    
    Args:
        move: The move to generate SAN for
        piece_letter: The piece letter (e.g., 'N', 'R')
        disambiguation: Disambiguation string if needed
        is_capture: Whether the move is a capture
        
    Returns:
        SAN string for the move
    """
    destination = _get_destination_square(move)
    capture_symbol = CAPTURE_SYMBOL if is_capture else ''
    return f"{piece_letter}{disambiguation}{capture_symbol}{destination}"


def _add_promotion_suffix(san: str, move: Move) -> str:
    """
    Add promotion suffix to SAN if the move is a promotion.
    
    Args:
        san: The SAN string to modify
        move: The move being converted to SAN
        
    Returns:
        SAN string with promotion suffix if applicable
    """
    if move.promotion:
        san += f"{PROMOTION_SEPARATOR}{move.promotion.upper()}"
    return san


def _add_check_suffix(san: str, board: Board, move: Move) -> str:
    """
    Add check or checkmate suffix to SAN based on board state after the move.
    
    Args:
        san: The SAN string to modify
        board: The board object
        move: The move being converted to SAN
        
    Returns:
        SAN string with check/checkmate suffix if applicable
    """
    # Make the move temporarily to check for check/checkmate
    state = board.make_move(move)
    try:
        if board.is_checkmate():
            san += CHECKMATE_SUFFIX
        elif board.in_check(board.white_to_move):
            san += CHECK_SUFFIX
    finally:
        # Always undo the move
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
        board: The current board state
        move: The move to convert to SAN
        legal_moves: Optional list of legal moves (generated if not provided)
        
    Returns:
        SAN string representation of the move
    """
    piece = move.piece
    
    # Handle castling
    if move.is_castling and piece.upper() == KING_PIECE:
        san = _generate_castling_san(move)
    else:
        is_capture = _is_capture(move)
        piece_letter = _piece_letter(piece)
        disambiguation = ''
        
        # Calculate disambiguation for non-pawn moves
        if piece_letter:
            if legal_moves is None:
                legal_moves = board.generate_legal_moves()
            
            conflicting_moves = _find_conflicting_moves(
                legal_moves,
                move.to_sq,
                piece.upper(),
                move.from_sq
            )
            disambiguation = _calculate_disambiguation(move, conflicting_moves)
        
        # Generate base SAN
        if piece.upper() == PAWN_PIECE and is_capture:
            san = _generate_pawn_capture_san(move)
        else:
            san = _generate_standard_san(move, piece_letter, disambiguation, is_capture)
        
        # Add promotion suffix
        san = _add_promotion_suffix(san, move)
    
    # Add check/checkmate suffix
    san = _add_check_suffix(san, board, move)
    
    return san


def legal_moves_san_map(board: Board) -> Dict[str, Move]:
    """
    Generate a mapping of SAN notation variants to legal moves.
    
    Args:
        board: The current board state
        
    Returns:
        Dictionary mapping lowercase SAN strings to Move objects
    """
    moves = board.generate_legal_moves()
    mapping: Dict[str, Move] = {}
    
    for move in moves:
        san = generate_san_for_move(board, move, moves)
        
        # Add canonical form
        mapping[san.lower()] = move
        
        # Add form without check/mate suffix
        base_san = san.rstrip(f'{CHECK_SUFFIX}{CHECKMATE_SUFFIX}').lower()
        mapping[base_san] = move
        
        # Add castling notation variants
        if base_san in ("o-o", "o-o-o"):
            for variant in CASTLING_VARIANTS:
                mapping[variant.lower()] = move
        
        # Add promotion without '=' separator (e.g., 'e8q' in addition to 'e8=q')
        if PROMOTION_SEPARATOR in base_san:
            no_separator_san = base_san.replace(PROMOTION_SEPARATOR, '')
            mapping[no_separator_san] = move
    
    return mapping


def _parse_coordinate_notation(board: Board, coordinate: str) -> Optional[Move]:
    """
    Parse coordinate notation (e.g., 'e2e4' or 'g7g8q') into a Move object.
    
    Args:
        board: The current board state
        coordinate: Coordinate notation string
        
    Returns:
        The matching legal Move, or None if no match found
    """
    source_square = square_to_index(coordinate[COORD_FROM_INDEX])
    destination_square = square_to_index(coordinate[COORD_TO_INDEX])
    
    promotion_piece = None
    if len(coordinate) == 5:
        promotion_char = coordinate[COORD_PROMOTION_INDEX].upper()
        # Adjust case based on whose turn it is
        promotion_piece = promotion_char if board.white_to_move else promotion_char.lower()
    
    # Find matching legal move
    for move in board.generate_legal_moves():
        if move.from_sq != source_square or move.to_sq != destination_square:
            continue
        
        # Handle promotion moves
        if move.promotion is not None:
            if promotion_piece is None:
                # Default to queen if promotion not specified
                if move.promotion.upper() == QUEEN_PROMOTION:
                    return move
            elif promotion_piece == move.promotion:
                return move
        else:
            # Non-promotion move
            return move
    
    return None


def _parse_san_with_default_promotion(san_map: Dict[str, Move], base_san: str) -> Optional[Move]:
    """
    Attempt to parse SAN with default queen promotion if exact match not found.
    
    Args:
        san_map: Mapping of SAN strings to moves
        base_san: Base SAN string without check/mate suffix
        
    Returns:
        The matching Move if found with default promotion, None otherwise
    """
    # Try appending =q for promotions
    if base_san + PROMOTION_SEPARATOR + QUEEN_PROMOTION.lower() in san_map:
        return san_map[base_san + PROMOTION_SEPARATOR + QUEEN_PROMOTION.lower()]
    
    if base_san + QUEEN_PROMOTION.lower() in san_map:
        return san_map[base_san + QUEEN_PROMOTION.lower()]
    
    return None


def parse_user_input(board: Board, text: str) -> Optional[Move]:
    """
    Parse user input in SAN or coordinate notation into a Move object.
    
    Supports:
    - Standard Algebraic Notation (SAN): e.g., 'e4', 'Nf3', 'O-O'
    - Coordinate notation: e.g., 'e2e4', 'g7g8q'
    - Castling variants: '0-0', 'o-o', 'O-O'
    - Promotion without separator: 'e8q' in addition to 'e8=q'
    
    Args:
        board: The current board state
        text: User input string
        
    Returns:
        The parsed Move object, or None if input is invalid or ambiguous
    """
    user_input = text.strip()
    if not user_input:
        return None
    
    # Try SAN mapping
    san_map = legal_moves_san_map(board)
    normalized_input = _normalize_castle_notation(user_input).strip()
    input_key = normalized_input.lower()
    
    if input_key in san_map:
        return san_map[input_key]
    
    # Try coordinate notation
    if COORD_PATTERN.match(input_key):
        return _parse_coordinate_notation(board, input_key)
    
    # Try SAN with default queen promotion
    base_input = input_key.rstrip(f'{CHECK_SUFFIX}{CHECKMATE_SUFFIX}')
    return _parse_san_with_default_promotion(san_map, base_input)