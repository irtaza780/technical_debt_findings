import logging
import tkinter as tk
from tkinter import messagebox
from typing import List, Dict

from game import WordleGame, ABSENT, PRESENT, CORRECT
from words import get_daily_word, get_random_word

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# UI Colors inspired by Wordle
COLOR_BG = "#121213"
COLOR_EMPTY = "#d3d6da"
COLOR_TEXT = "#ffffff"
COLOR_CORRECT = "#6aaa64"
COLOR_PRESENT = "#c9b458"
COLOR_ABSENT = "#787c7e"

# Game constants
QWERTY_LAYOUT = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
BOARD_ROWS = 6
WORD_LENGTH = 5
PADDING_STANDARD = 10
PADDING_CELL = 4
PADDING_KEYBOARD = 2
FONT_BOARD = ("Helvetica", 18, "bold")
FONT_STATUS = ("Helvetica", 12)
FONT_KEYBOARD = ("Helvetica", 10, "bold")
CELL_WIDTH = 4
CELL_HEIGHT = 2
ENTRY_WIDTH = 10
ENTRY_FONT = ("Helvetica", 16)
BUTTON_WIDTH = 3
BUTTON_HEIGHT = 1
KEYBOARD_BUTTON_WIDTH = 3

# UI Messages
MSG_INITIAL_STATUS = "Guess the 5-letter word!"
MSG_WIN_TEMPLATE = "Congratulations! You won in {attempts}/6."
MSG_LOSS_TEMPLATE = "Out of tries. The word was {word}."
MSG_ATTEMPTS_TEMPLATE = "Attempts: {attempts}/6"
MSG_WIN_DIALOG = "You guessed the word: {word}"
MSG_LOSS_DIALOG = "The word was: {word}"


