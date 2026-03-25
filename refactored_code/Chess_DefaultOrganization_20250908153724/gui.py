import tkinter as tk
from tkinter import messagebox
import logging
from typing import Optional, List
from engine.board import Board
from engine.utils import piece_unicode
from engine.move import Move

# Constants
BOARD_SIZE = 8
BUTTON_FONT = ("Arial", 20)
BUTTON_WIDTH = 3
BUTTON_HEIGHT = 1
LIGHT_SQUARE_COLOR = "#EEE"
DARK_SQUARE_COLOR = "#8AA"
SELECTED_COLOR = "#CC6"
LEGAL_TARGET_COLOR = "#6C6"
PROMOTION_PIECES = ['Q', 'R', 'B', 'N']
DEFAULT_PROMOTION = 'Q'
PADDING_LARGE = 10
PADDING_SMALL = 5

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromotionDialog(tk.Toplevel):
    """Dialog window for pawn promotion piece selection."""

    def __init__(self, master, white_to_move: bool):
        """
        Initialize promotion dialog.

        Args:
            master: Parent window
            white_to_move: True if white player is promoting, False if black
        """
        super().__init__(master)
        self.title("Promote pawn")
        self.resizable(False, False)
        self.result: Optional[str] = None
        self.white_to_move = white_to_move
        self._build_dialog()

    def _build_dialog(self) -> None:
        """Build the promotion dialog UI with piece selection buttons."""
        tk.Label(self, text="Choose promotion:").pack(padx=PADDING_LARGE, pady=PADDING_LARGE)
        frame = tk.Frame(self)
        frame.pack(padx=PADDING_LARGE, pady=PADDING_LARGE)

        for piece in PROMOTION_PIECES:
            button = tk.Button(
                frame,
                text=piece,
                width=4,
                command=lambda p=piece: self._choose_piece(p)
            )
            button.pack(side=tk.LEFT, padx=PADDING_SMALL)

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _choose_piece(self, piece: str) -> None:
        """
        Handle piece selection.

        Args:
            piece: Selected piece character (uppercase)
        """
        self.result = piece if self.white_to_move else piece.lower()
        self.destroy()

    def _on_close(self) -> None:
        """Handle dialog close by defaulting to queen."""
        self.result = DEFAULT_PROMOTION if self.white_to_move else DEFAULT_PROMOTION.lower()
        self.destroy()


