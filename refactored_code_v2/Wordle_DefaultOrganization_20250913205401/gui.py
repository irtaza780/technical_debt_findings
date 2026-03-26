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
INITIAL_STATUS_TEXT = "Guess the 5-letter word!"
WIN_MESSAGE_TEMPLATE = "Congratulations! You won in {attempts}/{total}."
LOSS_MESSAGE_TEMPLATE = "Out of tries. The word was {word}."
ATTEMPTS_STATUS_TEMPLATE = "Attempts: {attempts}/{total}"


class WordleGUI(tk.Tk):
    """
    Tkinter-based GUI for the Wordle game.
    
    Manages the game board display, keyboard input, and game state visualization.
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
        self.labels: List[List[tk.Label]] = []
        self.keyboard_buttons: Dict[str, tk.Button] = {}
        self.status_label: tk.Label = None
        self.entry: tk.Entry = None

        # Build UI components
        self._build_board()
        self._build_input()
        self._build_keyboard()
        self.resizable(False, False)
        
        logger.info(f"Wordle GUI initialized with secret word length: {len(secret)}")

    @staticmethod
    def _select_secret_word(date=None, random_word=False) -> str:
        """
        Select the secret word based on game mode.
        
        Args:
            date: Optional date for daily word selection.
            random_word: If True, select random word; otherwise select daily word.
            
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

    def _build_board(self):
        """
        Build the game board with a 6x5 grid of letter labels.
        """
        board_frame = tk.Frame(self, bg=COLOR_BG)
        board_frame.grid(row=0, column=0, padx=PADDING_STANDARD, pady=PADDING_STANDARD, columnspan=3)
        
        # Create grid of labels for letter display
        for row_idx in range(BOARD_ROWS):
            row_labels = []
            for col_idx in range(WORD_LENGTH):
                label = self._create_board_label(board_frame, row_idx, col_idx)
                row_labels.append(label)
            self.labels.append(row_labels)
        
        # Create status label
        self.status_label = tk.Label(
            self,
            text=INITIAL_STATUS_TEXT,
            bg=COLOR_BG,
            fg=COLOR_TEXT,
            font=FONT_STATUS
        )
        self.status_label.grid(row=1, column=0, padx=PADDING_STANDARD, pady=(0, PADDING_STANDARD), sticky="w")

    @staticmethod
    def _create_board_label(parent_frame: tk.Frame, row: int, col: int) -> tk.Label:
        """
        Create a single board cell label.
        
        Args:
            parent_frame: The parent frame to place the label in.
            row: Row index in the board.
            col: Column index in the board.
            
        Returns:
            The created label widget.
        """
        label = tk.Label(
            parent_frame,
            text=" ",
            width=CELL_WIDTH,
            height=CELL_HEIGHT,
            font=FONT_BOARD,
            bg=COLOR_EMPTY,
            fg="black",
            relief="groove",
            bd=2
        )
        label.grid(row=row, column=col, padx=PADDING_CELL, pady=PADDING_CELL)
        return label

    def _build_input(self):
        """
        Build the input entry field and submit button.
        """
        input_frame = tk.Frame(self, bg=COLOR_BG)
        input_frame.grid(row=2, column=0, padx=PADDING_STANDARD, pady=PADDING_STANDARD, sticky="w")
        
        self.entry = tk.Entry(input_frame, width=ENTRY_WIDTH, font=ENTRY_FONT)
        self.entry.grid(row=0, column=0, padx=(0, 8))
        self.entry.bind("<Return>", self._on_submit)
        
        submit_btn = tk.Button(input_frame, text="Submit", command=self._on_submit)
        submit_btn.grid(row=0, column=1)

    def _build_keyboard(self):
        """
        Build the on-screen QWERTY keyboard.
        """
        kb_frame = tk.Frame(self, bg=COLOR_BG)
        kb_frame.grid(row=3, column=0, padx=PADDING_STANDARD, pady=(0, PADDING_STANDARD))
        
        for row_idx, row_letters in enumerate(QWERTY_LAYOUT):
            row_frame = tk.Frame(kb_frame, bg=COLOR_BG)
            row_frame.grid(row=row_idx, column=0, pady=3)
            
            for letter in row_letters:
                button = self._create_keyboard_button(row_frame, letter)
                self.keyboard_buttons[letter.lower()] = button

    @staticmethod
    def _create_keyboard_button(parent_frame: tk.Frame, letter: str) -> tk.Button:
        """
        Create a single keyboard button.
        
        Args:
            parent_frame: The parent frame to place the button in.
            letter: The letter to display on the button.
            
        Returns:
            The created button widget.
        """
        button = tk.Button(
            parent_frame,
            text=letter,
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            relief="raised",
            bg=COLOR_EMPTY,
            fg="black",
            state="disabled",
            font=FONT_KEYBOARD,
            disabledforeground="black"
        )
        button.pack(side="left", padx=PADDING_KEYBOARD)
        return button

    def _apply_colors_to_row(self, row_idx: int, guess: str, statuses: List[str]):
        """
        Apply color coding to a completed guess row based on letter statuses.
        
        Args:
            row_idx: The row index to color.
            guess: The guessed word.
            statuses: List of status strings (CORRECT, PRESENT, or ABSENT) for each letter.
        """
        for col_idx in range(WORD_LENGTH):
            label = self.labels[row_idx][col_idx]
            letter = guess[col_idx].upper()
            status = statuses[col_idx]
            
            label.config(text=letter)
            self._apply_status_color(label, status)

    @staticmethod
    def _apply_status_color(label: tk.Label, status: str):
        """
        Apply background and foreground colors to a label based on letter status.
        
        Args:
            label: The label widget to color.
            status: The status string (CORRECT, PRESENT, or ABSENT).
        """
        if status == CORRECT:
            label.config(bg=COLOR_CORRECT, fg="white")
        elif status == PRESENT:
            label.config(bg=COLOR_PRESENT, fg="white")
        else:  # ABSENT
            label.config(bg=COLOR_ABSENT, fg="white")

    def _update_keyboard(self):
        """
        Update keyboard button colors based on current game state.
        """
        status_map = self.game.get_keyboard_status()
        
        for letter, button in self.keyboard_buttons.items():
            status = status_map.get(letter)
            self._apply_status_color(button, status)

    def _handle_game_end(self):
        """
        Handle end-of-game state (win or loss) and update UI accordingly.
        """
        if self.game.is_won:
            self._handle_win()
        elif self.game.is_over:
            self._handle_loss()

    def _handle_win(self):
        """
        Handle game win state.
        """
        message = WIN_MESSAGE_TEMPLATE.format(
            attempts=self.game.attempts_used,
            total=BOARD_ROWS
        )
        self.status_label.config(text=message)
        messagebox.showinfo("You win!", f"You guessed the word: {self.game.secret.upper()}")
        self.entry.config(state="disabled")
        logger.info(f"Game won in {self.game.attempts_used} attempts")

    def _handle_loss(self):
        """
        Handle game loss state.
        """
        message = LOSS_MESSAGE_TEMPLATE.format(word=self.game.secret.upper())
        self.status_label.config(text=message)
        messagebox.showinfo("Game Over", f"The word was: {self.game.secret.upper()}")
        self.entry.config(state="disabled")
        logger.info("Game lost - out of attempts")

    def _on_submit(self, event=None):
        """
        Handle guess submission from user input.
        
        Args:
            event: Optional event object from key binding.
        """
        guess = self.entry.get().strip()
        
        # Validate guess format
        is_valid, validation_message = self.game.validate_guess(guess)
        if not is_valid:
            messagebox.showwarning("Invalid guess", validation_message)
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
        
        # Check game state and update status
        self._handle_game_end()
        
        if not self.game.is_over:
            status_text = ATTEMPTS_STATUS_TEMPLATE.format(
                attempts=self.game.attempts_used,
                total=BOARD_ROWS
            )
            self.status_label.config(text=status_text)
        
        logger.info(f"Guess submitted: {guess}")


def run_gui(date=None, random_word: bool = False):
    """
    Launch the Wordle GUI application.
    
    Args:
        date: Optional date string for daily word selection.
        random_word: If True, use a random word; otherwise use daily word.
    """
    app = WordleGUI(date=date, random_word=random_word)
    app.mainloop()