class WordleGUI(tk.Tk):
    """
    Tkinter-based GUI for the Wordle game.
    
    Provides a graphical interface with a 6x5 letter grid, keyboard visualization,
    and input handling for playing Wordle.
    """

    def __init__(self, date=None, random_word=False):
        """
        Initialize the Wordle GUI application.
        
        Args:
            date: Optional date string for daily word selection.
            random_word: If True, use a random word; otherwise use daily word.
        """
        super().__init__()
        self.title("Wordle (GUI)")
        self.configure(bg=COLOR_BG)

        # Initialize game with appropriate word selection
        secret = self._select_secret_word(date, random_word)
        self.game = WordleGame(secret_word=secret)

        # UI state
        self.labels: List[List[tk.Label]] = []  # 6x5 grid of letter labels
        self.keyboard_buttons: Dict[str, tk.Button] = {}  # Keyboard button references
        self.status_label: tk.Label = None  # Status message label
        self.entry: tk.Entry = None  # Input entry widget

        # Build UI components
        self._build_board()
        self._build_input()
        self._build_keyboard()
        self.resizable(False, False)
        logger.info("Wordle GUI initialized")

    @staticmethod
    def _select_secret_word(date=None, random_word=False) -> str:
        """
        Select the secret word based on game mode.
        
        Args:
            date: Optional date for daily word selection.
            random_word: If True, select random word; otherwise use daily word.
            
        Returns:
            The selected secret word.
        """
        if random_word:
            word = get_random_word()
            logger.info("Selected random word for game")
        else:
            word = get_daily_word(date=date)
            logger.info(f"Selected daily word for date: {date}")
        return word

    def _build_board(self) -> None:
        """
        Build the main game board with 6x5 grid of letter labels.
        """
        board_frame = tk.Frame(self, bg=COLOR_BG)
        board_frame.grid(row=0, column=0, padx=PADDING_STANDARD, pady=PADDING_STANDARD, columnspan=3)

        # Create grid of labels for letter display
        for row_idx in range(BOARD_ROWS):
            row_labels = []
            for col_idx in range(WORD_LENGTH):
                label = tk.Label(
                    board_frame,
                    text=" ",
                    width=CELL_WIDTH,
                    height=CELL_HEIGHT,
                    font=FONT_BOARD,
                    bg=COLOR_EMPTY,
                    fg="black",
                    relief="groove",
                    bd=2
                )
                label.grid(row=row_idx, column=col_idx, padx=PADDING_CELL, pady=PADDING_CELL)
                row_labels.append(label)
            self.labels.append(row_labels)

        # Create status label
        self.status_label = tk.Label(
            self,
            text=MSG_INITIAL_STATUS,
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            font=FONT_STATUS
        )
        self.status_label.grid(row=1, column=0, padx=PADDING_STANDARD, pady=(0, PADDING_STANDARD), sticky="w")

    def _build_input(self) -> None:
        """
        Build the input frame with entry field and submit button.
        """
        input_frame = tk.Frame(self, bg=COLOR_BG)
        input_frame.grid(row=2, column=0, padx=PADDING_STANDARD, pady=PADDING_STANDARD, sticky="w")

        # Create entry field
        self.entry = tk.Entry(input_frame, width=ENTRY_WIDTH, font=ENTRY_FONT)
        self.entry.grid(row=0, column=0, padx=(0, 8))
        self.entry.bind("<Return>", self._on_submit)

        # Create submit button
        submit_btn = tk.Button(input_frame, text="Submit", command=self._on_submit)
        submit_btn.grid(row=0, column=1)

    def _build_keyboard(self) -> None:
        """
        Build the on-screen QWERTY keyboard with letter buttons.
        """
        kb_frame = tk.Frame(self, bg=COLOR_BG)
        kb_frame.grid(row=3, column=0, padx=PADDING_STANDARD, pady=(0, PADDING_STANDARD))

        # Create keyboard rows
        for row_idx, row_letters in enumerate(QWERTY_LAYOUT):
            row_frame = tk.Frame(kb_frame, bg=COLOR_BG)
            row_frame.grid(row=row_idx, column=0, pady=3)

            # Create buttons for each letter
            for letter in row_letters:
                btn = tk.Button(
                    row_frame,
                    text=letter,
                    width=KEYBOARD_BUTTON_WIDTH,
                    height=BUTTON_HEIGHT,
                    relief="raised",
                    bg=COLOR_EMPTY,
                    fg="black",
                    state="disabled",
                    font=FONT_KEYBOARD,
                    disabledforeground="black"
                )
                btn.pack(side="left", padx=PADDING_KEYBOARD)
                self.keyboard_buttons[letter.lower()] = btn

    def _get_color_for_status(self, status: str) -> tuple:
        """
        Map game status to display colors.
        
        Args:
            status: Status code (CORRECT, PRESENT, or ABSENT).
            
        Returns:
            Tuple of (background_color, foreground_color).
        """
        if status == CORRECT:
            return COLOR_CORRECT, "white"
        elif status == PRESENT:
            return COLOR_PRESENT, "white"
        else:  # ABSENT
            return COLOR_ABSENT, "white"

    def _apply_colors_to_row(self, row_idx: int, guess: str, statuses: List[str]) -> None:
        """
        Update the display colors for a completed guess row.
        
        Args:
            row_idx: Index of the row to update.
            guess: The guessed word.
            statuses: List of status codes for each letter.
        """
        for col_idx in range(WORD_LENGTH):
            label = self.labels[row_idx][col_idx]
            letter = guess[col_idx].upper()
            status = statuses[col_idx]

            # Update label text and colors
            label.config(text=letter)
            bg_color, fg_color = self._get_color_for_status(status)
            label.config(bg=bg_color, fg=fg_color)

    def _update_keyboard(self) -> None:
        """
        Update keyboard button colors based on current game state.
        """
        status_map = self.game.get_keyboard_status()

        for letter, button in self.keyboard_buttons.items():
            status = status_map.get(letter)
            if status:
                bg_color, fg_color = self._get_color_for_status(status)
                button.config(bg=bg_color, fg=fg_color)

    def _handle_game_won(self) -> None:
        """
        Handle the game won state by updating UI and showing dialog.
        """
        attempts = self.game.attempts_used
        word = self.game.secret.upper()

        status_msg = MSG_WIN_TEMPLATE.format(attempts=attempts)
        self.status_label.config(text=status_msg)

        dialog_msg = MSG_WIN_DIALOG.format(word=word)
        messagebox.showinfo("You win!", dialog_msg)

        self.entry.config(state="disabled")
        logger.info(f"Game won in {attempts} attempts")

    def _handle_game_lost(self) -> None:
        """
        Handle the game lost state by updating UI and showing dialog.
        """
        word = self.game.secret.upper()

        status_msg = MSG_LOSS_TEMPLATE.format(word=word)
        self.status_label.config(text=status_msg)

        dialog_msg = MSG_LOSS_DIALOG.format(word=word)
        messagebox.showinfo("Game Over", dialog_msg)

        self.entry.config(state="disabled")
        logger.info(f"Game lost. Secret word was: {word}")

    def _handle_game_in_progress(self) -> None:
        """
        Update UI for ongoing game state.
        """
        attempts = self.game.attempts_used
        status_msg = MSG_ATTEMPTS_TEMPLATE.format(attempts=attempts)
        self.status_label.config(text=status_msg)

    def _on_submit(self, event=None) -> None:
        """
        Handle guess submission from user input.
        
        Args:
            event: Optional event object from key binding.
        """
        guess = self.entry.get().strip()

        # Validate guess format
        is_valid, validation_msg = self.game.validate_guess(guess)
        if not is_valid:
            messagebox.showwarning("Invalid guess", validation_msg)
            return

        # Submit guess to game
        try:
            statuses = self.game.submit_guess(guess)
        except ValueError as error:
            messagebox.showerror("Error", str(error))
            logger.error(f"Error submitting guess: {error}")
            return

        # Update board display
        row_idx = self.game.attempts_used - 1
        self._apply_colors_to_row(row_idx, guess.lower(), statuses)
        self._update_keyboard()
        self.entry.delete(0, tk.END)

        # Handle game state
        if self.game.is_won:
            self._handle_game_won()
        elif self.game.is_over:
            self._handle_game_lost()
        else:
            self._handle_game_in_progress()


def run_gui(date=None, random_word: bool = False) -> None:
    """
    Launch the Wordle GUI application.
    
    Args:
        date: Optional date string for daily word selection.
        random_word: If True, use a random word; otherwise use daily word.
    """
    app = WordleGUI(date=date, random_word=random_word)
    app.mainloop()