import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, Callable, Optional
import logging

from crossword_model import CrosswordEntry

# Constants
DEFAULT_WINDOW_TITLE = "Crossword"
DEFAULT_WINDOW_WIDTH = 900
DEFAULT_WINDOW_HEIGHT = 600
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 520
MAIN_PADDING = 10
CONTROLS_PADDING = 10
CONTROLS_PADY = (0, 10)
CLUES_PADY = (8, 0)
SPINBOX_MIN = 1
SPINBOX_MAX = 99
SPINBOX_WIDTH = 6
CELL_WIDTH = 3
CELL_HEIGHT = 1
CELL_FONT = ("Helvetica", 18, "bold")
CELL_BG_EMPTY = "white"
CELL_BG_BLOCKED = "black"
CELL_BORDER_WIDTH = 1
CELL_PADX = 1
CELL_PADY = 1
CLUES_TEXT_HEIGHT = 12
CLUES_TEXT_WRAP = tk.WORD
CLUES_BG = "#fafafa"
STATUS_COLOR_OK = "#0a0"
STATUS_COLOR_ERROR = "#a00"
STATUS_COLOR_DEFAULT = "#333"
INITIAL_STATUS_MESSAGE = "Welcome! Select a clue and enter its answer."
DIRECTION_ACROSS = "A"
DIRECTION_DOWN = "D"
BLOCKED_CELL_MARKER = "#"
FILLED_MARKER = "✓ "
EMPTY_MARKER = "  "
NO_CLUES_TEXT = "(none)"

logger = logging.getLogger(__name__)


