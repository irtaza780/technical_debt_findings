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
PADDING_POSITION = 5


class MastermindGUI:
    """
    Tkinter GUI wrapper for the Mastermind game.
    
    Provides an interactive interface to play Mastermind with customizable settings,
    guess submission, and game history tracking.
    """

    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize the GUI and set up the game.
        
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

        # Initialize UI frames
        self._initialize_frames()
        self._initialize_widgets()
        self._build_ui()
        self._new_game_init()

        # Bind keyboard shortcuts
        self.root.bind("<Return>", self._on_submit_guess_event)
        self.root.bind("<Control-n>", self._on_new_game_event)

        logger.info("Mastermind GUI initialized successfully")

    def _initialize_frames(self) -> None:
        """
        Create and initialize all frame containers.
        """
        self.header_frame = tk.Frame(self.root, padx=PADDING_STANDARD, pady=PADDING_STANDARD)
        self.settings_frame = tk.Frame(self.root, padx=PADDING_STANDARD, pady=PADDING_SMALL)
        self.guess_frame = tk.Frame(self.root, padx=PADDING_STANDARD, pady=PADDING_STANDARD)
        self.controls_frame = tk.Frame(self.root, padx=PADDING_STANDARD, pady=PADDING_STANDARD)
        self.history_frame = tk.Frame(self.root, padx=PADDING_STANDARD, pady=PADDING_STANDARD)

    def _initialize_widgets(self) -> None:
        """
        Create all static widgets.
        """
        # Header widgets
        self.title_label = tk.Label(
            self.header_frame,
            text=WINDOW_TITLE,
            font=FONT_TITLE
        )
        self.subtitle_label = tk.Label(
            self.header_frame,
            text=(
                "Guess the hidden code of symbols.\n"
                "Feedback: Exact = right symbol & position, Partial = right symbol wrong position."
            ),
            wraplength=600,
            justify="left",
        )

        # Settings widgets
        self.settings_title = tk.Label(
            self.settings_frame,
            text="Settings:",
            font=FONT_SUBTITLE
        )
        self.lbl_len = tk.Label(self.settings_frame, text="Code length:")
        self.opt_len = tk.OptionMenu(
            self.settings_frame,
            self.var_code_length,
            *AVAILABLE_CODE_LENGTHS
        )
        self.lbl_attempts = tk.Label(self.settings_frame, text="Attempts:")
        self.opt_attempts = tk.OptionMenu(
            self.settings_frame,
            self.var_attempts,
            *AVAILABLE_ATTEMPTS
        )
        self.chk_dups = tk.Checkbutton(
            self.settings_frame,
            text="Allow duplicates",
            variable=self.var_allow_dups
        )
        self.lbl_symbols = tk.Label(self.settings_frame, text="Symbol set:")
        self.opt_symbols = tk.OptionMenu(
            self.settings_frame,
            self.var_symbol_set,
            SYMBOL_SET_COLORS,
            SYMBOL_SET_DIGITS
        )
        self.lbl_seed = tk.Label(self.settings_frame, text="Seed (optional):")
        self.ent_seed = tk.Entry(self.settings_frame, textvariable=self.var_seed, width=10)

        # Controls widgets
        self.attempts_label = tk.Label(self.controls_frame, text="", font=FONT_SUBTITLE)
        self.submit_btn = tk.Button(
            self.controls_frame,
            text="Submit Guess",
            command=self._on_submit_guess
        )
        self.new_game_btn = tk.Button(
            self.controls_frame,
            text="New Game",
            command=self._on_new_game_click
        )

        # History widgets
        self.history_listbox = tk.Listbox(
            self.history_frame,
            height=HISTORY_HEIGHT,
            width=HISTORY_WIDTH
        )
        self.scrollbar = tk.Scrollbar(
            self.history_frame,
            orient=tk.VERTICAL,
            command=self.history_listbox.yview
        )
        self.history_listbox.config(yscrollcommand=self.scrollbar.set)

    def _build_ui(self) -> None:
        """
        Build and layout all UI components.
        """
        self._layout_header()
        self._layout_settings()
        self._layout_controls()
        self._layout_history()

    def _layout_header(self) -> None:
        """
        Layout header section with title and subtitle.
        """
        self.header_frame.pack(fill="x")
        self.title_label.pack(anchor="w")
        self.subtitle_label.pack(anchor="w", pady=(PADDING_TINY, 0))

    def _layout_settings(self) -> None:
        """
        Layout settings section with configuration options.
        """
        self.settings_frame.pack(fill="x", pady=(PADDING_SMALL, 0))
        self.settings_title.grid(row=0, column=0, sticky="w", padx=(0, PADDING_STANDARD))

        # Row 0: Code length, attempts, duplicates
        self.lbl_len.grid(row=0, column=1, sticky="e")
        self.opt_len.grid(row=0, column=2, sticky="w", padx=(PADDING_TINY, PADDING_STANDARD))

        self.lbl_attempts.grid(row=0, column=3, sticky="e")
        self.opt_attempts.grid(row=0, column=4, sticky="w", padx=(PADDING_TINY, PADDING_STANDARD))

        self.chk_dups.grid(row=0, column=5, sticky="w", padx=(PADDING_TINY, PADDING_STANDARD))

        # Row 1: Symbol set, seed
        self.lbl_symbols.grid(row=1, column=1, sticky="e", pady=(PADDING_SMALL, 0))
        self.opt_symbols.grid(
            row=1,
            column=2,
            sticky="w",
            padx=(PADDING_TINY, PADDING_STANDARD),
            pady=(PADDING_SMALL, 0)
        )

        self.lbl_seed.grid(row=1, column=3, sticky="e", pady=(PADDING_SMALL, 0))
        self.ent_seed.grid(
            row=1,
            column=4,
            sticky="w",
            padx=(PADDING_TINY, PADDING_STANDARD),
            pady=(PADDING_SMALL, 0)
        )

    def _layout_controls(self) -> None:
        """
        Layout controls section with submit and new game buttons.
        """
        self.controls_frame.pack(fill="x", pady=(PADDING_SMALL, 0))
        self.submit_btn.grid(row=0, column=0, padx=(0, PADDING_SMALL))
        self.new_game_btn.grid(row=0, column=1, padx=(0, PADDING_SMALL))
        self.attempts_label.grid(row=0, column=2, padx=(PADDING_STANDARD, 0))

    def _layout_history(self) -> None:
        """
        Layout history section with listbox and scrollbar.
        """
        history_title = tk.Label(
            self.history_frame,
            text="History:",
            font=FONT_SUBTITLE
        )
        history_title.pack(anchor="w")
        self.history_listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.history_frame.pack(fill="both", expand=True, pady=(PADDING_SMALL, 0))

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
        return [str(d) for d in range(10)]

    def _symbols_from_setting(self) -> List[str]:
        """
        Determine the symbol set based on current settings.
        
        Returns:
            List of available symbols for the current setting.
        """
        symset = self.var_symbol_set.get()
        if symset == SYMBOL_SET_DIGITS:
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
        raw = self.var_seed.get().strip()
        if raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            messagebox.showerror("Invalid Seed", "Seed must be an integer or left blank.")
            return None

    def _validate_game_settings(self, code_len: int, allow_dups: bool, symbols: List[str]) -> bool:
        """
        Validate that game settings are compatible.
        
        Args:
            code_len: The desired code length.
            allow_dups: Whether duplicates are allowed.
            symbols: The available symbols.
            
        Returns:
            True if settings are valid, False otherwise.
        """
        if not allow_dups and code_len > len(symbols):
            messagebox.showerror(
                "Invalid Settings",
                "Code length cannot exceed number of available symbols when duplicates are not allowed.\n"
                "Either enable duplicates, reduce code length, or choose a symbol set with more symbols."
            )
            return False
        return True

    def _create_new_game(self, code_len: int, attempts: int, allow_dups: bool,
                        symbols: List[str], seed: Optional[int]) -> None:
        """
        Create a new game instance with the specified settings.
        
        Args:
            code_len: Code length for the game.
            attempts: Maximum number of attempts.
            allow_dups: Whether duplicates are allowed.
            symbols: Available symbols for the game.
            seed: Optional seed for reproducibility.
        """
        self.game = MastermindGame(
            code_length=code_len,
            colors=symbols,
            max_attempts=attempts,
            allow_duplicates=allow_dups,
            seed=seed,
        )
        logger.info(f"New game created: length={code_len}, attempts={attempts}, "
                   f"duplicates={allow_dups}, seed={seed}")

    def _rebuild_guess_inputs(self) -> None:
        """
        Rebuild the guess input dropdowns and position labels for the current code length.
        """
        # Clear existing widgets
        for menu in self.guess_menus:
            menu.destroy()
        self.guess_menus.clear()
        for lbl in self.pos_labels:
            lbl.destroy()
        self.pos_labels.clear()

        # Create new widgets
        default_value = self.game.colors[0]
        self.guess_vars = [tk.StringVar(value=default_value) for _ in range(self.game.code_length)]

        for i, var in enumerate(self.guess_vars, start=1):
            om = tk.OptionMenu(self.guess_frame, var, *self.game.colors)
            om.grid(row=1, column=i, padx=PADDING_POSITION, pady=PADDING_POSITION)
            self.guess_menus.append(om)

            pos_lbl = tk.Label(self.guess_frame, text=f"Pos {i}")
            pos_lbl.grid(row=2, column=i, padx=PADDING_POSITION, pady=(0, PADDING_POSITION))
            self.pos_labels.append(pos_lbl)

    def _reset_game_ui(self) -> None:
        """
        Reset UI elements for a new game.
        """
        self.history_listbox.delete(0, tk.END)
        self._update_attempts_label()
        self._set_submit_enabled(True)

    def _new_game_init(self) -> None:
        """
        Initialize a new game with current settings and update UI accordingly.
        """
        code_len = int(self.var_code_length.get())
        attempts = int(self.var_attempts.get())
        allow_dups = bool(self.var_allow_dups.get())
        symbols = self._symbols_from_setting()
        seed = self._parse_seed()

        if not self._validate_game_settings(code_len, allow_dups, symbols):
            return

        self._create_new_game(code_len, attempts, allow_dups, symbols, seed)
        self._rebuild_guess_inputs()
        self._reset_game_ui()

    def _set_submit_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the Submit Guess button.
        
        Args:
            enabled: True to enable, False to disable.
        """
        self.submit_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def _update_attempts_label(self) -> None:
        """
        Update the attempts label to reflect remaining attempts.
        """
        self.attempts_label.config(
            text=f"Attempts left: {self.game.remaining_attempts()} / {self.game.max_attempts}"
        )

    def _on_new_game_click(self) -> None:
        """
        Handle the New Game button click.
        """
        self._new_game_init