import logging
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional

from game_logic import MastermindGame

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CODE_LENGTH = 4
DEFAULT_MAX_ATTEMPTS = 10
AVAILABLE_CODE_LENGTHS = [3, 4, 5, 6]
AVAILABLE_ATTEMPTS = [6, 8, 10, 12]
SYMBOL_SET_COLORS = "Colors"
SYMBOL_SET_DIGITS = "Digits"
WINDOW_TITLE = "Mastermind"
FONT_TITLE = ("Arial", 18, "bold")
FONT_SUBTITLE = ("Arial", 12, "bold")
HISTORY_HEIGHT = 20
HISTORY_WIDTH = 70
PADDING_STANDARD = 10
PADDING_SMALL = 6
PADDING_TINY = 4
PADDING_ZERO = 0


class MastermindGUI:
    """
    Tkinter GUI wrapper for the Mastermind game.
    
    Provides an interactive interface to play Mastermind with customizable settings,
    guess submission, and game history tracking.
    """

    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize the GUI and prepare for a new game.
        
        Args:
            root: The root Tkinter window.
        """
        self.root = root
        self.game = MastermindGame()

        # UI state holders
        self.guess_vars: List[tk.StringVar] = []
        self.guess_menus: List[tk.OptionMenu] = []
        self.pos_labels: List[tk.Label] = []

        # Settings variables
        self.var_code_length = tk.IntVar(value=self.game.code_length)
        self.var_attempts = tk.IntVar(value=self.game.max_attempts)
        self.var_allow_dups = tk.BooleanVar(value=self.game.allow_duplicates)
        self.var_symbol_set = tk.StringVar(value=SYMBOL_SET_COLORS)
        self.var_seed = tk.StringVar(value="")

        # UI frames
        self.header_frame = tk.Frame(self.root, padx=PADDING_STANDARD, pady=PADDING_STANDARD)
        self.settings_frame = tk.Frame(self.root, padx=PADDING_STANDARD, pady=PADDING_SMALL)
        self.guess_frame = tk.Frame(self.root, padx=PADDING_STANDARD, pady=PADDING_STANDARD)
        self.controls_frame = tk.Frame(self.root, padx=PADDING_STANDARD, pady=PADDING_STANDARD)
        self.history_frame = tk.Frame(self.root, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

        # History display
        self.history_listbox = tk.Listbox(self.history_frame, height=HISTORY_HEIGHT, width=HISTORY_WIDTH)
        self.scrollbar = tk.Scrollbar(self.history_frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
        self.history_listbox.config(yscrollcommand=self.scrollbar.set)

        # Header labels
        self.title_label = tk.Label(self.header_frame, text=WINDOW_TITLE, font=FONT_TITLE)
        self.subtitle_label = tk.Label(
            self.header_frame,
            text=(
                "Guess the hidden code of symbols.\n"
                "Feedback: Exact = right symbol & position, Partial = right symbol wrong position."
            ),
            wraplength=600,
            justify="left",
        )

        # Settings controls
        self.settings_title = tk.Label(self.settings_frame, text="Settings:", font=FONT_SUBTITLE)
        self.lbl_len = tk.Label(self.settings_frame, text="Code length:")
        self.opt_len = tk.OptionMenu(self.settings_frame, self.var_code_length, *AVAILABLE_CODE_LENGTHS)
        self.lbl_attempts = tk.Label(self.settings_frame, text="Attempts:")
        self.opt_attempts = tk.OptionMenu(self.settings_frame, self.var_attempts, *AVAILABLE_ATTEMPTS)
        self.chk_dups = tk.Checkbutton(self.settings_frame, text="Allow duplicates", variable=self.var_allow_dups)
        self.lbl_symbols = tk.Label(self.settings_frame, text="Symbol set:")
        self.opt_symbols = tk.OptionMenu(self.settings_frame, self.var_symbol_set, SYMBOL_SET_COLORS, SYMBOL_SET_DIGITS)
        self.lbl_seed = tk.Label(self.settings_frame, text="Seed (optional):")
        self.ent_seed = tk.Entry(self.settings_frame, textvariable=self.var_seed, width=10)

        # Control buttons and status
        self.attempts_label = tk.Label(self.controls_frame, text="", font=FONT_SUBTITLE)
        self.submit_btn = tk.Button(self.controls_frame, text="Submit Guess", command=self._on_submit_guess)
        self.new_game_btn = tk.Button(self.controls_frame, text="New Game", command=self._on_new_game_click)

        self._build_ui()
        self._new_game_init()

        # Keyboard shortcuts
        self.root.bind("<Return>", self._on_submit_guess_event)
        self.root.bind("<Control-n>", self._on_new_game_event)

        logger.info("Mastermind GUI initialized successfully")

    def _build_ui(self) -> None:
        """
        Build and layout all static UI components.
        """
        self._build_header()
        self._build_settings()
        self._build_guess_section()
        self._build_controls()
        self._build_history()

    def _build_header(self) -> None:
        """
        Build the header section with title and instructions.
        """
        self.header_frame.pack(fill="x")
        self.title_label.pack(anchor="w")
        self.subtitle_label.pack(anchor="w", pady=(PADDING_TINY, PADDING_ZERO))

    def _build_settings(self) -> None:
        """
        Build the settings section with configuration options.
        """
        self.settings_frame.pack(fill="x", pady=(PADDING_SMALL, PADDING_ZERO))
        self.settings_title.grid(row=0, column=0, sticky="w", padx=(PADDING_ZERO, PADDING_STANDARD))

        self.lbl_len.grid(row=0, column=1, sticky="e")
        self.opt_len.grid(row=0, column=2, sticky="w", padx=(PADDING_TINY, 12))

        self.lbl_attempts.grid(row=0, column=3, sticky="e")
        self.opt_attempts.grid(row=0, column=4, sticky="w", padx=(PADDING_TINY, 12))

        self.chk_dups.grid(row=0, column=5, sticky="w", padx=(PADDING_TINY, 12))

        self.lbl_symbols.grid(row=1, column=1, sticky="e", pady=(PADDING_SMALL, PADDING_ZERO))
        self.opt_symbols.grid(row=1, column=2, sticky="w", padx=(PADDING_TINY, 12), pady=(PADDING_SMALL, PADDING_ZERO))

        self.lbl_seed.grid(row=1, column=3, sticky="e", pady=(PADDING_SMALL, PADDING_ZERO))
        self.ent_seed.grid(row=1, column=4, sticky="w", padx=(PADDING_TINY, 12), pady=(PADDING_SMALL, PADDING_ZERO))

    def _build_guess_section(self) -> None:
        """
        Build the guess input section header.
        """
        guess_title = tk.Label(self.guess_frame, text="Your Guess:", font=FONT_SUBTITLE)
        guess_title.grid(row=0, column=0, sticky="w", pady=(PADDING_ZERO, PADDING_SMALL))
        self.guess_frame.pack(fill="x")

    def _build_controls(self) -> None:
        """
        Build the control buttons and status display section.
        """
        self.controls_frame.pack(fill="x", pady=(PADDING_SMALL, PADDING_ZERO))
        self.submit_btn.grid(row=0, column=0, padx=(PADDING_ZERO, PADDING_SMALL))
        self.new_game_btn.grid(row=0, column=1, padx=(PADDING_ZERO, PADDING_SMALL))
        self.attempts_label.grid(row=0, column=2, padx=(12, PADDING_ZERO))

    def _build_history(self) -> None:
        """
        Build the game history display section.
        """
        history_title = tk.Label(self.history_frame, text="History:", font=FONT_SUBTITLE)
        history_title.pack(anchor="w")
        self.history_listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.history_frame.pack(fill="both", expand=True, pady=(PADDING_SMALL, PADDING_ZERO))

    @staticmethod
    def _color_symbols() -> List[str]:
        """
        Return a set of color names recognized by Tkinter.
        
        Returns:
            List of color name strings.
        """
        return [
            "red", "green", "blue", "yellow",
            "orange", "purple", "cyan", "magenta",
        ]

    @staticmethod
    def _digit_symbols() -> List[str]:
        """
        Return a set of digit symbols as strings.
        
        Returns:
            List of digit strings from "0" to "9".
        """
        return [str(digit) for digit in range(10)]

    def _symbols_from_setting(self) -> List[str]:
        """
        Determine the symbol set based on current settings.
        
        Returns:
            List of available symbols for the current setting.
        """
        symbol_set = self.var_symbol_set.get()
        if symbol_set == SYMBOL_SET_DIGITS:
            return self._digit_symbols()
        return self._color_symbols()

    def _parse_seed(self) -> Optional[int]:
        """
        Parse the optional seed field from user input.
        
        Returns:
            Integer seed value or None if field is empty.
            
        Raises:
            Shows error dialog if seed is not a valid integer.
        """
        raw_seed = self.var_seed.get().strip()
        if raw_seed == "":
            return None
        try:
            return int(raw_seed)
        except ValueError:
            messagebox.showerror("Invalid Seed", "Seed must be an integer or left blank.")
            return None

    def _validate_game_settings(self, code_length: int, symbols: List[str], allow_duplicates: bool) -> bool:
        """
        Validate that game settings are compatible.
        
        Args:
            code_length: Desired code length.
            symbols: Available symbols.
            allow_duplicates: Whether duplicates are allowed.
            
        Returns:
            True if settings are valid, False otherwise.
        """
        if not allow_duplicates and code_length > len(symbols):
            messagebox.showerror(
                "Invalid Settings",
                "Code length cannot exceed number of available symbols when duplicates are not allowed.\n"
                "Either enable duplicates, reduce code length, or choose a symbol set with more symbols."
            )
            return False
        return True

    def _clear_guess_inputs(self) -> None:
        """
        Destroy and clear all guess input widgets.
        """
        for menu in self.guess_menus:
            menu.destroy()
        self.guess_menus.clear()

        for label in self.pos_labels:
            label.destroy()
        self.pos_labels.clear()

    def _create_guess_inputs(self) -> None:
        """
        Create dropdown menus and position labels for guess input.
        """
        default_symbol = self.game.colors[0]
        self.guess_vars = [tk.StringVar(value=default_symbol) for _ in range(self.game.code_length)]

        for position, var in enumerate(self.guess_vars, start=1):
            # Create dropdown menu for this position
            option_menu = tk.OptionMenu(self.guess_frame, var, *self.game.colors)
            option_menu.grid(row=1, column=position, padx=PADDING_TINY, pady=PADDING_TINY)
            self.guess_menus.append(option_menu)

            # Create position label below dropdown
            position_label = tk.Label(self.guess_frame, text=f"Pos {position}")
            position_label.grid(row=2, column=position, padx=PADDING_TINY, pady=(PADDING_ZERO, PADDING_TINY))
            self.pos_labels.append(position_label)

    def _new_game_init(self) -> None:
        """
        Initialize a new game with current settings and reset all UI components.
        """
        # Read current settings
        code_length = int(self.var_code_length.get())
        max_attempts = int(self.var_attempts.get())
        allow_duplicates = bool(self.var_allow_dups.get())
        symbols = self._symbols_from_setting()
        seed = self._parse_seed()

        # Validate settings
        if not self._validate_game_settings(code_length, symbols, allow_duplicates):
            return

        # Create new game instance
        self.game = MastermindGame(
            code_length=code_length,
            colors=symbols,
            max_attempts=max_attempts,
            allow_duplicates=allow_duplicates,
            seed=seed,
        )

        logger.info(f"New game initialized: length={code_length}, attempts={max_attempts}, duplicates={allow_duplicates}")

        # Reset UI components
        self._clear_guess_inputs()
        self._create_guess_inputs()
        self.history_listbox.delete(0, tk.END)

        # Update status display
        self._update_attempts_label()
        self._set_submit_enabled(True)

    def _set_submit_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the Submit Guess button.
        
        Args:
            enabled: True to enable, False to disable.
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        self.submit_btn.config(state=state)

    def _update_attempts_label(self) -> None:
        """
        Update the attempts label to show remaining attempts.
        """
        remaining = self.game.remaining_attempts()
        total = self.game.max_attempts
        self.attempts_label.config(text=f"Attempts left: {remaining} / {total}")

    def _on_new_game_click(self) -> None:
        """
        Handle New Game button click.
        """
        self._new_game_init()

    def _on_new_game_event(self, event: tk.Event) -> None:
        """
        Handle New Game keyboard shortcut (Ctrl+N).
        
        Args:
            event: The keyboard event.
        """
        self._on_new_game_click()

    def _on_submit_guess_event(self, event: tk.Event) -> None:
        """
        Handle Submit Guess keyboard shortcut (Enter).
        
        Args:
            event: The keyboard event.
        """
        if self.submit_btn.cget("state") == tk.NORMAL:
            self._on_submit_guess()

    def _record_guess_in_history(self, guess: List[