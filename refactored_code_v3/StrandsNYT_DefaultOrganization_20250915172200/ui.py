import tkinter as tk
from tkinter import messagebox
import logging

try:
    from .game import GameState
except ImportError:
    from game import GameState

# UI Constants
CELL_SIZE = 52
FONT = ("Helvetica", 16, "bold")
FONT_TITLE = ("Helvetica", 14, "bold")
FONT_STATUS = ("Helvetica", 12)
BUTTON_BG = "#eeeeee"

# Color Constants
COLOR_BG = "#fafafa"
COLOR_CELL_BG = "#ffffff"
COLOR_CELL_BORDER = "#cccccc"
COLOR_CELL_TEXT = "#333333"
COLOR_CELL_TEXT_DARK = "#000000"
COLOR_TEMP = "#b2dfdb"
COLOR_THEME = "#64b5f6"
COLOR_SPANGRAM = "#ffd54f"
COLOR_INVALID = "#ffcdd2"
COLOR_NON_THEME = "#c5e1a5"

# Game Constants
MIN_NON_THEME_LEN = 4
FLASH_DURATION_MS = 250
HINT_THRESHOLD = 3

logger = logging.getLogger(__name__)


class StrandsApp:
    """GUI application for the Strands word puzzle game."""

    def __init__(self, root: tk.Tk, puzzle):
        """
        Initialize the Strands application.

        Args:
            root: The Tkinter root window
            puzzle: The puzzle object containing grid and word data
        """
        self.root = root
        self.root.title("Strands - Programming Languages Edition")
        self.puzzle = puzzle
        self.game = GameState(puzzle)

        self.grid_frame = None
        self.status_frame = None
        self.buttons = {}
        self.cell_states = {}

        # Drag/selection state
        self.dragging = False
        self.selection = []
        self.selection_set = set()

        self._build_ui()
        self._populate_grid()
        self.update_status()

    def _build_ui(self):
        """Build the user interface components."""
        self.root.configure(bg=COLOR_BG)
        self._create_title_label()
        self._create_grid_frame()
        self._create_status_frame()
        self._create_control_buttons()
        self.root.bind("<ButtonRelease-1>", self._global_mouse_up)

    def _create_title_label(self):
        """Create and pack the title label."""
        title = tk.Label(
            self.root,
            text=f"Theme: {self.puzzle.theme}",
            font=FONT_TITLE,
            bg=COLOR_BG
        )
        title.pack(pady=(10, 5))

    def _create_grid_frame(self):
        """Create and configure the grid frame."""
        self.grid_frame = tk.Frame(self.root, bg=COLOR_BG, bd=0, highlightthickness=0)
        self.grid_frame.pack(padx=10, pady=10)

        for r in range(self.puzzle.rows):
            self.grid_frame.grid_rowconfigure(r, weight=1)
        for c in range(self.puzzle.cols):
            self.grid_frame.grid_columnconfigure(c, weight=1)

    def _create_status_frame(self):
        """Create and pack the status display frame."""
        self.status_frame = tk.Frame(self.root, bg=COLOR_BG)
        self.status_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.found_label = tk.Label(
            self.status_frame,
            text="",
            font=FONT_STATUS,
            bg=COLOR_BG
        )
        self.found_label.pack(side="left")

        self.hints_label = tk.Label(
            self.status_frame,
            text="",
            font=FONT_STATUS,
            bg=COLOR_BG
        )
        self.hints_label.pack(side="left", padx=(15, 0))

    def _create_control_buttons(self):
        """Create and pack the control buttons."""
        controls = tk.Frame(self.root, bg=COLOR_BG)
        controls.pack(pady=(0, 10))

        self.hint_button = tk.Button(
            controls,
            text="Use Hint",
            command=self.on_hint,
            bg=BUTTON_BG
        )
        self.hint_button.pack(side="left", padx=5)

        self.reset_button = tk.Button(
            controls,
            text="Reset Progress",
            command=self.on_reset,
            bg=BUTTON_BG
        )
        self.reset_button.pack(side="left", padx=5)

        self.show_words_button = tk.Button(
            controls,
            text="Show Remaining Words",
            command=self.on_show_remaining,
            bg=BUTTON_BG
        )
        self.show_words_button.pack(side="left", padx=5)

    def _populate_grid(self):
        """Populate the grid with letter buttons."""
        for r in range(self.puzzle.rows):
            for c in range(self.puzzle.cols):
                letter = self.puzzle.get_letter(r, c)
                btn = tk.Label(
                    self.grid_frame,
                    text=letter,
                    width=3,
                    height=1,
                    font=FONT,
                    bd=1,
                    relief="solid",
                    bg=COLOR_CELL_BG,
                    fg=COLOR_CELL_TEXT
                )
                btn.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
                self._bind_cell_events(btn, r, c)
                self.buttons[(r, c)] = btn
                self.cell_states[(r, c)] = {
                    'claimed': False,
                    'type': None,
                    'word': None
                }

    def _bind_cell_events(self, button: tk.Label, row: int, col: int):
        """
        Bind mouse events to a grid cell button.

        Args:
            button: The label widget for the cell
            row: Row index
            col: Column index
        """
        button.bind("<ButtonPress-1>", lambda e: self.start_drag(row, col))
        button.bind("<Enter>", lambda e: self.enter_cell(row, col))
        button.bind("<ButtonRelease-1>", lambda e: self.end_drag())

    def on_hint(self):
        """Handle hint button click."""
        if self.game.hints <= 0:
            messagebox.showinfo(
                "No hints",
                f"You don't have any hints yet. Find {HINT_THRESHOLD} non-theme words to earn a hint."
            )
            return

        revealed = self.game.reveal_hint()
        if not revealed:
            messagebox.showinfo("Hints", "All themed words are already found!")
            return

        word, coords, word_type = revealed
        self.apply_claim(coords, word_type, word)
        self.update_status()

        if self.game.is_completed():
            self._show_completion()

    def on_reset(self):
        """Handle reset button click."""
        if not messagebox.askyesno("Reset", "Reset your current progress?"):
            return

        self.game = GameState(self.puzzle)
        self.selection.clear()
        self.selection_set.clear()
        self.dragging = False

        for coord, btn in self.buttons.items():
            btn.configure(bg=COLOR_CELL_BG, fg=COLOR_CELL_TEXT)
            self.cell_states[coord] = {'claimed': False, 'type': None, 'word': None}

        self.update_status()

    def on_show_remaining(self):
        """Handle show remaining words button click."""
        remaining = [
            w for w in self.puzzle.theme_words
            if w not in self.game.found_words
        ]

        if self.puzzle.spangram not in self.game.found_words:
            remaining.insert(0, f"(spangram) {self.puzzle.spangram}")

        if not remaining:
            messagebox.showinfo("Remaining Words", "All words found!")
            return

        message = "Words remaining:\n" + "\n".join(remaining)
        messagebox.showinfo("Remaining Words", message)

    def start_drag(self, row: int, col: int):
        """
        Start a drag selection from a cell.

        Args:
            row: Row index
            col: Column index
        """
        coord = (row, col)
        if not self.game.can_select_cell(coord):
            return

        self.dragging = True
        self.selection = [coord]
        self.selection_set = {coord}
        self._color_cell(coord, COLOR_TEMP)

    def enter_cell(self, row: int, col: int):
        """
        Handle mouse entering a cell during drag.

        Args:
            row: Row index
            col: Column index
        """
        if not self.dragging or not self.selection:
            return

        coord = (row, col)

        # Prevent revisiting cells and selecting claimed cells
        if coord in self.selection_set or not self.game.can_select_cell(coord):
            return

        # Ensure adjacency to last selected cell
        last_coord = self.selection[-1]
        if not self.game.is_adjacent(last_coord, coord):
            return

        self.selection.append(coord)
        self.selection_set.add(coord)
        self._color_cell(coord, COLOR_TEMP)

    def end_drag(self):
        """End the drag selection and process the result."""
        if not self.dragging:
            return

        self.dragging = False
        temp_coords = list(self.selection)
        self.selection.clear()
        self.selection_set.clear()

        result = self.game.try_commit_selection(temp_coords)
        self._process_selection_result(result, temp_coords)
        self.update_status()

        if self.game.is_completed():
            self._show_completion()

    def _process_selection_result(self, result: dict, temp_coords: list):
        """
        Process the result of a selection attempt.

        Args:
            result: Dictionary containing selection result
            temp_coords: List of coordinates that were temporarily highlighted
        """
        result_type = result.get('type')

        if result_type == 'spangram':
            self.apply_claim(result['coords'], 'spangram', result['word'])
        elif result_type == 'theme':
            self.apply_claim(result['coords'], 'theme', result['word'])
        elif result_type == 'non-theme':
            self._flash_cells(temp_coords, COLOR_NON_THEME)
        else:
            self._flash_cells(temp_coords, COLOR_INVALID)

    def _global_mouse_up(self, _event):
        """Handle global mouse release to end drag outside cells."""
        if self.dragging:
            self.end_drag()

    def _color_cell(self, coord: tuple, color: str, text_color: str = COLOR_CELL_TEXT):
        """
        Color a single cell.

        Args:
            coord: Tuple of (row, col)
            color: Background color
            text_color: Text color
        """
        btn = self.buttons.get(coord)
        if btn:
            btn.configure(bg=color, fg=text_color)

    def _flash_cells(self, coords: list, color: str):
        """
        Flash cells with a color temporarily.

        Args:
            coords: List of (row, col) tuples
            color: Color to flash
        """
        for coord in coords:
            if not self.cell_states[coord]['claimed']:
                self._color_cell(coord, color)

        self.root.after(
            FLASH_DURATION_MS,
            lambda: self._restore_temp_colors(coords)
        )

    def _restore_temp_colors(self, coords: list):
        """
        Restore unclaimed cells to default color.

        Args:
            coords: List of (row, col) tuples
        """
        for coord in coords:
            if not self.cell_states[coord]['claimed']:
                self._color_cell(coord, COLOR_CELL_BG, COLOR_CELL_TEXT)

    def apply_claim(self, coords: list, word_type: str, word: str):
        """
        Apply a word claim to cells.

        Args:
            coords: List of (row, col) tuples
            word_type: Type of word ('theme' or 'spangram')
            word: The word string
        """
        color = COLOR_SPANGRAM if word_type == 'spangram' else COLOR_THEME

        for coord in coords:
            self.cell_states[coord] = {
                'claimed': True,
                'type': word_type,
                'word': word
            }
            self._color_cell(coord, color, COLOR_CELL_TEXT_DARK)

    def update_status(self):
        """Update the status labels with current game state."""
        total_theme = len(self.puzzle.theme_words)
        found_theme = sum(
            1 for w in self.puzzle.theme_words
            if w in self.game.found_words
        )
        spangram_found = self.puzzle.spangram in self.game.found_words

        self.found_label.configure(
            text=f"Found: {found_theme}/{total_theme} themes; "
                 f"Spangram: {'Yes' if spangram_found else 'No'}"
        )
        self.hints_label.configure(
            text=f"Hints: {self.game.hints}; "
                 f"Non-theme words: {len(self.game.non_theme_words)}"
        )

    def _show_completion(self):
        """Show completion message."""
        messagebox.showinfo(
            "Congratulations!",
            "You completed the puzzle and filled the board!"
        )