class ChessGUI(tk.Tk):
    """Main chess GUI application using Tkinter."""

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
        """Build the user interface with board and status bar."""
        self._build_board()
        self._build_status_bar()

    def _build_board(self) -> None:
        """Build the chess board grid of buttons."""
        board_frame = tk.Frame(self)
        board_frame.pack(padx=PADDING_LARGE, pady=PADDING_LARGE)

        for row in range(BOARD_SIZE):
            row_buttons = []
            for col in range(BOARD_SIZE):
                button = tk.Button(
                    board_frame,
                    text="",
                    font=BUTTON_FONT,
                    width=BUTTON_WIDTH,
                    height=BUTTON_HEIGHT,
                    command=lambda r=row, c=col: self.on_click(r, c)
                )
                button.grid(row=row, column=col, sticky="nsew")
                row_buttons.append(button)
            self.buttons.append(row_buttons)

        # Configure grid to expand evenly
        for i in range(BOARD_SIZE):
            board_frame.grid_rowconfigure(i, weight=1)
            board_frame.grid_columnconfigure(i, weight=1)

    def _build_status_bar(self) -> None:
        """Build the status bar with game status and restart button."""
        status_frame = tk.Frame(self)
        status_frame.pack(fill=tk.X, padx=PADDING_LARGE, pady=PADDING_SMALL)
        tk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        tk.Button(status_frame, text="Restart", command=self.on_restart).pack(side=tk.RIGHT)

    def _refresh(self) -> None:
        """Refresh the board display and update game status."""
        self._update_board_display()
        self._update_game_status()

    def _update_board_display(self) -> None:
        """Update all board button visuals based on current board state."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                square_index = row * BOARD_SIZE + col
                piece = self.board.squares[square_index]
                button = self.buttons[row][col]

                # Update piece display
                piece_text = piece_unicode(piece) if piece else ''
                button.config(text=piece_text)

                # Update square color based on state
                color = self._get_square_color(square_index, row, col)
                button.config(bg=color, activebackground=color)

    def _get_square_color(self, square_index: int, row: int, col: int) -> str:
        """
        Determine the color for a square based on its state.

        Args:
            square_index: Index of the square (0-63)
            row: Row number (0-7)
            col: Column number (0-7)

        Returns:
            Hex color string for the square
        """
        if square_index == self.selected:
            return SELECTED_COLOR
        elif square_index in self.legal_targets:
            return LEGAL_TARGET_COLOR
        else:
            # Alternate light and dark squares
            return LIGHT_SQUARE_COLOR if (row + col) % 2 == 0 else DARK_SQUARE_COLOR

    def _update_game_status(self) -> None:
        """Update the status bar text based on current game state."""
        if self.board.is_checkmate():
            winner = "Black" if self.board.white_to_move else "White"
            status_text = f"Checkmate! {winner} wins."
            self.status_var.set(status_text)
            messagebox.showinfo("Game Over", status_text)
        elif self.board.is_stalemate():
            status_text = "Stalemate. Draw."
            self.status_var.set(status_text)
            messagebox.showinfo("Game Over", status_text)
        else:
            self._update_status_for_active_game()

    def _update_status_for_active_game(self) -> None:
        """Update status text for an ongoing game."""
        turn = "White" if self.board.white_to_move else "Black"
        check_status = " - Check" if self.board.in_check(self.board.white_to_move) else ""
        self.status_var.set(f"{turn} to move{check_status}")

    def on_restart(self) -> None:
        """Reset the board to the starting position."""
        self.board.setup_start_position()
        self.selected = None
        self.legal_targets = []
        self._refresh()
        logger.info("Game restarted")

    def on_click(self, row: int, col: int) -> None:
        """
        Handle square click events.

        Args:
            row: Row number (0-7)
            col: Column number (0-7)
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
            square_index: Index of the selected square
        """
        piece = self.board.squares[square_index]

        # Validate piece belongs to current player
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
            target_index: Index of the target square
        """
        source_index = self.selected

        if target_index == source_index:
            self._deselect()
            return

        # Get legal moves from source to target
        legal_moves = [
            move for move in self.board.get_legal_moves_for_square(source_index)
            if move.to_sq == target_index
        ]

        if not legal_moves:
            self._handle_invalid_target(target_index)
            return

        # Execute the move
        chosen_move = self._resolve_promotion(legal_moves)
        if chosen_move:
            self.board.make_move(chosen_move)
            logger.info(f"Move executed: {chosen_move}")
            self._deselect()
            self._refresh()

    def _handle_invalid_target(self, target_index: int) -> None:
        """
        Handle click on invalid target square.

        Args:
            target_index: Index of the clicked square
        """
        piece = self.board.squares[target_index]

        # If target has a piece belonging to current player, select it instead
        if piece is not None and self._is_player_piece(piece):
            self.selected = target_index
            legal_moves = self.board.get_legal_moves_for_square(target_index)
            self.legal_targets = [move.to_sq for move in legal_moves]
            self._refresh()
        else:
            self._deselect()

    def _is_player_piece(self, piece: Optional[str]) -> bool:
        """
        Check if a piece belongs to the current player.

        Args:
            piece: Piece character or None

        Returns:
            True if piece belongs to current player, False otherwise
        """
        if piece is None:
            return False

        if self.board.white_to_move:
            return piece.isupper()
        else:
            return piece.islower()

    def _resolve_promotion(self, legal_moves: List[Move]) -> Optional[Move]:
        """
        Resolve pawn promotion if applicable.

        Args:
            legal_moves: List of legal moves to the target square

        Returns:
            The move to execute, or None if no valid move found
        """
        # Check if any move involves promotion
        promotion_moves = [move for move in legal_moves if move.promotion is not None]

        if not promotion_moves:
            return legal_moves[0]

        # Show promotion dialog
        dialog = PromotionDialog(self, self.board.white_to_move)
        self.wait_window(dialog)
        selected_promotion = dialog.result or (
            DEFAULT_PROMOTION if self.board.white_to_move else DEFAULT_PROMOTION.lower()
        )

        # Find move with selected promotion
        for move in promotion_moves:
            if move.promotion == selected_promotion:
                return move

        # Fallback to queen promotion
        for move in promotion_moves:
            if move.promotion and move.promotion.upper() == DEFAULT_PROMOTION:
                return move

        return None

    def _deselect(self) -> None:
        """Clear piece selection and legal targets."""
        self.selected = None
        self.legal_targets = []
        self._refresh()


def run_gui() -> None:
    """Launch the chess GUI application."""
    app = ChessGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui()