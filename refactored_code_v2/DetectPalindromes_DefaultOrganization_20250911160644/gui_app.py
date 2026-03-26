import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict

from palindrome_detector import (
    DetectionOptions,
    detect_palindromes,
    PalindromeMatch,
)
from file_utils import read_text_file
from exporter import export_results_to_csv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UI Constants
DEFAULT_MIN_LENGTH = 3
MIN_LENGTH_SPINBOX_MIN = 1
MIN_LENGTH_SPINBOX_MAX = 100
MIN_LENGTH_SPINBOX_WIDTH = 5
PADDING_STANDARD = 8
PADDING_SMALL = 6
PADDING_LARGE = 20
COLUMN_WIDTH_CATEGORY = 90
COLUMN_WIDTH_CONTENT = 500
COLUMN_WIDTH_NUMERIC = 60
HIGHLIGHT_COLOR_MATCH = "#fffd86"
HIGHLIGHT_COLOR_LINE = "#e8f4ff"
WINDOW_TITLE = "Palindrome Detector"
STATUS_INITIAL = "Open a text file to begin."
STATUS_LOADED = "Loaded: {}"
STATUS_FOUND = "Found {} palindrome(s)."
NEWLINE_DISPLAY = "\\n"

# Tree columns
TREE_COLUMNS = ("category", "content", "length", "line", "start", "end")
TREE_COLUMN_HEADERS = {
    "category": "Category",
    "content": "Content",
    "length": "Length",
    "line": "Line",
    "start": "Start",
    "end": "End",
}
TREE_COLUMN_WIDTHS = {
    "category": COLUMN_WIDTH_CATEGORY,
    "content": COLUMN_WIDTH_CONTENT,
    "length": COLUMN_WIDTH_NUMERIC,
    "line": COLUMN_WIDTH_NUMERIC,
    "start": COLUMN_WIDTH_NUMERIC,
    "end": COLUMN_WIDTH_NUMERIC,
}


