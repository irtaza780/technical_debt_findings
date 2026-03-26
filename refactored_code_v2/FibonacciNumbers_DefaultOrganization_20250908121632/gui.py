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
    """Tkinter GUI application for generating Fibonacci numbers."""

    def __init__(self, master: tk.Tk) -> None:
        """
        Initialize the GUI components and layout.

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
        """Create and configure the top frame with input controls."""
        top_frame = ttk.Frame(self.master, padding=PADDING_STANDARD)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.columnconfigure(1, weight=1)

        label = ttk.Label(top_frame, text="Generate Fibonacci numbers up to:")
        label.grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")

        self.var_limit = tk.StringVar()
        self.entry_limit = ttk.Entry(top_frame, textvariable=self.var_limit)
        self.entry_limit.grid(row=0, column=1, padx=(0, 8), pady=4, sticky="ew")
        self.entry_limit.insert(0, DEFAULT_LIMIT_VALUE)
        self.entry_limit.focus()

        btn_generate = ttk.Button(top_frame, text="Generate", command=self.on_generate)
        btn_generate.grid(row=0, column=2, padx=(0, 0), pady=4)

    def _create_middle_frame(self) -> None:
        """Create and configure the middle frame with output listbox."""
        mid_frame = ttk.Frame(self.master, padding=PADDING_SMALL)
        mid_frame.grid(row=1, column=0, sticky="nsew")
        mid_frame.rowconfigure(0, weight=1)
        mid_frame.columnconfigure(0, weight=1)

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
        """Create and configure the bottom frame with action buttons and status."""
        bottom_frame = ttk.Frame(self.master, padding=PADDING_BOTTOM)
        bottom_frame.grid(row=2, column=0, sticky="ew")
        bottom_frame.columnconfigure(0, weight=1)

        self._create_action_buttons(bottom_frame)
        self._create_status_label(bottom_frame)

    def _create_action_buttons(self, parent: ttk.Frame) -> None:
        """
        Create action buttons in the given parent frame.

        Args:
            parent: The parent frame to contain the buttons.
        """
        btns_frame = ttk.Frame(parent)
        btns_frame.grid(row=0, column=0, sticky="w")

        btn_clear = ttk.Button(btns_frame, text="Clear", command=self.on_clear)
        btn_clear.grid(row=0, column=0, padx=(0, 8))

        btn_copy = ttk.Button(btns_frame, text="Copy", command=self.on_copy)
        btn_copy.grid(row=0, column=1, padx=(0, 8))

        btn_save = ttk.Button(btns_frame, text="Save...", command=self.on_save)
        btn_save.grid(row=0, column=2, padx=(0, 8))

    def _create_status_label(self, parent: ttk.Frame) -> None:
        """
        Create the status label in the given parent frame.

        Args:
            parent: The parent frame to contain the status label.
        """
        self.status_var = tk.StringVar(value="Ready.")
        self.status_label = ttk.Label(
            parent, textvariable=self.status_var, foreground=STATUS_COLOR_NORMAL
        )
        self.status_label.grid(row=1, column=0, sticky="w", pady=(6, 0))

    def _bind_keyboard_shortcuts(self) -> None:
        """Bind keyboard shortcuts to their respective handlers."""
        self.master.bind("<Return>", lambda e: self.on_generate())
        self.master.bind("<Control-s>", lambda e: self.on_save())
        # Bind Ctrl+C only when the listbox has focus to avoid overriding Entry copy
        self.listbox.bind("<Control-c>", self._on_copy_hotkey)

    def on_generate(self) -> None:
        """
        Handle Generate button click: validate input and compute sequence.

        Displays error message if input is invalid.
        """
        text = self.var_limit.get()
        try:
            limit = parse_limit(text)
        except ValueError as error:
            messagebox.showerror("Invalid input", str(error), parent=self.master)
            self._set_status(str(error), error=True)
            logger.warning(f"Invalid input: {error}")
            return

        numbers = generate_fibonacci_up_to(limit)
        self._update_output(numbers)
        stats = sequence_stats(numbers)
        status_message = (
            f"Generated {stats['count']} numbers up to {limit}. "
            f"Max={stats['max']}, Sum={stats['sum']}."
        )
        self._set_status(status_message)
        logger.info(f"Generated Fibonacci sequence: {status_message}")

    def on_clear(self) -> None:
        """Clear input and output widgets."""
        self.var_limit.set("")
        self.listbox.delete(0, tk.END)
        self._set_status("Cleared. Enter a non-negative integer and press Generate.")
        logger.info("Cleared input and output")

    def on_copy(self) -> None:
        """
        Copy the generated sequence to the clipboard.

        Displays error message if no sequence has been generated.
        """
        items = self.listbox.get(0, tk.END)
        if not items:
            self._set_status(
                "Nothing to copy. Generate a sequence first.", error=True
            )
            logger.warning("Copy attempted with empty sequence")
            return

        # Convert listbox items to integers and format for clipboard
        sequence = [int(item) for item in items]
        joined = format_sequence(sequence)
        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(joined)
            self._set_status("Sequence copied to clipboard.")
            logger.info("Sequence copied to clipboard")
        except tk.TclError as error:
            self._set_status("Failed to access clipboard.", error=True)
            logger.error(f"Clipboard access failed: {error}")

    def on_save(self) -> None:
        """
        Save the generated sequence to a text file.

        Displays error message if no sequence has been generated or save fails.
        """
        items = self.listbox.get(0, tk.END)
        if not items:
            self._set_status("Nothing to save. Generate a sequence first.", error=True)
            logger.warning("Save attempted with empty sequence")
            return

        # Determine limit from input (best effort)
        limit_text = self.var_limit.get().strip()
        limit_val = self._try_parse_limit(limit_text)

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

        sequence = [int(item) for item in items]
        content = self._build_save_content(sequence, limit_val)

        try:
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(content)
            self._set_status(f"Saved to {filepath}.")
            logger.info(f"Sequence saved to {filepath}")
        except OSError as error:
            messagebox.showerror("Save Error", str(error), parent=self.master)
            self._set_status("Failed to save file.", error=True)
            logger.error(f"Failed to save file: {error}")

    def _try_parse_limit(self, limit_text: str) -> int | None:
        """
        Attempt to parse the limit value from text.

        Args:
            limit_text: The text to parse as a limit value.

        Returns:
            The parsed limit value, or None if parsing fails.
        """
        try:
            return parse_limit(limit_text)
        except ValueError:
            logger.debug(f"Could not parse limit from text: {limit_text}")
            return None

    def _build_save_content(self, sequence: List[int], limit_val: int | None) -> str:
        """
        Build the content string for saving to file.

        Args:
            sequence: The Fibonacci sequence to save.
            limit_val: The limit value used to generate the sequence, or None.

        Returns:
            The formatted content string.
        """
        content_lines = []
        if limit_val is not None:
            content_lines.append(f"Fibonacci numbers up to {limit_val}:")
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
            error: If True, apply error styling to the status label.
        """
        self.status_var.set(text)
        color = STATUS_COLOR_ERROR if error else STATUS_COLOR_NORMAL
        self.status_label.configure(foreground=color)

    def _on_copy_hotkey(self, event) -> str:
        """
        Handle Ctrl+C when the listbox has focus.

        Args:
            event: The keyboard event that triggered this handler.

        Returns:
            "break" to prevent event propagation.
        """
        self.on_copy()
        return "break"