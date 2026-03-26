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
BORDER_WIDTH = 2
MENU_TEAROFF = 0


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

    def build_ui(self) -> None:
        """Create all UI components and layout."""
        self._build_menu()
        self._build_status_area()
        self._build_grid_area()
        self._build_control_area()
        self._bind_keyboard_shortcuts()
        self.update_status()
        logger.info("UI built successfully")

    def _build_menu(self) -> None:
        """Create the application menu bar with Game and Help menus."""
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
        """Create and configure the status label area."""
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
        """Create and configure the game grid with buttons."""
        self.grid_frame = tk.Frame(self.root, bg=COLORS['grid_bg'])
        self.grid_frame.pack(padx=STATUS_PADDING, pady=6)
        self._build_grid_buttons()

    def _build_grid_buttons(self) -> None:
        """Create the 3x3 grid of game cell buttons."""
        assert self.grid_frame is not None
        self.buttons = []

        for row_idx in range(GRID_SIZE):
            row_buttons: List[tk.Button] = []
            for col_idx in range(GRID_SIZE):
                button = self._create_grid_button(row_idx, col_idx)
                button.grid(row=row_idx, column=col_idx, padx=GRID_PADDING, pady=GRID_PADDING, sticky='nsew')
                row_buttons.append(button)
            self.buttons.append(row_buttons)

        # Configure grid weights for even expansion
        for idx in range(GRID_SIZE):
            self.grid_frame.grid_rowconfigure(idx, weight=1, uniform="row")
            self.grid_frame.grid_columnconfigure(idx, weight=1, uniform="col")

    def _create_grid_button(self, row: int, col: int) -> tk.Button:
        """
        Create a single grid button with styling and command binding.

        Args:
            row: The row index of the button.
            col: The column index of the button.

        Returns:
            A configured tk.Button instance.
        """
        button = tk.Button(
            self.grid_frame,
            text="",
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            font=FONTS['cell'],
            bg=COLORS['button_bg'],
            fg=COLORS['button_fg'],
            activebackground=COLORS['button_bg'],
            activeforeground=COLORS['button_fg'],
            relief='raised',
            borderwidth=BORDER_WIDTH,
            command=lambda r=row, c=col: self.on_cell_click(r, c)
        )
        return button

    def _build_control_area(self) -> None:
        """Create and configure the control buttons area."""
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
            command: The callback function for the button.

        Returns:
            A configured tk.Button instance.
        """
        button = tk.Button(
            self.control_frame,
            text=label,
            font=FONTS['control'],
            bg=COLORS['button_bg'],
            fg=COLORS['button_fg'],
            activebackground=COLORS['button_bg'],
            activeforeground=COLORS['button_fg'],
            command=command
        )
        return button

    def _bind_keyboard_shortcuts(self) -> None:
        """Bind keyboard shortcuts for game actions."""
        self.root.bind('<Control-n>', lambda e: self.reset_game())
        self.root.bind('<Control-q>', lambda e: self.root.destroy())

    def on_cell_click(self, row: int, col: int) -> None:
        """
        Handle a click on a game cell button.

        Args:
            row: The row index of the clicked cell.
            col: The column index of the clicked cell.
        """
        # Ignore clicks if game has already ended
        if self._is_game_over():
            return

        # Attempt to make the move
        if not self.game.make_move(row, col):
            logger.debug(f"Invalid move attempted at ({row}, {col})")
            return

        # Update the button display
        symbol = self.game.get_cell(row, col)
        button = self.buttons[row][col]
        button.config(text=symbol)
        self._apply_symbol_style(button, symbol)

        # Handle game end conditions
        self._handle_game_state()

    def _is_game_over(self) -> bool:
        """
        Check if the game has ended.

        Returns:
            True if there is a winner or the game is a draw, False otherwise.
        """
        return self.game.winner is not None or self.game.is_draw()

    def _handle_game_state(self) -> None:
        """Handle the current game state and update UI accordingly."""
        if self.game.winner is not None:
            self.highlight_winning_line()
            self.disable_board()
            self.update_status()
            winner = self.game.winner
            messagebox.showinfo("Game Over", f"Player {winner} wins!")
            logger.info(f"Game won by player {winner}")
        elif self.game.is_draw():
            self.disable_board()
            self.update_status()
            messagebox.showinfo("Game Over", "It's a draw!")
            logger.info("Game ended in a draw")
        else:
            self.update_status()

    def update_status(self) -> None:
        """Update the status label based on the current game state."""
        if not self.status_label:
            return

        if self.game.winner is not None:
            self._update_status_winner()
        elif self.game.is_draw():
            self._update_status_draw()
        else:
            self._update_status_turn()

    def _update_status_winner(self) -> None:
        """Update status label to show the winner."""
        winner = self.game.winner
        color = COLORS['x_fg'] if winner == SYMBOL_X else COLORS['o_fg']
        self.status_label.config(text=f"Player {winner} wins!", fg=color)

    def _update_status_draw(self) -> None:
        """Update status label to show a draw."""
        self.status_label.config(text="It's a draw. Start a new game!", fg=COLORS['status_fg'])

    def _update_status_turn(self) -> None:
        """Update status label to show whose turn it is."""
        current_player = self.game.current_player
        color = COLORS['x_fg'] if current_player == SYMBOL_X else COLORS['o_fg']
        self.status_label.config(text=f"Turn: Player {current_player}", fg=color)

    def highlight_winning_line(self) -> None:
        """Highlight the cells that form the winning line."""
        if self.game.winning_line is None:
            return

        for row, col in self.game.winning_line:
            button = self.buttons[row][col]
            button.config(bg=COLORS['highlight'])

    def _apply_symbol_style(self, button: tk.Button, symbol: str) -> None:
        """
        Apply foreground color styling based on the symbol.

        Args:
            button: The button to style.
            symbol: The symbol (X, O, or empty string).
        """
        if symbol == SYMBOL_X:
            button.config(fg=COLORS['x_fg'])
        elif symbol == SYMBOL_O:
            button.config(fg=COLORS['o_fg'])
        else:
            button.config(fg=COLORS['button_fg'])

    def disable_board(self) -> None:
        """Disable all grid buttons to prevent further moves."""
        for row in self.buttons:
            for button in row:
                button.config(state='disabled', disabledforeground=COLORS['button_disabled_fg'])

    def enable_board(self) -> None:
        """Enable all grid buttons and reset their appearance."""
        for row_idx, row in enumerate(self.buttons):
            for col_idx, button in enumerate(row):
                button.config(state='normal')
                symbol = self.game.get_cell(row_idx, col_idx)
                button.config(text=symbol if symbol else "")
                self._apply_symbol_style(button, symbol)
                button.config(bg=COLORS['button_bg'])

    def reset_game(self) -> None:
        """Reset the game state and UI for a new match."""
        self.game.reset(alternate=True)
        self._reset_board_display()
        self.update_status()
        logger.info("Game reset for new match")

    def _reset_board_display(self) -> None:
        """Clear all button displays and reset their styling."""
        for row in self.buttons:
            for button in row:
                button.config(
                    text="",
                    bg=COLORS['button_bg'],
                    fg=COLORS['button_fg'],
                    state='normal'
                )

    def show_about(self) -> None:
        """Display the About dialog with game information."""
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