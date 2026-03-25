import logging
import tkinter as tk
from typing import Optional

from game import ConnectFourGame

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Visual layout constants
CELL_SIZE = 80
MARGIN = 20
BOARD_BG = "#1E5AB6"
EMPTY_COLOR = "#F2F3F5"
BOARD_OUTLINE = "#0D3B8E"
CELL_PADDING_RATIO = 0.1
COLUMN_NUMBERS_Y_OFFSET = 10
CANVAS_EXTRA_HEIGHT = 30
CANVAS_Y_OFFSET = 20

# Player colors
PLAYER_COLORS = {
    1: "#E74C3C",  # Red
    2: "#F1C40F",  # Yellow
}

# Player color names
PLAYER_COLOR_NAMES = {
    1: "Red",
    2: "Yellow",
}

# UI dimensions
ENTRY_WIDTH = 5
BUTTON_WIDTH = 8
LABEL_FONT = ("Segoe UI", 10)
STATUS_FONT = ("Segoe UI", 11)
COLUMN_HEADER_FONT = ("Segoe UI", 10, "bold")

# UI padding
PADX_MAIN = 10
PADY_STATUS = (10, 5)
PADY_CANVAS = 5
PADY_CONTROLS = (5, 10)
PADX_CONTROLS_INNER = (5, 5)
PADX_CONTROLS_BETWEEN = (5, 15)

# Board boundaries
BOARD_OUTLINE_WIDTH = 2

# Entry states
ENTRY_STATE_NORMAL = "normal"
ENTRY_STATE_DISABLED = "disabled"


class ConnectFourGUI:
    """Graphical user interface for the Connect Four game."""

    def __init__(self, root: tk.Tk, game: ConnectFourGame) -> None:
        """
        Initialize the Connect Four GUI.

        Args:
            root: The root Tkinter window.
            game: The ConnectFourGame instance to manage game logic.
        """
        self.root = root
        self.game = game
        self.status_var = tk.StringVar()

        # Calculate canvas dimensions based on board size
        self.canvas_width = MARGIN * 2 + game.cols * CELL_SIZE
        self.canvas_height = MARGIN * 2 + game.rows * CELL_SIZE

        self._build_widgets()
        self.draw_board()
        self.update_status()

    def _build_widgets(self) -> None:
        """Create and lay out all GUI widgets."""
        self._build_status_frame()
        self._build_canvas()
        self._build_controls_frame()

    def _build_status_frame(self) -> None:
        """Build the status display frame."""
        status_frame = tk.Frame(self.root)
        status_frame.pack(padx=PADX_MAIN, pady=PADY_STATUS, fill=tk.X)

        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            anchor="w",
            font=STATUS_FONT,
        )
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _build_canvas(self) -> None:
        """Build the game board canvas."""
        self.canvas = tk.Canvas(
            self.root,
            width=self.canvas_width,
            height=self.canvas_height + CANVAS_EXTRA_HEIGHT,
            bg="#ffffff",
            highlightthickness=0,
        )
        self.canvas.pack(padx=PADX_MAIN, pady=PADY_CANVAS)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def _build_controls_frame(self) -> None:
        """Build the input controls frame."""
        controls = tk.Frame(self.root)
        controls.pack(padx=PADX_MAIN, pady=PADY_CONTROLS, fill=tk.X)

        tk.Label(
            controls,
            text=f"Column (1-{self.game.cols}):",
            font=LABEL_FONT,
        ).pack(side=tk.LEFT)

        self.column_var = tk.StringVar()
        self.column_entry = tk.Entry(controls, width=ENTRY_WIDTH, textvariable=self.column_var)
        self.column_entry.pack(side=tk.LEFT, padx=PADX_CONTROLS_INNER)
        self.column_entry.bind("<Return>", self.on_submit)

        self.submit_button = tk.Button(
            controls,
            text="Drop",
            command=self.on_submit,
            width=BUTTON_WIDTH,
        )
        self.submit_button.pack(side=tk.LEFT, padx=PADX_CONTROLS_BETWEEN)

        self.reset_button = tk.Button(
            controls,
            text="Reset",
            command=self.reset_game,
            width=BUTTON_WIDTH,
        )
        self.reset_button.pack(side=tk.LEFT)

    def focus_column_entry(self) -> None:
        """Give focus to the column entry for immediate typing."""
        self.column_entry.focus_set()
        self.column_entry.selection_range(0, tk.END)

    def update_status(self, message: Optional[str] = None) -> None:
        """
        Update the status bar with current turn or custom message.

        Args:
            message: Optional custom message to display. If None, displays game state.
        """
        if message:
            self.status_var.set(message)
            return

        if self.game.game_over:
            self._update_status_game_over()
        else:
            self._update_status_active_game()

    def _update_status_game_over(self) -> None:
        """Update status message when game is over."""
        winner = self.game.get_winner()
        if winner:
            color = PLAYER_COLOR_NAMES.get(winner, "Unknown")
            self.status_var.set(
                f"Player {winner} ({color}) wins! Press Reset to play again."
            )
        else:
            self.status_var.set("It's a draw! Press Reset to play again.")

    def _update_status_active_game(self) -> None:
        """Update status message during active gameplay."""
        player = self.game.get_current_player()
        color = PLAYER_COLOR_NAMES.get(player, "Unknown")
        self.status_var.set(
            f"Player {player} ({color}) to move. Enter a column number (1-{self.game.cols})."
        )

    def draw_board(self) -> None:
        """Render the Connect Four board and discs."""
        self.canvas.delete("all")
        self._draw_column_numbers()
        self._draw_board_background()
        self._draw_cells()

    def _draw_column_numbers(self) -> None:
        """Draw column number labels above the board."""
        for col in range(self.game.cols):
            x_center = MARGIN + col * CELL_SIZE + CELL_SIZE / 2
            self.canvas.create_text(
                x_center,
                COLUMN_NUMBERS_Y_OFFSET,
                text=str(col + 1),
                font=COLUMN_HEADER_FONT,
                fill="#333333",
            )

    def _draw_board_background(self) -> None:
        """Draw the board background rectangle."""
        self.canvas.create_rectangle(
            MARGIN,
            MARGIN + CANVAS_Y_OFFSET,
            self.canvas_width - MARGIN,
            self.canvas_height + CANVAS_Y_OFFSET - MARGIN,
            fill=BOARD_BG,
            width=0,
        )

    def _draw_cells(self) -> None:
        """Draw all cells (holes) and discs on the board."""
        padding = CELL_SIZE * CELL_PADDING_RATIO

        for row in range(self.game.rows):
            for col in range(self.game.cols):
                self._draw_cell(row, col, padding)

    def _draw_cell(self, row: int, col: int, padding: float) -> None:
        """
        Draw a single cell (hole) and disc.

        Args:
            row: Row index (0-based).
            col: Column index (0-based).
            padding: Padding around the cell.
        """
        x0 = MARGIN + col * CELL_SIZE + padding
        y0 = MARGIN + CANVAS_Y_OFFSET + row * CELL_SIZE + padding
        x1 = MARGIN + (col + 1) * CELL_SIZE - padding
        y1 = MARGIN + CANVAS_Y_OFFSET + (row + 1) * CELL_SIZE - padding

        cell_value = self.game.board[row][col]
        color = EMPTY_COLOR if cell_value == 0 else PLAYER_COLORS.get(cell_value, "#000000")

        self.canvas.create_oval(
            x0,
            y0,
            x1,
            y1,
            fill=color,
            outline=BOARD_OUTLINE,
            width=BOARD_OUTLINE_WIDTH,
        )

    def on_submit(self, event: Optional[tk.Event] = None) -> Optional[str]:
        """
        Handle 'Drop' button or Enter key to submit the typed column.

        Args:
            event: Optional event object from key binding.

        Returns:
            "break" if triggered by an event to stop further propagation, else None.
        """
        # Early guard: preserve final status and avoid handling after game end
        if self.game.game_over:
            self.update_status()
            return "break" if event is not None else None

        text = self.column_var.get().strip()

        if not text:
            self.update_status(f"Please type a column number (1-{self.game.cols}).")
        else:
            try:
                col_input = int(text)
            except ValueError:
                self.update_status(
                    f"Invalid input. Enter a number from 1 to {self.game.cols}."
                )
            else:
                self.attempt_move(col_input - 1)

        # Ensure single handling for Entry's Return
        if event is not None:
            return "break"

        return None

    def attempt_move(self, col: int) -> None:
        """
        Attempt to make a move in the specified column.

        Args:
            col: Column index (0-based).
        """
        if self.game.game_over:
            self.update_status("The game is over. Press Reset to play again.")
            return

        # Validate column range
        if not self._is_valid_column(col):
            self.update_status(f"Column must be between 1 and {self.game.cols}.")
            self.column_entry.selection_range(0, tk.END)
            return

        # Attempt to drop disc
        try:
            self.game.drop_disc(col)
        except ValueError as e:
            self._handle_move_error(str(e))
        else:
            self._handle_successful_move()
        finally:
            self._clear_and_refocus_entry()

    def _is_valid_column(self, col: int) -> bool:
        """
        Check if column index is within valid range.

        Args:
            col: Column index (0-based).

        Returns:
            True if column is valid, False otherwise.
        """
        return 0 <= col < self.game.cols

    def _handle_move_error(self, error_message: str) -> None:
        """
        Handle errors from move attempts.

        Args:
            error_message: The error message from the game.
        """
        if "full" in error_message.lower():
            self.update_status("That column is full. Try a different one.")
        elif "over" in error_message.lower():
            self.update_status("The game is over. Press Reset to play again.")
        else:
            self.update_status(error_message)

    def _handle_successful_move(self) -> None:
        """Handle successful move: update board and check game state."""
        self.draw_board()

        if self.game.game_over:
            self.end_game_feedback()
        else:
            self.update_status()

    def _clear_and_refocus_entry(self) -> None:
        """Clear the entry field and refocus if enabled."""
        self.column_var.set("")

        if self._is_entry_enabled():
            self.focus_column_entry()

    def _is_entry_enabled(self) -> bool:
        """
        Check if the column entry is enabled.

        Returns:
            True if entry is in normal state, False otherwise.
        """
        return str(self.column_entry["state"]) == ENTRY_STATE_NORMAL

    def on_canvas_click(self, event: tk.Event) -> None:
        """
        Handle canvas click to drop a disc in the clicked column.

        Args:
            event: The click event containing coordinates.
        """
        if self.game.game_over:
            return

        col = self._get_column_from_click(event.x, event.y)

        if col is not None:
            self.attempt_move(col)

    def _get_column_from_click(self, x: int, y: int) -> Optional[int]:
        """
        Determine column index from canvas click coordinates.

        Args:
            x: X coordinate of click.
            y: Y coordinate of click.

        Returns:
            Column index (0-based) if click is within board, None otherwise.
        """
        # Check horizontal bounds
        left = MARGIN
        right = self.canvas_width - MARGIN

        if not (left <= x <= right):
            return None

        # Check vertical bounds
        top = MARGIN + CANVAS_Y_OFFSET
        bottom = self.canvas_height + CANVAS_Y_OFFSET - MARGIN

        if not (top <= y <= bottom):
            return None

        # Calculate column from x coordinate
        col = int((x - MARGIN) // CELL_SIZE)
        return col

    def end_game_feedback(self) -> None:
        """Disable inputs and show final status."""
        self.update_status()
        self.column_entry.configure(state=ENTRY_STATE_DISABLED)
        self.submit_button.configure(state=ENTRY_STATE_DISABLED)

    def reset_game(self) -> None:
        """Reset the game logic and UI to initial state."""
        self.game.reset()
        self.column_var.set("")
        self.column_entry.configure(state=ENTRY_STATE_NORMAL)
        self.submit_button.configure(state=ENTRY_STATE_NORMAL)
        self.draw_board()
        self.update_status()
        self.focus_column_entry()