import tkinter as tk
from tkinter import messagebox
import logging
from typing import Optional, List
from engine.board import Board
from engine.utils import piece_unicode
from engine.move import Move

# Constants
BOARD_SIZE = 8
SQUARE_SIZE = 3
FONT_SIZE = 20
LIGHT_SQUARE_COLOR = "#EEE"
DARK_SQUARE_COLOR = "#8AA"
SELECTED_SQUARE_COLOR = "#CC6"
LEGAL_TARGET_COLOR = "#6C6"
PROMOTION_PIECES = ['Q', 'R', 'B', 'N']
DEFAULT_PROMOTION = 'Q'
PADDING_LARGE = 10
PADDING_SMALL = 5

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromotionDialog(tk.Toplevel):
    """Dialog window for selecting pawn promotion piece."""

    def __init__(self, master, white_to_move: bool):
        """
        Initialize promotion dialog.

        Args:
            master: Parent window
            white_to_move: True if white player is promoting
        """
        super().__init__(master)
        self.title("Promote pawn")
        self.resizable(False, False)
        self.result: Optional[str] = None
        self.white_to_move = white_to_move
        self._build_dialog()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_dialog(self) -> None:
        """Build the promotion dialog UI."""
        tk.Label(self, text="Choose promotion:").pack(padx=PADDING_LARGE, pady=PADDING_LARGE)
        frame = tk.Frame(self)
        frame.pack(padx=PADDING_LARGE, pady=PADDING_LARGE)
        for piece in PROMOTION_PIECES:
            btn = tk.Button(
                frame,
                text=piece,
                width=4,
                command=lambda p=piece: self._choose_piece(p)
            )
            btn.pack(side=tk.LEFT, padx=PADDING_SMALL)

    def _choose_piece(self, piece: str) -> None:
        """
        Handle piece selection.

        Args:
            piece: Selected piece character
        """
        self.result = piece if self.white_to_move else piece.lower()
        self.destroy()

    def _on_close(self) -> None:
        """Handle dialog close button."""
        self.result = DEFAULT_PROMOTION if self.white_to_move else DEFAULT_PROMOTION.lower()
        self.destroy()


