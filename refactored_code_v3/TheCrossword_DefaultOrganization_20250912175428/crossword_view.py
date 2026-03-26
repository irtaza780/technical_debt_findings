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
CLUES_PADDING = 10
STATUS_PADY = (8, 0)
SPINBOX_MIN = 1
SPINBOX_MAX = 99
SPINBOX_WIDTH = 6
CELL_WIDTH = 3
CELL_HEIGHT = 1
CELL_FONT = ("Helvetica", 18, "bold")
CELL_BG_EMPTY = "white"
CELL_BG_BLOCKED = "black"
CELL_BORDER_WIDTH = 1
CELL_PADDING_X = 1
CELL_PADDING_Y = 1
CLUES_TEXT_HEIGHT = 12
CLUES_BG = "#fafafa"
STATUS_COLOR_OK = "#0a0"
STATUS_COLOR_ERROR = "#a00"
STATUS_COLOR_DEFAULT = "#333"
DIRECTION_ACROSS = "A"
DIRECTION_DOWN = "D"
BLOCKED_CELL = "#"
FILLED_MARK = "✓ "
EMPTY_MARK = "  "
NO_CLUES_TEXT = "(none)"
INITIAL_STATUS = "Welcome! Select a clue and enter its answer."

logger = logging.getLogger(__name__)


