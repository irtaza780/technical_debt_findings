import logging
from collections import Counter
from typing import List, Tuple, Dict, Optional

from words import get_daily_word, is_valid_guess

# Configure logging
logger = logging.getLogger(__name__)

# Game constants
WORD_LENGTH = 5
DEFAULT_MAX_ATTEMPTS = 6
MIN_ASCII_LETTER = ord('A')
MAX_ASCII_LETTER = ord('Z')

# Status constants
ABSENT = 'absent'
PRESENT = 'present'
CORRECT = 'correct'
STATUS_ORDER = {ABSENT: 0, PRESENT: 1, CORRECT: 2}


def evaluate_guess(secret: str, guess: str) -> List[str]:
    """
    Compare a guess against the secret word and return a list of statuses.

    Each position receives one of three statuses:
    - 'correct' (green): letter matches at this position
    - 'present' (yellow): letter exists in word but wrong position
    - 'absent' (grey): letter not in word

    Handles duplicate letters correctly by first marking exact matches,
    then allocating remaining letters as 'present' up to their unused counts.

    Args:
        secret: The target word (case-insensitive).
        guess: The guessed word (case-insensitive).

    Returns:
        A list of status strings, one per letter position.

    Raises:
        ValueError: If guess length does not match secret length.
    """
    secret = secret.lower()
    guess = guess.lower()
    n = len(secret)

    if len(guess) != n:
        raise ValueError(f"Guess length must match secret length ({n}).")

    statuses = [ABSENT] * n
    secret_counts = Counter(secret)

    # First pass: mark correct positions and decrement available letter counts
    for i in range(n):
        if guess[i] == secret[i]:
            statuses[i] = CORRECT
            secret_counts[guess[i]] -= 1

    # Second pass: mark present letters (wrong position) respecting remaining counts
    for i in range(n):
        if statuses[i] == CORRECT:
            continue

        ch = guess[i]
        # Check if this letter has remaining unused occurrences in secret
        if secret_counts.get(ch, 0) > 0:
            statuses[i] = PRESENT
            secret_counts[ch] -= 1

    return statuses


def _validate_word_format(word: str, word_length: int = WORD_LENGTH) -> Tuple[bool, str]:
    """
    Validate that a word has correct length and contains only ASCII letters.

    Args:
        word: The word to validate.
        word_length: Expected word length (default: 5).

    Returns:
        A tuple of (is_valid, error_message).
    """
    if word is None:
        return False, "Please enter a guess."

    word = word.strip()

    if len(word) != word_length:
        return False, f"Your guess must be exactly {word_length} letters."

    if not word.isascii() or not word.isalpha():
        return False, "Your guess must contain only letters (A-Z)."

    return True, ""


def _update_keyboard_status(
    keyboard_status: Dict[str, str],
    guess: str,
    statuses: List[str]
) -> None:
    """
    Update keyboard knowledge with the best-known status for each letter.

    For each letter in the guess, retain the highest-priority status
    (correct > present > absent) based on STATUS_ORDER.

    Args:
        keyboard_status: Dictionary to update with letter statuses.
        guess: The guessed word.
        statuses: The feedback statuses for each position.
    """
    for i, ch in enumerate(guess):
        current_status = keyboard_status.get(ch)
        new_status = statuses[i]

        # Update if no prior knowledge or new status has higher priority
        if current_status is None or STATUS_ORDER[new_status] > STATUS_ORDER[current_status]:
            keyboard_status[ch] = new_status


class WordleGame:
    """
    Manages the state and logic of a Wordle game.

    Attributes:
        secret: The target word to guess.
        max_attempts: Maximum number of allowed guesses (default: 6).
        history: List of (guess, statuses) tuples for all submitted guesses.
    """

    def __init__(
        self,
        secret_word: Optional[str] = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        word_provider=get_daily_word
    ):
        """
        Initialize a new Wordle game.

        Args:
            secret_word: The target word. If None, fetched from word_provider.
            max_attempts: Maximum number of guesses allowed.
            word_provider: Callable that returns a word (default: get_daily_word).

        Raises:
            ValueError: If secret word is invalid.
        """
        self.max_attempts = max_attempts
        self._word_provider = word_provider
        self.secret = secret_word.lower() if secret_word else self._word_provider()
        self._validate_secret_word()
        self.history: List[Tuple[str, List[str]]] = []
        self._keyboard_status: Dict[str, str] = {}
        self._won = False

    def _validate_secret_word(self) -> None:
        """
        Validate that the secret word meets game requirements.

        Raises:
            ValueError: If secret is not a valid 5-letter alphabetic word.
        """
        if len(self.secret) != WORD_LENGTH or not self.secret.isalpha():
            raise ValueError(
                f"Secret word must be a {WORD_LENGTH}-letter alphabetic word."
            )

    def reset_with_date(self, date: Optional[str] = None) -> None:
        """
        Reset the game with a new secret word and clear all history.

        Args:
            date: Optional date parameter to pass to word_provider.
        """
        self.secret = self._word_provider(date=date).lower()
        self._validate_secret_word()
        self.history.clear()
        self._keyboard_status.clear()
        self._won = False
        logger.info("Game reset with new secret word.")

    @property
    def attempts_used(self) -> int:
        """Return the number of guesses submitted so far."""
        return len(self.history)

    @property
    def is_won(self) -> bool:
        """Return True if the secret word has been guessed correctly."""
        return self._won

    @property
    def is_over(self) -> bool:
        """Return True if the game has ended (won or max attempts reached)."""
        return self._won or self.attempts_used >= self.max_attempts

    def validate_guess(self, guess: str) -> Tuple[bool, str]:
        """
        Validate that a guess is a valid English word.

        Checks:
        - Exactly 5 ASCII alphabetic letters (A–Z)
        - Present in the allowed guess dictionary

        Args:
            guess: The word to validate.

        Returns:
            A tuple of (is_valid, error_message).
        """
        is_valid, error_msg = _validate_word_format(guess, WORD_LENGTH)
        if not is_valid:
            return False, error_msg

        guess_lower = guess.lower()
        if not is_valid_guess(guess_lower):
            return False, "Not in word list."

        return True, ""

    def submit_guess(self, guess: str) -> List[str]:
        """
        Validate and evaluate a guess against the secret word.

        Updates game history, win state, and keyboard knowledge.

        Args:
            guess: The guessed word.

        Returns:
            A list of status strings for each letter position.

        Raises:
            ValueError: If the game is over or the guess is invalid.
        """
        if self.is_over:
            raise ValueError("The game is over. No more guesses allowed.")

        is_valid, error_msg = self.validate_guess(guess)
        if not is_valid:
            raise ValueError(error_msg)

        guess_lower = guess.lower()
        statuses = evaluate_guess(self.secret, guess_lower)

        # Record the guess in history
        self.history.append((guess_lower, statuses))

        # Check if this guess wins the game
        if all(status == CORRECT for status in statuses):
            self._won = True
            logger.info(f"Game won! Secret word: {self.secret}")

        # Update keyboard knowledge with best-known status for each letter
        _update_keyboard_status(self._keyboard_status, guess_lower, statuses)

        return statuses

    def get_keyboard_status(self) -> Dict[str, str]:
        """
        Return the best-known status for each letter encountered so far.

        Returns:
            A dictionary mapping letters to their status ('correct', 'present', 'absent').
        """
        return dict(self._keyboard_status)