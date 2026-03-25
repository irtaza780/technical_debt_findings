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
TITLE_FONT = ("Helvetica", 14, "bold")
LABEL_FONT = ("Helvetica", 12)
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
    """
    Tkinter GUI application for the Strands word puzzle game.
    
    Handles grid rendering, mouse interactions for word selection via dragging,
    visual feedback, game status display, and hint management.
    """

    def __init__(self, root: tk.Tk, puzzle):
        """
        Initialize the Strands application.
        
        Args:
            root: The Tkinter root window
            puzzle: The puzzle object containing grid data and word definitions
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
        """Build the complete user interface including title, grid, and controls."""
        self.root.configure(bg=COLOR_BG)
        self._create_title_label()
        self._create_grid_frame()
        self._create_status_frame()
        self._create_control_buttons()
        self.root.bind("<ButtonRelease-1>", self._global_mouse_up)

    def _create_title_label(self):
        """Create and pack the puzzle theme title label."""
        title = tk.Label(
            self.root,
            text=f"Theme: {self.puzzle.theme}",
            font=TITLE_FONT,
            bg=COLOR_BG
        )
        title.pack(pady=(10, 5))

    def _create_grid_frame(self):
        """Create and configure the grid frame with proper row/column weights."""
        self.grid_frame = tk.Frame(self.root, bg=COLOR_BG, bd=0, highlightthickness=0)
        self.grid_frame.pack(padx=10, pady=10)

        for r in range(self.puzzle.rows):
            self.grid_frame.grid_rowconfigure(r, weight=1)
        for c in range(self.puzzle.cols):
            self.grid_frame.grid_columnconfigure(c, weight=1)

    def _create_status_frame(self):
        """Create and pack the status display frame with found words and hints info."""
        self.status_frame = tk.Frame(self.root, bg=COLOR_BG)
        self.status_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.found_label = tk.Label(
            self.status_frame,
            text="",
            font=LABEL_FONT,
            bg=COLOR_BG
        )
        self.found_label.pack(side="left")

        self.hints_label = tk.Label(
            self.status_frame,
            text="",
            font=LABEL_FONT,
            bg=COLOR_BG
        )
        self.hints_label.pack(side="left", padx=(15, 0))

    def _create_control_buttons(self):
        """Create and pack the control buttons (hint, reset, show remaining)."""
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
        """Create grid cell buttons and bind mouse event handlers."""
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

                # Bind mouse events with proper coordinate capture
                btn.bind("<ButtonPress-1>", lambda e, rr=r, cc=c: self.start_drag(rr, cc))
                btn.bind("<Enter>", lambda e, rr=r, cc=c: self.enter_cell(rr, cc))
                btn.bind("<ButtonRelease-1>", lambda e, rr=r, cc=c: self.end_drag())

                self.buttons[(r, c)] = btn
                self._initialize_cell_state((r, c))

    def _initialize_cell_state(self, coord):
        """
        Initialize the state dictionary for a cell.
        
        Args:
            coord: Tuple of (row, col)
        """
        self.cell_states[coord] = {
            'claimed': False,
            'type': None,
            'word': None
        }

    def on_hint(self):
        """Handle hint button click: reveal a themed word if hints available."""
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
        """Handle reset button click: confirm and reset all progress."""
        if not messagebox.askyesno("Reset", "Reset your current progress?"):
            return

        self.game = GameState(self.puzzle)
        self.selection.clear()
        self.selection_set.clear()
        self.dragging = False

        # Reset all cell visuals and states
        for coord, btn in self.buttons.items():
            btn.configure(bg=COLOR_CELL_BG, fg=COLOR_CELL_TEXT)
            self._initialize_cell_state(coord)

        self.update_status()

    def on_show_remaining(self):
        """Handle show remaining words button: display words not yet found."""
        remaining = [
            w for w in self.puzzle.theme_words
            if w not in self.game.found_words
        ]

        # Add spangram to front if not found
        if self.puzzle.spangram not in self.game.found_words:
            remaining.insert(0, f"(spangram) {self.puzzle.spangram}")

        if not remaining:
            messagebox.showinfo("Remaining Words", "All words found!")
            return

        message = "Words remaining:\n" + "\n".join(remaining)
        messagebox.showinfo("Remaining Words", message)

    def start_drag(self, r, c):
        """
        Handle mouse press: start a new selection if cell is available.
        
        Args:
            r: Row index
            c: Column index
        """
        coord = (r, c)
        if not self.game.can_select_cell(coord):
            return

        self.dragging = True
        self.selection = [coord]
        self.selection_set = {coord}
        self._color_cell(coord, COLOR_TEMP)

    def enter_cell(self, r, c):
        """
        Handle mouse enter: extend selection if cell is adjacent and available.
        
        Args:
            r: Row index
            c: Column index
        """
        if not self.dragging:
            return

        coord = (r, c)

        # Prevent duplicate cells in selection
        if coord in self.selection_set:
            return

        # Check if cell is available for selection
        if not self.game.can_select_cell(coord):
            return

        if not self.selection:
            return

        # Verify adjacency to last selected cell
        last_coord = self.selection[-1]
        if not self.game.is_adjacent(last_coord, coord):
            return

        self.selection.append(coord)
        self.selection_set.add(coord)
        self._color_cell(coord, COLOR_TEMP)

    def end_drag(self):
        """Handle mouse release: evaluate selection and apply game logic."""
        if not self.dragging:
            return

        self.dragging = False
        temp_coords = list(self.selection)
        self.selection.clear()
        self.selection_set.clear()

        # Evaluate the selection with game logic
        result = self.game.try_commit_selection(temp_coords)
        self._process_selection_result(result, temp_coords)

        self.update_status()

        if self.game.is_completed():
            self._show_completion()

    def _process_selection_result(self, result, temp_coords):
        """
        Process the result of a word selection attempt.
        
        Args:
            result: Dictionary with 'type', 'coords', and 'word' keys
            temp_coords: List of coordinates that were temporarily highlighted
        """
        result_type = result.get('type')

        if result_type == 'spangram':
            self.apply_claim(result['coords'], 'spangram', result['word'])
        elif result_type == 'theme':
            self.apply_claim(result['coords'], 'theme', result['word'])
        elif result_type == 'non-theme':
            # Flash green briefly for valid non-theme word
            self._flash_cells(temp_coords, COLOR_NON_THEME)
        else:
            # Flash red for invalid selection
            self._flash_cells(temp_coords, COLOR_INVALID)

    def _global_mouse_up(self, _event):
        """Handle global mouse release to end drag if released outside grid."""
        if self.dragging:
            self.end_drag()

    def _color_cell(self, coord, color, text_color=COLOR_CELL_TEXT):
        """
        Set the background and text color of a cell.
        
        Args:
            coord: Tuple of (row, col)
            color: Background color hex code
            text_color: Text color hex code
        """
        btn = self.buttons.get(coord)
        if btn:
            btn.configure(bg=color, fg=text_color)

    def _flash_cells(self, coords, color):
        """
        Temporarily highlight cells with a color, then restore.
        
        Args:
            coords: List of (row, col) tuples
            color: Highlight color hex code
        """
        # Paint unclaimed cells with the flash color
        for coord in coords:
            if not self.cell_states[coord]['claimed']:
                self._color_cell(coord, color)

        # Schedule restoration after delay
        self.root.after(
            FLASH_DURATION_MS,
            lambda: self._restore_temp_colors(coords)
        )

    def _restore_temp_colors(self, coords):
        """
        Restore unclaimed cells to their default appearance.
        
        Args:
            coords: List of (row, col) tuples
        """
        for coord in coords:
            if not self.cell_states[coord]['claimed']:
                self._color_cell(coord, COLOR_CELL_BG, COLOR_CELL_TEXT)

    def apply_claim(self, coords, word_type, word):
        """
        Mark cells as claimed and apply appropriate coloring.
        
        Args:
            coords: List of (row, col) tuples
            word_type: 'theme' or 'spangram'
            word: The word string that was found
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
        """Update the status labels with current game progress."""
        total_theme = len(self.puzzle.theme_words)
        found_theme = sum(
            1 for w in self.puzzle.theme_words
            if w in self.game.found_words
        )
        spangram_found = self.puzzle.spangram in self.game.found_words

        self.found_label.configure(
            text=f"Found: {found_theme}/{total_theme} themes; Spangram: {'Yes' if spangram_found else 'No'}"
        )
        self.hints_label.configure(
            text=f"Hints: {self.game.hints}; Non-theme words: {len(self.game.non_theme_words)}"
        )

    def _show_completion(self):
        """Display completion message when puzzle is solved."""
        messagebox.showinfo(
            "Congratulations!",
            "You completed the puzzle and filled the board!"
        )