class PalindromeGUI(tk.Tk):
    """Main GUI window for the Palindrome Detector application.
    
    Provides controls to open files, configure detection options, analyze text,
    view results, highlight matches in a preview, and export results to CSV.
    """

    def __init__(self):
        """Initialize the GUI application."""
        super().__init__()
        self.title(WINDOW_TITLE)
        
        self._build_vars()
        self._build_menu()
        self._build_layout()
        self._connect_events()

        self.loaded_text: str = ""
        self.results = []
        self.tree_item_to_result: Dict[str, PalindromeMatch] = {}

    def _build_vars(self) -> None:
        """Initialize all Tkinter variables for options and status."""
        # Detection type options
        self.var_words = tk.BooleanVar(value=True)
        self.var_sentences = tk.BooleanVar(value=True)
        self.var_lines = tk.BooleanVar(value=True)
        
        # Processing options
        self.var_ignore_case = tk.BooleanVar(value=True)
        self.var_ignore_non_alnum = tk.BooleanVar(value=True)
        self.var_min_length = tk.IntVar(value=DEFAULT_MIN_LENGTH)

        # Status display
        self.var_status = tk.StringVar(value=STATUS_INITIAL)

    def _build_menu(self) -> None:
        """Build the application menu bar."""
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Open...", command=self.on_open_file)
        file_menu.add_command(label="Analyze", command=self.on_analyze)
        file_menu.add_separator()
        file_menu.add_command(label="Export Results...", command=self.on_export)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About", command=self.on_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_layout(self) -> None:
        """Build the main window layout with all frames and widgets."""
        self._build_controls_frame()
        self._build_results_frame()
        self._build_preview_frame()
        self._build_status_bar()

    def _build_controls_frame(self) -> None:
        """Build the detection options control frame."""
        controls = ttk.LabelFrame(self, text="Detection Options")
        controls.pack(side=tk.TOP, fill=tk.X, padx=PADDING_STANDARD, pady=PADDING_SMALL)

        # Detection type checkboxes
        self._build_detection_checkboxes(controls)
        
        # Processing options checkboxes
        self._build_processing_checkboxes(controls)
        
        # Minimum length spinbox
        self._build_min_length_control(controls)
        
        # Action buttons
        self._build_action_buttons(controls)

    def _build_detection_checkboxes(self, parent: ttk.Frame) -> None:
        """Build checkboxes for detection types (words, sentences, lines).
        
        Args:
            parent: Parent frame to contain the checkboxes.
        """
        check_frame = ttk.Frame(parent)
        check_frame.pack(side=tk.LEFT, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
        ttk.Checkbutton(check_frame, text="Words", variable=self.var_words).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Checkbutton(check_frame, text="Sentences", variable=self.var_sentences).grid(
            row=1, column=0, sticky="w"
        )
        ttk.Checkbutton(check_frame, text="Lines", variable=self.var_lines).grid(
            row=2, column=0, sticky="w"
        )

    def _build_processing_checkboxes(self, parent: ttk.Frame) -> None:
        """Build checkboxes for processing options (case, alphanumeric).
        
        Args:
            parent: Parent frame to contain the checkboxes.
        """
        opt_frame = ttk.Frame(parent)
        opt_frame.pack(side=tk.LEFT, padx=PADDING_LARGE, pady=PADDING_SMALL)
        
        ttk.Checkbutton(opt_frame, text="Ignore case", variable=self.var_ignore_case).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Checkbutton(
            opt_frame, text="Ignore non-alphanumeric", variable=self.var_ignore_non_alnum
        ).grid(row=1, column=0, sticky="w")

    def _build_min_length_control(self, parent: ttk.Frame) -> None:
        """Build minimum length spinbox control.
        
        Args:
            parent: Parent frame to contain the control.
        """
        minlen_frame = ttk.Frame(parent)
        minlen_frame.pack(side=tk.LEFT, padx=PADDING_LARGE, pady=PADDING_SMALL)
        
        ttk.Label(minlen_frame, text="Minimum length:").grid(row=0, column=0, sticky="w")
        self.spin_min_length = ttk.Spinbox(
            minlen_frame,
            from_=MIN_LENGTH_SPINBOX_MIN,
            to=MIN_LENGTH_SPINBOX_MAX,
            textvariable=self.var_min_length,
            width=MIN_LENGTH_SPINBOX_WIDTH,
        )
        self.spin_min_length.grid(row=0, column=1, sticky="w", padx=5)

    def _build_action_buttons(self, parent: ttk.Frame) -> None:
        """Build action buttons (Open, Analyze, Export).
        
        Args:
            parent: Parent frame to contain the buttons.
        """
        action_frame = ttk.Frame(parent)
        action_frame.pack(side=tk.RIGHT, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
        self.btn_open = ttk.Button(action_frame, text="Open...", command=self.on_open_file)
        self.btn_open.grid(row=0, column=0, padx=4)
        
        self.btn_analyze = ttk.Button(action_frame, text="Analyze", command=self.on_analyze)
        self.btn_analyze.grid(row=0, column=1, padx=4)
        
        self.btn_export = ttk.Button(
            action_frame, text="Export Results...", command=self.on_export, state=tk.DISABLED
        )
        self.btn_export.grid(row=0, column=2, padx=4)

    def _build_results_frame(self) -> None:
        """Build the results treeview frame."""
        results_frame = ttk.LabelFrame(self, text="Results")
        results_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=PADDING_STANDARD, pady=(0, PADDING_SMALL))

        # Create treeview with columns
        self.tree = ttk.Treeview(
            results_frame, columns=TREE_COLUMNS, show="headings", selectmode="browse"
        )
        
        # Configure column headings and widths
        for col in TREE_COLUMNS:
            self.tree.heading(col, text=TREE_COLUMN_HEADERS[col])
            self.tree.column(col, width=TREE_COLUMN_WIDTHS[col], anchor="w")
        
        # Center-align numeric columns
        for col in ("length", "line", "start", "end"):
            self.tree.column(col, anchor="center")

        # Add scrollbar
        tree_scroll_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        
        results_frame.rowconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)

    def _build_preview_frame(self) -> None:
        """Build the file preview text frame with scrollbars."""
        preview_frame = ttk.LabelFrame(self, text="File Preview")
        preview_frame.pack(
            side=tk.TOP, fill=tk.BOTH, expand=True, padx=PADDING_STANDARD, pady=(0, PADDING_STANDARD)
        )

        # Create text widget
        self.text_preview = tk.Text(preview_frame, wrap="none", undo=False)
        self.text_preview.config(state=tk.DISABLED)
        
        # Configure highlight tags
        self.text_preview.tag_configure("highlight", background=HIGHLIGHT_COLOR_MATCH)
        self.text_preview.tag_configure("linehl", background=HIGHLIGHT_COLOR_LINE)

        # Add scrollbars
        yscroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.text_preview.yview)
        xscroll = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.text_preview.xview)
        self.text_preview.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        
        self.text_preview.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)

    def _build_status_bar(self) -> None:
        """Build the status bar at the bottom of the window."""
        status_bar = ttk.Frame(self)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.lbl_status = ttk.Label(status_bar, textvariable=self.var_status, anchor="w")
        self.lbl_status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=PADDING_STANDARD, pady=4)

    def _connect_events(self) -> None:
        """Connect event handlers to widgets."""
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def on_about(self) -> None:
        """Display the About dialog."""
        messagebox.showinfo(
            "About",
            "Palindrome Detector\n\n"
            "Detect palindromic words, sentences, and lines in text files.\n"
            "Options allow ignoring case and non-alphanumeric characters.\n\n"
            "Built with tkinter.",
        )

    def on_open_file(self) -> None:
        """Open a file dialog and load the selected text file."""
        path = filedialog.askopenfilename(
            title="Open Text File",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            txt = read_text_file(path)
        except IOError as e:
            logger.error(f"Failed to open file {path}: {e}")
            messagebox.showerror("Error", f"Failed to open file:\n{e}")
            return

        self.loaded_text = txt
        self._set_preview_text(self.loaded_text)
        self._clear_results()
        self.var_status.set(STATUS_LOADED.format(path))
        self.btn_export.configure(state=tk.DISABLED)
        logger.info(f"Loaded file: {path}")

    def _set_preview_text(self, text: str) -> None:
        """Update the preview text widget with new content.
        
        Args:
            text: The text content to display.
        """
        self.text_preview.config(state=tk.NORMAL)
        self.text_preview.delete("1.0", tk.END)
        self.text_preview.insert("1.0", text)
        self.text_preview.config(state=tk.DISABLED)

    def _clear_results(self) -> None:
        """Clear all results from the treeview and internal storage."""
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.tree_item_to_result.clear()
        self.results = []
        self._clear_highlight()

    def _clear_highlight(self) -> None:
        """Remove all highlight tags from the preview text."""
        self.text_preview.config(state=tk.NORMAL)
        self.text_preview.tag_remove("highlight", "1.0", tk.END)
        self.text_preview.tag_remove("linehl", "1.0", tk.END)
        self.text_preview.config(state=tk.DISABLED)

    def _collect_options(self) -> DetectionOptions:
        """Collect detection options from UI variables.
        
        Returns:
            DetectionOptions object with current settings.
        """
        min_len = self.var_min_length.get()
        # Ensure minimum length is at least 1
        if min_len < MIN_LENGTH_SPINBOX_MIN:
            min_len = MIN_LENGTH_SPINBOX_MIN
            self