class ChessGUI(tk.Tk):
    """Main chess GUI application."""

    def __init__(self):
        """Initialize the chess GUI."""
        super().__init__()
        self.title("ChatDev Chess")
        self.board = Board()
        self.board.setup_start_position()
        self.buttons: List[List[tk.Button]] = []
        self.selected: Optional[int] = None
        self.legal_targets: List[int] = []
        self.status_var = tk.StringVar()
        self.status_var.set("White to move")
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        """Build the user interface."""
        self._build_board_frame()
        self._build_status_frame()

    def _build_board_frame(self) -> None:
        """Build the chess board frame with buttons."""
        board_frame = tk.Frame(self)
        board_frame.pack(padx=PADDING_LARGE, pady=PADDING_LARGE)

        for row in range(BOARD_SIZE):
            row_buttons = []
            for col in range(BOARD_SIZE):
                btn = tk.Button(
                    board_frame,
                    text="",
                    font=("Arial", FONT_SIZE),
                    width=SQUARE_SIZE,
                    height=1,
                    command=lambda r=row, c=col: self.on_click(r, c)
                )
                btn.grid(row=row, column=col, sticky="nsew")
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

        # Configure grid to expand evenly
        for i in range(BOARD_SIZE):
            board_frame.grid_rowconfigure(i, weight=1)
            board_frame.grid_columnconfigure(i, weight=1)

    def _build_status_frame(self) -> None:
        """Build the status and control frame."""
        status_frame = tk.Frame(self)
        status_frame.pack(fill=tk.X, padx=PADDING_LARGE, pady=PADDING_SMALL)
        tk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        tk.Button(status_frame, text="Restart", command=self.on_restart).pack(side=tk.RIGHT)

    def _refresh(self) -> None:
        """Refresh the board display and game status."""
        self._update_board_display()
        self._update_game_status()

    def _update_board_display(self) -> None:
        """Update all board square displays."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                square_index = row * BOARD_SIZE + col
                piece = self.board.squares[square_index]
                text = piece_unicode(piece) if piece else ''
                btn = self.buttons[row][col]
                btn.config(text=text)
                color = self._get_square_color(row, col, square_index)
                btn.config(bg=color, activebackground=color)

    def _get_square_color(self, row: int, col: int, square_index: int) -> str:
        """
        Determine the color for a square.

        Args:
            row: Board row
            col: Board column
            square_index: Linear square index

        Returns:
            Color hex code
        """
        if square_index == self.selected:
            return SELECTED_SQUARE_COLOR
        if square_index in self.legal_targets:
            return LEGAL_TARGET_COLOR
        # Checkerboard pattern
        return LIGHT_SQUARE_COLOR if (row + col) % 2 == 0 else DARK_SQUARE_COLOR

    def _update_game_status(self) -> None:
        """Update the game status message."""
        if self.board.is_checkmate():
            self._handle_checkmate()
        elif self.board.is_stalemate():
            self._handle_stalemate()
        else:
            self._handle_normal_status()

    def _handle_checkmate(self) -> None:
        """Handle checkmate condition."""
        winner = "Black" if self.board.white_to_move else "White"
        message = f"Checkmate! {winner} wins."
        self.status_var.set(message)
        messagebox.showinfo("Game Over", message)

    def _handle_stalemate(self) -> None:
        """Handle stalemate condition."""
        message = "Stalemate. Draw."
        self.status_var.set(message)
        messagebox.showinfo("Game Over", message)

    def _handle_normal_status(self) -> None:
        """Update status for normal game state."""
        turn = "White" if self.board.white_to_move else "Black"
        in_check = self.board.in_check(self.board.white_to_move)
        check_suffix = " - Check" if in_check else ""
        self.status_var.set(f"{turn} to move{check_suffix}")

    def on_restart(self) -> None:
        """Restart the game."""
        self.board.setup_start_position()
        self.selected = None
        self.legal_targets = []
        self._refresh()

    def on_click(self, row: int, col: int) -> None:
        """
        Handle square click.

        Args:
            row: Clicked row
            col: Clicked column
        """
        square_index = row * BOARD_SIZE + col

        if self.selected is None:
            self._handle_piece_selection(square_index)
        else:
            self._handle_move_attempt(square_index)

    def _handle_piece_selection(self, square_index: int) -> None:
        """
        Handle selection of a piece to move.

        Args:
            square_index: Index of selected square
        """
        piece = self.board.squares[square_index]
        if piece is None:
            return

        if not self._is_player_piece(piece):
            return

        self.selected = square_index
        legal_moves = self.board.get_legal_moves_for_square(square_index)
        self.legal_targets = [move.to_sq for move in legal_moves]
        self._refresh()

    def _handle_move_attempt(self, target_index: int) -> None:
        """
        Handle attempt to move selected piece to target square.

        Args:
            target_index: Index of target square
        """
        source_index = self.selected

        if target_index == source_index:
            self._deselect()
            return

        legal_moves = [
            move for move in self.board.get_legal_moves_for_square(source_index)
            if move.to_sq == target_index
        ]

        if not legal_moves:
            self._handle_invalid_target(target_index)
            return

        chosen_move = self._get_promotion_move(legal_moves) if self._has_promotion(legal_moves) else legal_moves[0]
        self.board.make_move(chosen_move)
        self._deselect()
        self._refresh()

    def _handle_invalid_target(self, target_index: int) -> None:
        """
        Handle click on invalid target square.

        Args:
            target_index: Index of target square
        """
        piece = self.board.squares[target_index]
        if piece is not None and self._is_player_piece(piece):
            # Select new piece instead
            self.selected = target_index
            legal_moves = self.board.get_legal_moves_for_square(target_index)
            self.legal_targets = [move.to_sq for move in legal_moves]
        else:
            # Invalid move, deselect
            self._deselect()
        self._refresh()

    def _deselect(self) -> None:
        """Clear selection and legal targets."""
        self.selected = None
        self.legal_targets = []

    def _is_player_piece(self, piece: str) -> bool:
        """
        Check if piece belongs to current player.

        Args:
            piece: Piece character

        Returns:
            True if piece belongs to current player
        """
        if self.board.white_to_move:
            return piece.isupper()
        return piece.islower()

    def _has_promotion(self, moves: List[Move]) -> bool:
        """
        Check if any move involves promotion.

        Args:
            moves: List of moves to check

        Returns:
            True if any move has promotion
        """
        return any(move.promotion is not None for move in moves)

    def _get_promotion_move(self, moves: List[Move]) -> Move:
        """
        Get the correct promotion move based on user selection.

        Args:
            moves: List of promotion moves

        Returns:
            Selected promotion move
        """
        dialog = PromotionDialog(self, self.board.white_to_move)
        self.wait_window(dialog)
        promotion_piece = dialog.result or (DEFAULT_PROMOTION if self.board.white_to_move else DEFAULT_PROMOTION.lower())

        # Find move with matching promotion
        for move in moves:
            if move.promotion == promotion_piece:
                return move

        # Fallback to queen promotion
        for move in moves:
            if move.promotion and move.promotion.upper() == DEFAULT_PROMOTION:
                return move

        logger.warning("No valid promotion move found, returning first move")
        return moves[0]


def run_gui() -> None:
    """Run the chess GUI application."""
    app = ChessGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui()