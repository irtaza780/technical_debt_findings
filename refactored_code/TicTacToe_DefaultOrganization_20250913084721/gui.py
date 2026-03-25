import logging
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional, Tuple

from game_logic import TicTacToeGame
from constants import GRID_SIZE, SYMBOL_X, SYMBOL_O, COLORS, FONTS, WINDOW_TITLE, APP_VERSION

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# UI Constants
BUTTON_WIDTH = 4
BUTTON_HEIGHT = 2
GRID_PADDING = 6
STATUS_PADDING = 12
CONTROL_PADDING = 8
MENU_TEAROFF = 0
BUTTON_RELIEF = 'raised'
BUTTON_BORDERWIDTH = 2
GRID_WEIGHT = 1


class TicTacToeGUI:
    """Tkinter-based GUI for the Tic-Tac-Toe game."""

    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize the Tic-Tac-Toe GUI.

        Args:
            root: The root Tkinter window.
        """
        self.root = root
        self.game = TicTacToeGame()
        self.buttons: List[List[tk.Button]] = []
        self.status_label: Optional[tk.Label] = None
        self.grid_frame: Optional[tk.Frame] = None
        self.control_frame: Optional[tk.Frame] = None
        logger.info("TicTacToeGUI initialized")

    def build_ui(self) -> None:
        """Create all UI components and layout."""
        logger.info("Building UI")
        self._build_menu()
        self._build_status_area()
        self._build_grid_area()
        self._build_control_area()
        self._bind_keyboard_shortcuts()
        self.update_status()
        logger.info("UI build complete")

    def _build_menu(self) -> None:
        """Create the application menu bar."""
        menu_bar = tk.Menu(self.root)

        game_menu = tk.Menu(menu_bar, tearoff=MENU_TEAROFF)
        game_menu.add_command(label="New Game", command=self.reset_game, accelerator="Ctrl+N")
        game_menu.add_separator()
        game_menu.add_command(label="Quit", command=self.root.destroy, accelerator="Ctrl+Q")
        menu_bar.add_cascade(label="Game", menu=game_menu)

        help_menu = tk.Menu(menu_bar, tearoff=MENU_TEAROFF)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

    def _build_status_area(self) -> None:
        """Create the status label area."""
        status_frame = tk.Frame(self.root, bg=COLORS['bg'])
        status_frame.pack(padx=STATUS_PADDING, pady=(STATUS_PADDING, 6), fill='x')

        self.status_label = tk.Label(
            status_frame,
            text="",
            font=FONTS['status'],
            bg=COLORS['bg'],
            fg=COLORS['status_fg']
        )
        self.status_label.pack(anchor='center')

    def _build_grid_area(self) -> None:
        """Create the game grid area with buttons."""
        self.grid_frame = tk.Frame(self.root, bg=COLORS['grid_bg'])
        self.grid_frame.pack(padx=STATUS_PADDING, pady=6)
        self._build_grid_buttons()

    def _build_control_area(self) -> None:
        """Create the control buttons area."""
        self.control_frame = tk.Frame(self.root, bg=COLORS['bg'])
        self.control_frame.pack(padx=STATUS_PADDING, pady=(6, STATUS_PADDING), fill='x')

        new_game_btn = self._create_control_button("New Game", self.reset_game)
        new_game_btn.pack(side='left', padx=(0, CONTROL_PADDING))

        quit_btn = self._create_control_button("Quit", self.root.destroy)
        quit_btn.pack(side='left')

    def _create_control_button(self, label: str, command) -> tk.Button:
        """
        Create a styled control button.

        Args:
            label: The button label text.
            command: The callback function for button click.

        Returns:
            The configured Button widget.
        """
        return tk.Button(
            self.control_frame,
            text=label,
            font=FONTS['control'],
            bg=COLORS['button_bg'],
            fg=COLORS['button_fg'],
            activebackground=COLORS['button_bg'],
            activeforeground=COLORS['button_fg'],
            command=command
        )

    def _bind_keyboard_shortcuts(self) -> None:
        """Bind keyboard shortcuts to their respective commands."""
        self.root.bind('<Control-n>', lambda e: self.reset_game())
        self.root.bind('<Control-q>', lambda e: self.root.destroy())

    def _build_grid_buttons(self) -> None:
        """Create the 3x3 grid of buttons."""
        assert self.grid_frame is not None
        self.buttons = []

        for row_idx in range(GRID_SIZE):
            row_buttons: List[tk.Button] = []
            for col_idx in range(GRID_SIZE):
                btn = self._create_grid_button(row_idx, col_idx)
                btn.grid(row=row_idx, column=col_idx, padx=GRID_PADDING, pady=GRID_PADDING, sticky='nsew')
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

        # Configure grid weights for even expansion
        for idx in range(GRID_SIZE):
            self.grid_frame.grid_rowconfigure(idx, weight=GRID_WEIGHT, uniform="row")
            self.grid_frame.grid_columnconfigure(idx, weight=GRID_WEIGHT, uniform="col")

    def _create_grid_button(self, row: int, col: int) -> tk.Button:
        """
        Create a styled grid cell button.

        Args:
            row: The row index of the button.
            col: The column index of the button.

        Returns:
            The configured Button widget.
        """
        return tk.Button(
            self.grid_frame,
            text="",
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            font=FONTS['cell'],
            bg=COLORS['button_bg'],
            fg=COLORS['button_fg'],
            activebackground=COLORS['button_bg'],
            activeforeground=COLORS['button_fg'],
            relief=BUTTON_RELIEF,
            borderwidth=BUTTON_BORDERWIDTH,
            command=lambda rr=row, cc=col: self.on_cell_click(rr, cc)
        )

    def on_cell_click(self, row: int, col: int) -> None:
        """
        Handle a click on a cell button.

        Args:
            row: The row index of the clicked cell.
            col: The column index of the clicked cell.
        """
        # Ignore clicks if game already ended
        if self.game.winner is not None or self.game.is_draw():
            logger.debug(f"Ignoring click on ({row}, {col}): game already ended")
            return

        moved = self.game.make_move(row, col)
        if not moved:
            logger.debug(f"Invalid move at ({row}, {col})")
            return

        logger.info(f"Move made at ({row}, {col})")
        self._update_cell_display(row, col)
        self._handle_game_state()

    def _update_cell_display(self, row: int, col: int) -> None:
        """
        Update the display of a cell after a move.

        Args:
            row: The row index of the cell.
            col: The column index of the cell.
        """
        symbol = self.game.get_cell(row, col)
        btn = self.buttons[row][col]
        btn.config(text=symbol)
        self._apply_symbol_style(btn, symbol)

    def _handle_game_state(self) -> None:
        """Handle the current game state and update UI accordingly."""
        if self.game.winner is not None:
            self.highlight_winning_line()
            self.disable_board()
            self.update_status()
            winner_message = f"Player {self.game.winner} wins!"
            logger.info(winner_message)
            messagebox.showinfo("Game Over", winner_message)
        elif self.game.is_draw():
            self.disable_board()
            self.update_status()
            logger.info("Game ended in a draw")
            messagebox.showinfo("Game Over", "It's a draw!")
        else:
            self.update_status()

    def update_status(self) -> None:
        """Update the status label based on game state."""
        if not self.status_label:
            return

        if self.game.winner is not None:
            status_text = f"Player {self.game.winner} wins!"
            # Use winner's color for status text
            status_color = COLORS['x_fg'] if self.game.winner == SYMBOL_X else COLORS['o_fg']
            self.status_label.config(text=status_text, fg=status_color)
        elif self.game.is_draw():
            self.status_label.config(text="It's a draw. Start a new game!", fg=COLORS['status_fg'])
        else:
            # Display current player's turn with matching color
            current_player = self.game.current_player
            status_text = f"Turn: Player {current_player}"
            status_color = COLORS['x_fg'] if current_player == SYMBOL_X else COLORS['o_fg']
            self.status_label.config(text=status_text, fg=status_color)

    def highlight_winning_line(self) -> None:
        """Highlight the winning line cells if there is a winner."""
        if self.game.winning_line is None:
            return

        for row_idx, col_idx in self.game.winning_line:
            btn = self.buttons[row_idx][col_idx]
            btn.config(bg=COLORS['highlight'])
            logger.debug(f"Highlighted winning cell at ({row_idx}, {col_idx})")

    def _apply_symbol_style(self, button: tk.Button, symbol: str) -> None:
        """
        Apply per-symbol foreground color to a button.

        Args:
            button: The button widget to style.
            symbol: The symbol (X, O, or empty) to style for.
        """
        if symbol == SYMBOL_X:
            button.config(fg=COLORS['x_fg'])
        elif symbol == SYMBOL_O:
            button.config(fg=COLORS['o_fg'])
        else:
            button.config(fg=COLORS['button_fg'])

    def disable_board(self) -> None:
        """Disable all grid buttons."""
        for row in self.buttons:
            for btn in row:
                btn.config(state='disabled', disabledforeground=COLORS['button_disabled_fg'])
        logger.debug("Board disabled")

    def enable_board(self) -> None:
        """Enable all grid buttons and reset their appearance."""
        for row_idx, row in enumerate(self.buttons):
            for col_idx, btn in enumerate(row):
                btn.config(state='normal')
                # Re-apply text and symbol style
                symbol = self.game.get_cell(row_idx, col_idx)
                btn.config(text=symbol if symbol else "")
                self._apply_symbol_style(btn, symbol)
                # Reset background to remove any highlight
                btn.config(bg=COLORS['button_bg'])
        logger.debug("Board enabled")

    def reset_game(self) -> None:
        """Reset the game state and UI to start a new match."""
        logger.info("Resetting game")
        self.game.reset(alternate=True)
        # Clear button texts and styles
        for row in self.buttons:
            for btn in row:
                btn.config(text="", bg=COLORS['button_bg'], fg=COLORS['button_fg'], state='normal')
        self.update_status()

    def show_about(self) -> None:
        """Display the About dialog with application information."""
        message = (
            f"{WINDOW_TITLE}\n"
            f"Version {APP_VERSION}\n\n"
            "Two-player Tic-Tac-Toe.\n"
            "- Click a cell to place your mark.\n"
            "- Players alternate as X and O.\n"
            "- First to get 3 in a row wins.\n"
            "- Use 'New Game' (Ctrl+N) to start over."
        )
        messagebox.showinfo("About", message)
        logger.info("About dialog displayed")