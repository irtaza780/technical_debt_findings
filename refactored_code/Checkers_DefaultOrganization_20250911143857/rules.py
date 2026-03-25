import logging
from typing import List, Tuple, Optional
from board import Board, Piece
from constants import ROWS, COLS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
RED_PLAYER = 'red'
BLACK_PLAYER = 'black'
RED_KING_ROW = 0
BLACK_KING_ROW = ROWS - 1
MIN_MOVE_LENGTH = 2
KING_DIRECTIONS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
RED_FORWARD_DIRECTIONS = [(-1, -1), (-1, 1)]
BLACK_FORWARD_DIRECTIONS = [(1, -1), (1, 1)]
JUMP_DISTANCE = 2

Coord = Tuple[int, int]


class GameState:
    """Manages game rules, legal moves, and game state for Checkers."""

    def __init__(self, board: Board):
        """
        Initialize game state.

        Args:
            board: The game board instance.
        """
        self.board = board
        self.current_player = RED_PLAYER
        self.last_move: Optional[List[Coord]] = None

    @staticmethod
    def _opponent(color: str) -> str:
        """
        Get the opponent color.

        Args:
            color: The current player color.

        Returns:
            The opponent's color.
        """
        return BLACK_PLAYER if color == RED_PLAYER else RED_PLAYER

    def get_legal_moves(self, player: str) -> Tuple[List[List[Coord]], List[List[Coord]]]:
        """
        Get all legal moves for a player.

        Captures are mandatory in Checkers, so if any captures exist,
        only captures are returned.

        Args:
            player: The player color.

        Returns:
            Tuple of (capture_sequences, normal_moves). Each is a list of move paths.
        """
        captures = []
        normals = []

        for r in range(ROWS):
            for c in range(COLS):
                piece = self.board.get(r, c)
                if piece and piece.color == player:
                    cap = self._capture_sequences_from((r, c), piece)
                    if cap:
                        captures.extend(cap)
                    else:
                        normals.extend(self._normal_moves_from((r, c), piece))

        # Captures are mandatory
        if captures:
            return captures, []
        return [], normals

    def _get_move_directions(self, piece: Piece) -> List[Tuple[int, int]]:
        """
        Get valid movement directions for a piece.

        Args:
            piece: The piece to get directions for.

        Returns:
            List of (row_delta, col_delta) tuples.
        """
        if piece.king:
            return KING_DIRECTIONS

        if piece.color == RED_PLAYER:
            return RED_FORWARD_DIRECTIONS
        return BLACK_FORWARD_DIRECTIONS

    def _normal_moves_from(self, pos: Coord, piece: Piece) -> List[List[Coord]]:
        """
        Generate all legal normal (non-capture) moves from a position.

        Args:
            pos: The starting position (row, col).
            piece: The piece at the position.

        Returns:
            List of move sequences, each containing [start, destination].
        """
        r, c = pos
        moves = []
        directions = self._get_move_directions(piece)

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if Board.in_bounds(nr, nc) and self.board.get(nr, nc) is None:
                moves.append([pos, (nr, nc)])

        return moves

    def _capture_sequences_from(self, pos: Coord, piece: Piece) -> List[List[Coord]]:
        """
        Generate all maximal capture sequences (forced jump chains) from a position.

        A maximal sequence includes all possible jumps in a chain. Men capture
        forward only; kings capture in all directions.

        Args:
            pos: The starting position (row, col).
            piece: The piece at the position.

        Returns:
            List of capture sequences, each containing [start, ..., end].
        """
        sequences = []

        def recurse(
            board: Board,
            current: Coord,
            piece: Piece,
            path: List[Coord],
            any_jump: bool,
        ) -> None:
            """
            Recursively find all capture sequences from current position.

            Args:
                board: Current board state.
                current: Current position.
                piece: Current piece.
                path: Path taken so far.
                any_jump: Whether at least one jump has been made.
            """
            r, c = current
            color = piece.color
            directions = self._get_move_directions(piece)
            found_jump = False

            for dr, dc in directions:
                mid_r, mid_c = r + dr, c + dc
                land_r, land_c = r + JUMP_DISTANCE * dr, c + JUMP_DISTANCE * dc

                # Check bounds
                if not Board.in_bounds(land_r, land_c) or not Board.in_bounds(mid_r, mid_c):
                    continue

                mid_piece = board.get(mid_r, mid_c)
                landing_empty = board.get(land_r, land_c) is None

                # Check if valid capture: opponent piece in middle, empty landing
                if mid_piece and mid_piece.color == self._opponent(color) and landing_empty:
                    # Simulate the jump
                    next_board = board.copy()
                    next_board.remove_piece(r, c)
                    next_board.remove_piece(mid_r, mid_c)
                    next_board.set(land_r, land_c, Piece(color, king=piece.king))
                    next_piece = next_board.get(land_r, land_c)

                    # Check if piece becomes king after this jump
                    becomes_king = self._should_king_piece(color, land_r, piece.king)
                    if becomes_king:
                        next_piece.king = True

                    found_jump = True

                    # If piece becomes king, capture sequence ends
                    if becomes_king:
                        sequences.append(path + [(land_r, land_c)])
                    else:
                        recurse(next_board, (land_r, land_c), next_piece, path + [(land_r, land_c)], True)

            # If no more jumps found but we've made at least one, save the sequence
            if not found_jump and any_jump:
                sequences.append(path)

        recurse(self.board, pos, piece, [pos], False)

        # Filter to keep only sequences with at least one jump (length >= 2)
        return [seq for seq in sequences if len(seq) >= MIN_MOVE_LENGTH]

    def _should_king_piece(self, color: str, row: int, is_king: bool) -> bool:
        """
        Determine if a piece should be kinged at the given row.

        Args:
            color: The piece color.
            row: The current row.
            is_king: Whether the piece is already a king.

        Returns:
            True if the piece should be kinged.
        """
        if is_king:
            return False

        if color == RED_PLAYER and row == RED_KING_ROW:
            return True
        if color == BLACK_PLAYER and row == BLACK_KING_ROW:
            return True

        return False

    def try_move(self, seq: List[Coord]) -> Tuple[bool, Optional[str]]:
        """
        Attempt to execute a move.

        Args:
            seq: The move sequence as a list of coordinates.

        Returns:
            Tuple of (success: bool, error_message: Optional[str]).
        """
        # Validate move sequence format
        if not seq or len(seq) < MIN_MOVE_LENGTH:
            return False, "Move must specify at least a source and a destination."

        sr, sc = seq[0]
        piece = self.board.get(sr, sc)

        # Validate piece exists and belongs to current player
        if piece is None:
            return False, "No piece at the source square."
        if piece.color != self.current_player:
            return False, f"It is {self.current_player.capitalize()}'s turn."

        captures, normals = self.get_legal_moves(self.current_player)

        if captures:
            # Captures are mandatory
            if not self._is_valid_move_sequence(seq, captures):
                return False, "Invalid capture sequence or not maximal. Include full jump chain."
            self._apply_capture_sequence(seq)
            self.last_move = seq
            self._post_move_kinging(seq[-1])
            self._end_turn()
            return True, None

        # No captures available, check normal moves
        if len(seq) != MIN_MOVE_LENGTH:
            return False, "Only a single step move is allowed (no captures available)."
        if not self._is_valid_move_sequence(seq, normals):
            return False, "Invalid move."

        self._apply_normal_move(seq)
        self.last_move = seq
        self._post_move_kinging(seq[-1])
        self._end_turn()
        return True, None

    @staticmethod
    def _is_valid_move_sequence(seq: List[Coord], legal_sequences: List[List[Coord]]) -> bool:
        """
        Check if a move sequence matches one of the legal sequences.

        Args:
            seq: The move sequence to validate.
            legal_sequences: List of legal move sequences.

        Returns:
            True if the sequence is legal.
        """
        return any(GameState._same_path(seq, legal) for legal in legal_sequences)

    @staticmethod
    def _same_path(path_a: List[Coord], path_b: List[Coord]) -> bool:
        """
        Check if two paths are identical.

        Args:
            path_a: First path.
            path_b: Second path.

        Returns:
            True if paths are identical.
        """
        if len(path_a) != len(path_b):
            return False
        return all(coord_a == coord_b for coord_a, coord_b in zip(path_a, path_b))

    def _apply_capture_sequence(self, seq: List[Coord]) -> None:
        """
        Apply a capture sequence, removing jumped pieces.

        Args:
            seq: The capture sequence to apply.
        """
        for i in range(len(seq) - 1):
            from_pos = seq[i]
            to_pos = seq[i + 1]

            self.board.move_piece(from_pos, to_pos)

            # Remove the jumped piece (midpoint between from and to)
            r1, c1 = from_pos
            r2, c2 = to_pos
            mid_r = (r1 + r2) // 2
            mid_c = (c1 + c2) // 2
            self.board.remove_piece(mid_r, mid_c)

    def _apply_normal_move(self, seq: List[Coord]) -> None:
        """
        Apply a normal (non-capture) move.

        Args:
            seq: The move sequence [start, destination].
        """
        self.board.move_piece(seq[0], seq[1])

    def _post_move_kinging(self, dest: Coord) -> None:
        """
        King a piece if it reaches the back row after a move.

        Args:
            dest: The destination coordinate.
        """
        r, c = dest
        piece = self.board.get(r, c)

        if piece and not piece.king:
            if piece.color == RED_PLAYER and r == RED_KING_ROW:
                piece.king = True
            elif piece.color == BLACK_PLAYER and r == BLACK_KING_ROW:
                piece.king = True

    def _end_turn(self) -> None:
        """Switch to the opponent's turn."""
        self.current_player = self._opponent(self.current_player)

    def is_game_over(self) -> Tuple[bool, Optional[str], str]:
        """
        Check if the game is over.

        Returns:
            Tuple of (is_over: bool, winner: Optional[str], reason: str).
        """
        red_count = self._count_pieces(RED_PLAYER)
        black_count = self._count_pieces(BLACK_PLAYER)

        # Check for eliminated players
        if red_count == 0 and black_count == 0:
            return True, None, "No pieces remain."
        if red_count == 0:
            return True, BLACK_PLAYER, "Red has no pieces."
        if black_count == 0:
            return True, RED_PLAYER, "Black has no pieces."

        # Check if current player has legal moves
        captures, normals = self.get_legal_moves(self.current_player)
        if not captures and not normals:
            winner = self._opponent(self.current_player)
            return True, winner, f"{self.current_player.capitalize()} has no legal moves."

        return False, None, ""

    def _count_pieces(self, color: str) -> int:
        """
        Count the number of pieces of a given color.

        Args:
            color: The piece color to count.

        Returns:
            The number of pieces.
        """
        count = 0
        for r in range(ROWS):
            for c in range(COLS):
                piece = self.board.get(r, c)
                if piece and piece.color == color:
                    count += 1
        return count