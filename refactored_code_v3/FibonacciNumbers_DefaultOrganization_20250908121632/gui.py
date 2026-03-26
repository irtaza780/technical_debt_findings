import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List

from fibonacci import (
    generate_fibonacci_up_to,
    parse_limit,
    format_sequence,
    sequence_stats,
)

# Constants
DEFAULT_WINDOW_WIDTH = 640
DEFAULT_WINDOW_HEIGHT = 420
MIN_WINDOW_WIDTH = 520
MIN_WINDOW_HEIGHT = 360
DEFAULT_LIMIT_VALUE = "1000"
DEFAULT_FONT_FAMILY = "Courier New"
DEFAULT_FONT_SIZE = 11
DEFAULT_FILENAME = "fibonacci.txt"
STATUS_COLOR_ERROR = "#b00020"
STATUS_COLOR_NORMAL = "#444"
PADDING_STANDARD = (10, 10, 10, 5)
PADDING_SMALL = (10, 5, 10, 5)
PADDING_BOTTOM = (10, 5, 10, 10)

logger = logging.getLogger(__name__)


class FibonacciApp:
    """Tkinter GUI application for generating and managing Fibonacci sequences."""

    def __init__(self, master: tk.Tk) -> None:
        """
        Initialize the Fibonacci GUI application.

        Args:
            master: The root Tkinter window.
        """
        self.master = master
        self._configure_window()
        self._apply_styling()
        self._create_top_frame()
        self._create_middle_frame()
        self._create_bottom_frame()
        self._bind_keyboard_shortcuts()

    def _configure_window(self) -> None:
        """Configure the main window properties and grid layout."""
        self.master.title("Fibonacci Generator")
        self.master.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        self.master.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # Configure grid for responsiveness
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)

    def _apply_styling(self) -> None:
        """Apply theme styling to the application."""
        style = ttk.Style(self.master)
        try:
            # Use a platform-appropriate theme if available
            style.theme_use("clam")
        except tk.TclError:
            logger.debug("Clam theme not available, using default theme")

    def _create_top_frame(self) -> None:
        """Create and configure the top input frame."""
        top_frame = ttk.Frame(self.master, padding=PADDING_STANDARD)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.columnconfigure(1, weight=1)

        # Label for input field
        label = ttk.Label(top_frame, text="Generate Fibonacci numbers up to:")
        label.grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")

        # Entry field for limit value
        self.var_limit = tk.StringVar()
        self.entry_limit = ttk.Entry(top_frame, textvariable=self.var_limit)
        self.entry_limit.grid(row=0, column=1, padx=(0, 8), pady=4, sticky="ew")
        self.entry_limit.insert(0, DEFAULT_LIMIT_VALUE)
        self.entry_limit.focus()

        # Generate button
        btn_generate = ttk.Button(top_frame, text="Generate", command=self.on_generate)
        btn_generate.grid(row=0, column=2, padx=(0, 0), pady=4)

    def _create_middle_frame(self) -> None:
        """Create and configure the middle output frame with listbox."""
        mid_frame = ttk.Frame(self.master, padding=PADDING_SMALL)
        mid_frame.grid(row=1, column=0, sticky="nsew")
        mid_frame.rowconfigure(0, weight=1)
        mid_frame.columnconfigure(0, weight=1)

        # Listbox for displaying Fibonacci numbers
        self.listbox = tk.Listbox(
            mid_frame,
            font=(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE),
            activestyle="none",
            exportselection=False,
        )
        yscroll = ttk.Scrollbar(
            mid_frame, orient="vertical", command=self.listbox.yview
        )
        self.listbox.configure(yscrollcommand=yscroll.set)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

    def _create_bottom_frame(self) -> None:
        """Create and configure the bottom action and status frame."""
        bottom_frame = ttk.Frame(self.master, padding=PADDING_BOTTOM)
        bottom_frame.grid(row=2, column=0, sticky="ew")
        bottom_frame.columnconfigure(0, weight=1)

        # Action buttons frame
        btns_frame = ttk.Frame(bottom_frame)
        btns_frame.grid(row=0, column=0, sticky="w")

        btn_clear = ttk.Button(btns_frame, text="Clear", command=self.on_clear)
        btn_clear.grid(row=0, column=0, padx=(0, 8))

        btn_copy = ttk.Button(btns_frame, text="Copy", command=self.on_copy)
        btn_copy.grid(row=0, column=1, padx=(0, 8))

        btn_save = ttk.Button(btns_frame, text="Save...", command=self.on_save)
        btn_save.grid(row=0, column=2, padx=(0, 8))

        # Status label
        self.status_var = tk.StringVar(value="Ready.")
        self.status_label = ttk.Label(
            bottom_frame, textvariable=self.status_var, foreground=STATUS_COLOR_NORMAL
        )
        self.status_label.grid(row=1, column=0, sticky="w", pady=(6, 0))

    def _bind_keyboard_shortcuts(self) -> None:
        """Bind keyboard shortcuts to their respective handlers."""
        self.master.bind("<Return>", lambda e: self.on_generate())
        self.master.bind("<Control-s>", lambda e: self.on_save())
        # Bind Ctrl+C only when listbox has focus to avoid overriding Entry copy
        self.listbox.bind("<Control-c>", self._on_copy_hotkey)

    def on_generate(self) -> None:
        """
        Handle Generate button click.

        Validates the input limit, generates the Fibonacci sequence,
        and updates the display with results and statistics.
        """
        text = self.var_limit.get()
        try:
            limit = parse_limit(text)
        except ValueError as e:
            error_msg = str(e)
            messagebox.showerror("Invalid input", error_msg, parent=self.master)
            self._set_status(error_msg, error=True)
            logger.warning(f"Invalid input: {error_msg}")
            return

        numbers = generate_fibonacci_up_to(limit)
        self._update_output(numbers)
        stats = sequence_stats(numbers)
        status_msg = (
            f"Generated {stats['count']} numbers up to {limit}. "
            f"Max={stats['max']}, Sum={stats['sum']}."
        )
        self._set_status(status_msg)
        logger.info(f"Generated Fibonacci sequence: {status_msg}")

    def on_clear(self) -> None:
        """Clear all input and output widgets."""
        self.var_limit.set("")
        self.listbox.delete(0, tk.END)
        self._set_status("Cleared. Enter a non-negative integer and press Generate.")
        logger.info("Cleared input and output")

    def on_copy(self) -> None:
        """
        Copy the generated Fibonacci sequence to the clipboard.

        Displays an error message if no sequence has been generated.
        """
        items = self.listbox.get(0, tk.END)
        if not items:
            self._set_status(
                "Nothing to copy. Generate a sequence first.", error=True
            )
            logger.warning("Copy attempted with empty sequence")
            return

        # Convert listbox items to integers and format as string
        sequence_numbers = [int(x) for x in items]
        joined = format_sequence(sequence_numbers)

        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(joined)
            self._set_status("Sequence copied to clipboard.")
            logger.info("Sequence copied to clipboard")
        except tk.TclError as e:
            self._set_status("Failed to access clipboard.", error=True)
            logger.error(f"Clipboard error: {e}")

    def on_save(self) -> None:
        """
        Save the generated Fibonacci sequence to a text file.

        Prompts the user for a file location and writes the sequence
        with optional header information.
        """
        items = self.listbox.get(0, tk.END)
        if not items:
            self._set_status("Nothing to save. Generate a sequence first.", error=True)
            logger.warning("Save attempted with empty sequence")
            return

        # Attempt to parse the limit value for the file header
        limit_val = self._try_parse_limit()

        filepath = filedialog.asksaveasfilename(
            parent=self.master,
            title="Save Fibonacci Sequence",
            defaultextension=".txt",
            initialfile=DEFAULT_FILENAME,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not filepath:
            logger.debug("Save dialog cancelled by user")
            return

        # Build file content
        sequence_numbers = [int(x) for x in items]
        content = self._build_file_content(sequence_numbers, limit_val)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self._set_status(f"Saved to {filepath}.")
            logger.info(f"Sequence saved to {filepath}")
        except OSError as e:
            messagebox.showerror("Save Error", str(e), parent=self.master)
            self._set_status("Failed to save file.", error=True)
            logger.error(f"Failed to save file: {e}")

    def _try_parse_limit(self) -> int | None:
        """
        Attempt to parse the limit value from the input field.

        Returns:
            The parsed limit value, or None if parsing fails.
        """
        limit_text = self.var_limit.get().strip()
        try:
            return parse_limit(limit_text)
        except ValueError:
            logger.debug("Could not parse limit value for file header")
            return None

    def _build_file_content(self, sequence: List[int], limit: int | None) -> str:
        """
        Build the content string for saving to a file.

        Args:
            sequence: The list of Fibonacci numbers.
            limit: The limit value used to generate the sequence, or None.

        Returns:
            A formatted string ready to be written to a file.
        """
        content_lines = []
        if limit is not None:
            content_lines.append(f"Fibonacci numbers up to {limit}:")
        else:
            content_lines.append("Fibonacci numbers:")
        content_lines.append(format_sequence(sequence))
        return "\n".join(content_lines)

    def _update_output(self, numbers: List[int]) -> None:
        """
        Render the Fibonacci numbers in the listbox.

        Args:
            numbers: The list of Fibonacci numbers to display.
        """
        self.listbox.delete(0, tk.END)
        for num in numbers:
            self.listbox.insert(tk.END, str(num))

    def _set_status(self, text: str, error: bool = False) -> None:
        """
        Update the status label with optional error styling.

        Args:
            text: The status message to display.
            error: If True, apply error styling (red color).
        """
        self.status_var.set(text)
        color = STATUS_COLOR_ERROR if error else STATUS_COLOR_NORMAL
        self.status_label.configure(foreground=color)

    def _on_copy_hotkey(self, event) -> str:
        """
        Handle Ctrl+C keyboard shortcut when listbox has focus.

        Args:
            event: The keyboard event object.

        Returns:
            "break" to prevent event propagation.
        """
        self.on_copy()
        return "break"