class CrosswordView:
    """
    Tkinter GUI for displaying and interacting with a crossword puzzle.
    
    Provides a two-panel layout with the crossword grid on the left and
    controls/clues on the right. Decoupled from the model; exposes methods
    to update display and retrieve user input.
    """

    def __init__(self, root: tk.Tk, title: str = DEFAULT_WINDOW_TITLE):
        """
        Initialize the crossword view.
        
        Args:
            root: The root Tkinter window.
            title: Window title.
        """
        self.root = root
        self.root.title(title)
        self.root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # Initialize grid state
        self.cell_labels: List[List[tk.Label]] = []
        self.rows = 0
        self.cols = 0

        # Initialize callback placeholders
        self._submit_cb: Optional[Callable[[], None]] = None
        self._reset_cb: Optional[Callable[[], None]] = None

        # Build UI components
        self._build_main_layout()
        self._build_left_panel()
        self._build_right_panel()
        self._configure_text_widgets()
        self._bind_events()

        # Set initial focus
        self.answer_entry.focus_set()

    def _build_main_layout(self) -> None:
        """Build the main two-column layout (left grid, right controls/clues)."""
        self.main = ttk.Frame(self.root, padding=MAIN_PADDING)
        self.main.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.main)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = ttk.Frame(self.main)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def _build_left_panel(self) -> None:
        """Build the left panel containing the crossword grid."""
        self.grid_frame = ttk.Frame(self.left_frame)
        self.grid_frame.pack(fill=tk.BOTH, expand=True)

    def _build_right_panel(self) -> None:
        """Build the right panel containing controls, clues, and status."""
        self._build_controls_frame()
        self._build_clues_frame()
        self._build_status_label()

    def _build_controls_frame(self) -> None:
        """Build the answer input controls frame."""
        self.controls_frame = ttk.LabelFrame(
            self.right_frame, text="Enter Answer", padding=CONTROLS_PADDING
        )
        self.controls_frame.pack(fill=tk.X, pady=CONTROLS_PADY)

        # Clue number input
        self.number_var = tk.StringVar()
        self._build_number_input()

        # Direction selection
        self.direction_var = tk.StringVar(value=DIRECTION_ACROSS)
        self._build_direction_input()

        # Answer input
        self.answer_var = tk.StringVar()
        self._build_answer_input()

        # Submit and reset buttons
        self._build_button_row()

    def _build_number_input(self) -> None:
        """Build the clue number input row."""
        number_row = ttk.Frame(self.controls_frame)
        number_row.pack(fill=tk.X, pady=4)
        ttk.Label(number_row, text="Clue number:").pack(side=tk.LEFT)
        self.number_spin = tk.Spinbox(
            number_row,
            from_=SPINBOX_MIN,
            to=SPINBOX_MAX,
            textvariable=self.number_var,
            width=SPINBOX_WIDTH,
            justify=tk.RIGHT,
        )
        self.number_spin.pack(side=tk.LEFT, padx=(8, 0))

    def _build_direction_input(self) -> None:
        """Build the direction selection row."""
        dir_row = ttk.Frame(self.controls_frame)
        dir_row.pack(fill=tk.X, pady=4)
        ttk.Label(dir_row, text="Direction:").pack(side=tk.LEFT)
        self.dir_across_rb = ttk.Radiobutton(
            dir_row, text="Across", variable=self.direction_var, value=DIRECTION_ACROSS
        )
        self.dir_down_rb = ttk.Radiobutton(
            dir_row, text="Down", variable=self.direction_var, value=DIRECTION_DOWN
        )
        self.dir_across_rb.pack(side=tk.LEFT, padx=(8, 0))
        self.dir_down_rb.pack(side=tk.LEFT, padx=(8, 0))

    def _build_answer_input(self) -> None:
        """Build the answer entry field row."""
        ans_row = ttk.Frame(self.controls_frame)
        ans_row.pack(fill=tk.X, pady=4)
        ttk.Label(ans_row, text="Answer:").pack(side=tk.LEFT)
        self.answer_entry = ttk.Entry(ans_row, textvariable=self.answer_var)
        self.answer_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

    def _build_button_row(self) -> None:
        """Build the submit and reset button row."""
        btn_row = ttk.Frame(self.controls_frame)
        btn_row.pack(fill=tk.X, pady=8)
        self.submit_btn = ttk.Button(btn_row, text="Submit")
        self.submit_btn.pack(side=tk.LEFT)
        self.reset_btn = ttk.Button(btn_row, text="Reset")
        self.reset_btn.pack(side=tk.LEFT, padx=8)

    def _build_clues_frame(self) -> None:
        """Build the clues display frame with across and down sections."""
        self.clues_frame = ttk.LabelFrame(
            self.right_frame, text="Clues", padding=CONTROLS_PADDING
        )
        self.clues_frame.pack(fill=tk.BOTH, expand=True)

        # Across clues
        ttk.Label(self.clues_frame, text="Across").pack(anchor=tk.W)
        self.across_text = tk.Text(
            self.clues_frame, height=CLUES_TEXT_HEIGHT, wrap=CLUES_TEXT_WRAP
        )
        self.across_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Down clues
        ttk.Label(self.clues_frame, text="Down").pack(anchor=tk.W)
        self.down_text = tk.Text(
            self.clues_frame, height=CLUES_TEXT_HEIGHT, wrap=CLUES_TEXT_WRAP
        )
        self.down_text.pack(fill=tk.BOTH, expand=True)

    def _build_status_label(self) -> None:
        """Build the status message label."""
        self.status_var = tk.StringVar(value=INITIAL_STATUS_MESSAGE)
        self.status_label = ttk.Label(
            self.right_frame, textvariable=self.status_var, foreground=STATUS_COLOR_DEFAULT
        )
        self.status_label.pack(fill=tk.X, pady=CLUES_PADY)

    def _configure_text_widgets(self) -> None:
        """Configure text widgets as read-only with custom styling."""
        for text_widget in (self.across_text, self.down_text):
            text_widget.configure(state=tk.DISABLED)
            text_widget.configure(background=CLUES_BG)

    def _bind_events(self) -> None:
        """Bind keyboard and button events."""
        self.answer_entry.bind("<Return>", lambda e: self._on_submit_enter())

    def _on_submit_enter(self) -> None:
        """Handle Enter key press in answer field."""
        if self._submit_cb:
            self._submit_cb()

    def set_number_range(self, min_num: int, max_num: int) -> None:
        """
        Set the valid range for clue numbers in the spinbox.
        
        Args:
            min_num: Minimum clue number.
            max_num: Maximum clue number.
        """
        try:
            self.number_spin.config(from_=min_num, to=max_num)
        except tk.TclError as e:
            logger.warning(f"Failed to set spinbox range: {e}")

    def build_grid(self, rows: int, cols: int) -> None:
        """
        Build the crossword grid display.
        
        Creates a grid of label widgets with the specified dimensions.
        Clears any previously built grid.
        
        Args:
            rows: Number of rows in the grid.
            cols: Number of columns in the grid.
        """
        # Clear previous grid
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.cell_labels = []
        self.rows = rows
        self.cols = cols

        # Build new grid of labels
        for r in range(rows):
            row_labels: List[tk.Label] = []
            for c in range(cols):
                lbl = tk.Label(
                    self.grid_frame,
                    text="",
                    width=CELL_WIDTH,
                    height=CELL_HEIGHT,
                    borderwidth=CELL_BORDER_WIDTH,
                    relief="solid",
                    font=CELL_FONT,
                    bg=CELL_BG_EMPTY,
                )
                lbl.grid(row=r, column=c, sticky="nsew", padx=CELL_PADX, pady=CELL_PADY)
                row_labels.append(lbl)
            self.cell_labels.append(row_labels)

        # Configure grid weights for uniform expansion
        for r in range(rows):
            self.grid_frame.rowconfigure(r, weight=1)
        for c in range(cols):
            self.grid_frame.columnconfigure(c, weight=1)

    def update_grid(self, cell_value_at: Callable[[int, int], str]) -> None:
        """
        Update the grid display with current cell values.
        
        Args:
            cell_value_at: Callable that returns the value for cell (row, col).
                          Returns "#" for blocked cells, or the answer character.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                val = cell_value_at(r, c)
                lbl = self.cell_labels[r][c]
                # Blocked cells are displayed as black with no text
                if val == BLOCKED_CELL_MARKER:
                    lbl.configure(text="", bg=CELL_BG_BLOCKED)
                else:
                    lbl.configure(text=val if val else "", bg=CELL_BG_EMPTY)

    def render_clues(
        self,
        across_entries: List[CrosswordEntry],
        down_entries: List[CrosswordEntry],
    ) -> None:
        """
        Render clue lists for across and down directions.
        
        Args:
            across_entries: List of CrosswordEntry objects for across clues.
            down_entries: List of CrosswordEntry objects for down clues.
        """
        across_text = self._format_clue_list(across_entries, DIRECTION_ACROSS)
        down_text = self._format_clue_list(down_entries, DIRECTION_DOWN)

        self._set_text(self.across_text, across_text)
        self._set_text(self.down_text, down_text)

    def _format_clue_list(
        self, entries: List[CrosswordEntry], direction: str
    ) -> str:
        """
        Format a list of clue entries into a displayable string.
        
        Args:
            entries: List of CrosswordEntry objects.
            direction: Direction indicator ("A" for across, "D" for down).
            
        Returns:
            Formatted string with clues, one per line.
        """
        if not entries:
            return NO_CLUES_TEXT

        lines = []
        for entry in entries:
            # Add checkmark if clue is filled
            mark = FILLED_MARKER if entry.filled else EMPTY_MARKER
            line = f"{mark}{entry.number}{direction} ({entry.length}): {entry.clue}"
            lines.append(line)

        return "\n".join(lines)

    def _set_text(self, text_widget: tk.Text, content: str) -> None:
        """
        Set the content of a read-only text widget.
        
        Temporarily enables the widget, updates content, then disables it again.
        
        Args:
            text_widget: The Text widget to update.
            content: The new content to display.
        """
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, content)
        text_widget.configure(state=tk.DISABLED)

    def get_input(self) -> Tuple[Optional[int], str, str]:
        """
        Retrieve the current user input from controls.
        
        Returns:
            Tuple of (clue_number, direction, answer) where:
            - clue_number: int or None if invalid
            - direction: "A" or "D"
            - answer: user-entered answer string
        """
        num_str = self.number_var.get().strip()
        try:
            number = int(num_str)
        except ValueError:
            number = None

        direction = (self.direction_var.get() or DIRECTION_ACROSS).upper()
        answer = self.answer_var.get().strip()

        return number, direction, answer

    def clear_answer_field(self) -> None:
        """Clear the answer input field and restore focus."""
        self.answer_var.set("")
        self.answer_entry.focus_set()
        self.answer_entry.icursor(