class CrosswordView:
    """
    Tkinter GUI for displaying and interacting with a crossword puzzle.
    
    Manages the grid display, clue rendering, user input controls, and status messages.
    Decoupled from the model; exposes methods to update display and bind event handlers.
    """

    def __init__(self, root: tk.Tk, title: str = DEFAULT_WINDOW_TITLE):
        """
        Initialize the crossword view with main window and layout.
        
        Args:
            root: The root Tkinter window.
            title: Window title (default: "Crossword").
        """
        self.root = root
        self._configure_window(title)
        self._create_main_layout()
        self._create_grid_frame()
        self._create_controls_frame()
        self._create_clues_frame()
        self._create_status_frame()
        self._initialize_grid_state()
        self._initialize_control_variables()
        self._setup_event_bindings()
        self._initialize_callbacks()
        self.answer_entry.focus_set()

    def _configure_window(self, title: str) -> None:
        """Configure the root window properties."""
        self.root.title(title)
        self.root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

    def _create_main_layout(self) -> None:
        """Create the main layout with left and right frames."""
        self.main = ttk.Frame(self.root, padding=MAIN_PADDING)
        self.main.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.main)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = ttk.Frame(self.main)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def _create_grid_frame(self) -> None:
        """Create the frame for the crossword grid."""
        self.grid_frame = ttk.Frame(self.left_frame)
        self.grid_frame.pack(fill=tk.BOTH, expand=True)

    def _create_controls_frame(self) -> None:
        """Create the controls frame with input fields and buttons."""
        self.controls_frame = ttk.LabelFrame(
            self.right_frame, text="Enter Answer", padding=CONTROLS_PADDING
        )
        self.controls_frame.pack(fill=tk.X, pady=CONTROLS_PADY)

        self._create_number_input()
        self._create_direction_input()
        self._create_answer_input()
        self._create_action_buttons()

    def _create_number_input(self) -> None:
        """Create the clue number input row."""
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

    def _create_direction_input(self) -> None:
        """Create the direction selection row."""
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

    def _create_answer_input(self) -> None:
        """Create the answer entry field row."""
        ans_row = ttk.Frame(self.controls_frame)
        ans_row.pack(fill=tk.X, pady=4)
        ttk.Label(ans_row, text="Answer:").pack(side=tk.LEFT)
        self.answer_entry = ttk.Entry(ans_row, textvariable=self.answer_var)
        self.answer_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

    def _create_action_buttons(self) -> None:
        """Create the submit and reset buttons."""
        btn_row = ttk.Frame(self.controls_frame)
        btn_row.pack(fill=tk.X, pady=8)
        self.submit_btn = ttk.Button(btn_row, text="Submit")
        self.submit_btn.pack(side=tk.LEFT)
        self.reset_btn = ttk.Button(btn_row, text="Reset")
        self.reset_btn.pack(side=tk.LEFT, padx=8)

    def _create_clues_frame(self) -> None:
        """Create the clues display frame with across and down sections."""
        self.clues_frame = ttk.LabelFrame(
            self.right_frame, text="Clues", padding=CLUES_PADDING
        )
        self.clues_frame.pack(fill=tk.BOTH, expand=True)

        self._create_clues_text_widgets()

    def _create_clues_text_widgets(self) -> None:
        """Create and configure the across and down clues text widgets."""
        self.across_text = tk.Text(self.clues_frame, height=CLUES_TEXT_HEIGHT, wrap=tk.WORD)
        self.down_text = tk.Text(self.clues_frame, height=CLUES_TEXT_HEIGHT, wrap=tk.WORD)

        ttk.Label(self.clues_frame, text="Across").pack(anchor=tk.W)
        self.across_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        ttk.Label(self.clues_frame, text="Down").pack(anchor=tk.W)
        self.down_text.pack(fill=tk.BOTH, expand=True)

        # Configure text widgets as read-only
        for text_widget in (self.across_text, self.down_text):
            text_widget.configure(state=tk.DISABLED, background=CLUES_BG)

    def _create_status_frame(self) -> None:
        """Create the status message label."""
        self.status_var = tk.StringVar(value=INITIAL_STATUS)
        self.status_label = ttk.Label(
            self.right_frame, textvariable=self.status_var, foreground=STATUS_COLOR_DEFAULT
        )
        self.status_label.pack(fill=tk.X, pady=STATUS_PADY)

    def _initialize_grid_state(self) -> None:
        """Initialize grid-related state variables."""
        self.cell_labels: List[List[tk.Label]] = []
        self.rows = 0
        self.cols = 0

    def _initialize_control_variables(self) -> None:
        """Initialize Tkinter variables for user input controls."""
        self.number_var = tk.StringVar()
        self.direction_var = tk.StringVar(value=DIRECTION_ACROSS)
        self.answer_var = tk.StringVar()

    def _setup_event_bindings(self) -> None:
        """Set up event bindings for user interactions."""
        # Bind Enter key to submit answer
        self.answer_entry.bind("<Return>", lambda e: self._on_submit_enter())

    def _initialize_callbacks(self) -> None:
        """Initialize callback placeholders."""
        self._submit_cb: Optional[Callable[[], None]] = None
        self._reset_cb: Optional[Callable[[], None]] = None

    def _on_submit_enter(self) -> None:
        """Handle Enter key press in answer entry field."""
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
        Build the crossword grid with the specified dimensions.
        
        Args:
            rows: Number of rows in the grid.
            cols: Number of columns in the grid.
        """
        # Clear any previous grid
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.cell_labels = []
        self.rows = rows
        self.cols = cols

        # Build new grid of labels
        for r in range(rows):
            row_labels: List[tk.Label] = []
            for c in range(cols):
                lbl = self._create_grid_cell(r, c)
                row_labels.append(lbl)
            self.cell_labels.append(row_labels)

        # Configure grid weights for uniform expansion
        self._configure_grid_weights(rows, cols)

    def _create_grid_cell(self, row: int, col: int) -> tk.Label:
        """
        Create a single grid cell label.
        
        Args:
            row: Row index.
            col: Column index.
            
        Returns:
            Configured Label widget for the grid cell.
        """
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
        lbl.grid(row=row, column=col, sticky="nsew", padx=CELL_PADDING_X, pady=CELL_PADDING_Y)
        return lbl

    def _configure_grid_weights(self, rows: int, cols: int) -> None:
        """
        Configure grid row and column weights for uniform expansion.
        
        Args:
            rows: Number of rows.
            cols: Number of columns.
        """
        for r in range(rows):
            self.grid_frame.rowconfigure(r, weight=1)
        for c in range(cols):
            self.grid_frame.columnconfigure(c, weight=1)

    def update_grid(self, cell_value_at: Callable[[int, int], str]) -> None:
        """
        Update the grid display with current cell values.
        
        Args:
            cell_value_at: Callable that returns the value for cell (row, col).
        """
        for r in range(self.rows):
            for c in range(self.cols):
                val = cell_value_at(r, c)
                lbl = self.cell_labels[r][c]
                # Blocked cells are displayed as black with no text
                if val == BLOCKED_CELL:
                    lbl.configure(text="", bg=CELL_BG_BLOCKED)
                else:
                    lbl.configure(text=val if val else "", bg=CELL_BG_EMPTY)

    def render_clues(
        self, across_entries: List[CrosswordEntry], down_entries: List[CrosswordEntry]
    ) -> None:
        """
        Render clues for across and down entries.
        
        Args:
            across_entries: List of across clue entries.
            down_entries: List of down clue entries.
        """
        across_str = self._format_clue_list(across_entries, DIRECTION_ACROSS)
        down_str = self._format_clue_list(down_entries, DIRECTION_DOWN)

        self._set_text(self.across_text, across_str)
        self._set_text(self.down_text, down_str)

    def _format_clue_list(self, entries: List[CrosswordEntry], direction: str) -> str:
        """
        Format a list of clue entries into a displayable string.
        
        Args:
            entries: List of clue entries.
            direction: Direction indicator ("A" for across, "D" for down).
            
        Returns:
            Formatted string with all clues.
        """
        if not entries:
            return NO_CLUES_TEXT

        lines = []
        for entry in entries:
            # Mark filled clues with a checkmark
            mark = FILLED_MARK if entry.filled else EMPTY_MARK
            direction_suffix = "A" if direction == DIRECTION_ACROSS else "D"
            line = f"{mark}{entry.number}{direction_suffix} ({entry.length}): {entry.clue}"
            lines.append(line)

        return "\n".join(lines)

    def _set_text(self, text_widget: tk.Text, content: str) -> None:
        """
        Set the content of a read-only text widget.
        
        Args:
            text_widget: The Text widget to update.
            content: The content to display.
        """
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, content)
        text_widget.configure(state=tk.DISABLED)

    def get_input(self) -> Tuple[Optional[int], str, str]:
        """
        Retrieve the current user input from controls.
        
        Returns:
            Tuple of (clue_number, direction, answer).
            clue_number is None if input is invalid.
        """
        num_str = self.number_var.get().strip()
        try: