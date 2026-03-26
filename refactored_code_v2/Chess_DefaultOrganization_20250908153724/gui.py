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
        Set selected promotion piece and close dialog.

        Args:
            piece: Uppercase piece character (Q, R, B, N)
        """
        self.result = piece if self.white_to_move else piece.lower()
        self.destroy()

    def _on_close(self) -> None:
        """Handle dialog close by defaulting to queen."""
        self.result = DEFAULT_PROMOTION if self.white_to_move else DEFAULT_PROMOTION.lower()
        self.destroy()


class ChessGUI(tk.Tk):
    """Main chess GUI application."""

    def __init__(self):
        """Initialize the chess GUI application."""
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
        """Build the user interface components."""
        self._build_board_frame()
        self._build_status_frame()

    def _build_board_frame(self) -> None:
        """Build the chess board grid of buttons."""
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
        """Build the status bar and control buttons."""
        status_frame = tk.Frame(self)
        status_frame.pack(fill=tk.X, padx=PADDING_LARGE, pady=PADDING_SMALL)
        tk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        tk.Button(status_frame, text="Restart", command=self.on_restart).pack(side=tk.RIGHT)

    def _refresh(self) -> None:
        """Update board display and game status."""
        self._update_board_display()
        self._update_game_status()

    def _update_board_display(self) -> None:
        """Update all board square colors and piece displays."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                idx = row * BOARD_SIZE + col
                piece = self.board.squares[idx]
                text = piece_unicode(piece) if piece else ''
                btn = self.buttons[row][col]
                btn.config(text=text)

                # Determine square color
                color = self._get_square_color(row, col, idx)
                btn.config(bg=color, activebackground=color)

    def _get_square_color(self, row: int, col: int, idx: int) -> str:
        """
        Determine the display color for a square.

        Args:
            row: Board row (0-7)
            col: Board column (0-7)
            idx: Square index (0-63)

        Returns:
            Hex color string for the square
        """
        if idx == self.selected:
            return SELECTED_SQUARE_COLOR
        if idx in self.legal_targets:
            return LEGAL_TARGET_COLOR
        # Checkerboard pattern
        return LIGHT_SQUARE_COLOR if (row + col) % 2 == 0 else DARK_SQUARE_COLOR

    def _update_game_status(self) -> None:
        """Update status message based on current game state."""
        if self.board.is_checkmate():
            self._handle_checkmate()
        elif self.board.is_stalemate():
            self._handle_stalemate()
        else:
            self._handle_normal_status()

    def _handle_checkmate(self) -> None:
        """Handle checkmate game end."""
        winner = "Black" if self.board.white_to_move else "White"
        message = f"Checkmate! {winner} wins."
        self.status_var.set(message)
        messagebox.showinfo("Game Over", message)

    def _handle_stalemate(self) -> None:
        """Handle stalemate game end."""
        message = "Stalemate. Draw."
        self.status_var.set(message)
        messagebox.showinfo("Game Over", message)

    def _handle_normal_status(self) -> None:
        """Update status for normal game state."""
        turn = "White" if self.board.white_to_move else "Black"
        check_status = " - Check" if self.board.in_check(self.board.white_to_move) else ""
        self.status_var.set(f"{turn} to move{check_status}")

    def on_restart(self) -> None:
        """Reset the board to starting position."""
        self.board.setup_start_position()
        self.selected = None
        self.legal_targets = []
        self._refresh()
        logger.info("Game restarted")

    def on_click(self, row: int, col: int) -> None:
        """
        Handle square click event.

        Args:
            row: Clicked row (0-7)
            col: Clicked column (0-7)
        """
        idx = row * BOARD_SIZE + col

        if self.selected is None:
            self._handle_piece_selection(idx)
        else:
            self._handle_move_attempt(idx)

    def _handle_piece_selection(self, idx: int) -> None:
        """
        Handle selection of a piece to move.

        Args:
            idx: Square index of selected piece
        """
        piece = self.board.squares[idx]
        if piece is None:
            return

        # Check if piece belongs to current player
        if not self._piece_belongs_to_current_player(piece):
            return

        self.selected = idx
        legal_moves = self.board.get_legal_moves_for_square(idx)
        self.legal_targets = [move.to_sq for move in legal_moves]
        self._refresh()

    def _handle_move_attempt(self, target_idx: int) -> None:
        """
        Handle attempt to move selected piece to target square.

        Args:
            target_idx: Target square index
        """
        source_idx = self.selected

        if target_idx == source_idx:
            self._deselect()
            return

        legal_moves = [
            move for move in self.board.get_legal_moves_for_square(source_idx)
            if move.to_sq == target_idx
        ]

        if not legal_moves:
            self._handle_invalid_target(target_idx)
            return

        # Execute the move
        chosen_move = self._resolve_promotion(legal_moves)
        self.board.make_move(chosen_move)
        self._deselect()
        self._refresh()
        logger.info(f"Move executed: {chosen_move}")

    def _handle_invalid_target(self, target_idx: int) -> None:
        """
        Handle click on invalid target square.

        Args:
            target_idx: Target square index
        """
        piece = self.board.squares[target_idx]
        if piece is not None and self._piece_belongs_to_current_player(piece):
            # Select new piece instead
            self.selected = target_idx
            legal_moves = self.board.get_legal_moves_for_square(target_idx)
            self.legal_targets = [move.to_sq for move in legal_moves]
        else:
            # Invalid move, deselect
            self._deselect()
        self._refresh()

    def _deselect(self) -> None:
        """Clear piece selection and legal targets."""
        self.selected = None
        self.legal_targets = []

    def _piece_belongs_to_current_player(self, piece: str) -> bool:
        """
        Check if piece belongs to the player whose turn it is.

        Args:
            piece: Piece character (uppercase for white, lowercase for black)

        Returns:
            True if piece belongs to current player
        """
        if self.board.white_to_move:
            return piece.isupper()
        return piece.islower()

    def _resolve_promotion(self, legal_moves: List[Move]) -> Move:
        """
        Resolve pawn promotion if applicable.

        Args:
            legal_moves: List of legal moves to target square

        Returns:
            The move to execute (with promotion piece if applicable)
        """
        # Check if any move involves promotion
        promotion_moves = [move for move in legal_moves if move.promotion is not None]

        if not promotion_moves:
            return legal_moves[0]

        # Show promotion dialog
        dialog = PromotionDialog(self, self.board.white_to_move)
        self.wait_window(dialog)
        chosen_piece = dialog.result or (DEFAULT_PROMOTION if self.board.white_to_move else DEFAULT_PROMOTION.lower())

        # Find move with chosen promotion piece
        for move in promotion_moves:
            if move.promotion == chosen_piece:
                return move

        # Fallback to queen promotion
        for move in promotion_moves:
            if move.promotion and move.promotion.upper() == DEFAULT_PROMOTION:
                return move

        return legal_moves[0]


def run_gui() -> None:
    """Launch the chess GUI application."""
    try:
        app = ChessGUI()
        app.mainloop()
    except Exception as e:
        logger.error(f"GUI error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_gui()