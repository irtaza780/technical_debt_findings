from __future__ import annotations

import logging
import random
from collections import Counter
from typing import List, Tuple, Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Game configuration constants
DEFAULT_COLORS = ["red", "green", "blue", "yellow", "orange", "purple"]
DEFAULT_CODE_LENGTH = 4
DEFAULT_MAX_ATTEMPTS = 10
MIN_POSITIVE_VALUE = 1


class MastermindGame:
    """
    Core game logic for Mastermind.

    Implements the Mastermind game where a player attempts to guess a secret code
    within a limited number of attempts. Feedback is provided as exact matches
    (correct symbol in correct position) and partial matches (correct symbol in
    wrong position).

    Attributes:
        code_length: Number of positions in the secret code.
        colors: List of available symbol keys (strings) (e.g., color names or digits).
        max_attempts: Maximum number of attempts allowed.
        allow_duplicates: Whether the secret code can contain duplicate symbols.
    """

    def __init__(
        self,
        code_length: int = DEFAULT_CODE_LENGTH,
        colors: Optional[List[str]] = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        allow_duplicates: bool = True,
        seed: Optional[int] = None,
    ) -> None:
        """
        Initialize a new Mastermind game.

        Args:
            code_length: Length of the secret code (must be positive).
            colors: Available symbols for the code. Defaults to color names.
            max_attempts: Maximum guesses allowed (must be positive).
            allow_duplicates: If False, secret code has unique symbols only.
            seed: Random seed for reproducible games.

        Raises:
            ValueError: If parameters are invalid.
        """
        if colors is None:
            colors = DEFAULT_COLORS

        self._validate_initialization_parameters(code_length, max_attempts, colors, allow_duplicates)

        self.code_length = code_length
        self.colors = colors
        self.max_attempts = max_attempts
        self.allow_duplicates = allow_duplicates

        self._rng = random.Random(seed)
        self._secret: List[str] = []
        self._attempts: int = 0
        self._won: bool = False
        self._history: List[Dict[str, object]] = []

        self.new_game()
        logger.debug(f"Initialized Mastermind game: code_length={code_length}, max_attempts={max_attempts}")

    @staticmethod
    def _validate_initialization_parameters(
        code_length: int,
        max_attempts: int,
        colors: List[str],
        allow_duplicates: bool,
    ) -> None:
        """
        Validate game initialization parameters.

        Args:
            code_length: Length of the secret code.
            max_attempts: Maximum number of attempts.
            colors: List of available colors.
            allow_duplicates: Whether duplicates are allowed in the code.

        Raises:
            ValueError: If any parameter is invalid.
        """
        if code_length < MIN_POSITIVE_VALUE:
            raise ValueError("code_length must be positive")
        if max_attempts < MIN_POSITIVE_VALUE:
            raise ValueError("max_attempts must be positive")
        if not colors:
            raise ValueError("colors list must not be empty")
        if not allow_duplicates and code_length > len(colors):
            raise ValueError(
                "code_length cannot exceed number of colors when duplicates are not allowed"
            )

    def new_game(self) -> None:
        """
        Start a new game by generating a fresh secret code and resetting game state.

        The secret code is randomly generated from the available colors, respecting
        the allow_duplicates setting.
        """
        self._secret = self._generate_secret_code()
        self._attempts = 0
        self._won = False
        self._history.clear()
        logger.info("New game started")

    def _generate_secret_code(self) -> List[str]:
        """
        Generate a random secret code.

        Returns:
            A list of randomly selected colors forming the secret code.
        """
        if self.allow_duplicates:
            # choice allows duplicates
            return [self._rng.choice(self.colors) for _ in range(self.code_length)]
        else:
            # sample avoids duplicates
            return self._rng.sample(self.colors, self.code_length)

    def remaining_attempts(self) -> int:
        """
        Get the number of attempts remaining.

        Returns:
            Number of guesses the player can still make.
        """
        return self.max_attempts - self._attempts

    def attempts_made(self) -> int:
        """
        Get the number of attempts used so far.

        Returns:
            Number of guesses already submitted.
        """
        return self._attempts

    def is_over(self) -> bool:
        """
        Check if the game has ended.

        Returns:
            True if the game is won or attempts are exhausted, False otherwise.
        """
        return self._won or self._attempts >= self.max_attempts

    def has_won(self) -> bool:
        """
        Check if the player has successfully guessed the secret code.

        Returns:
            True if the code has been cracked, False otherwise.
        """
        return self._won

    def reveal_secret(self) -> List[str]:
        """
        Reveal the secret code.

        Useful for displaying the answer at the end of the game.

        Returns:
            A copy of the secret code.
        """
        return list(self._secret)

    def get_history(self) -> List[Dict[str, object]]:
        """
        Get the complete history of all guesses and their feedback.

        Returns:
            List of dictionaries, each containing:
                - 'guess': List[str] - the guessed code
                - 'exact': int - number of exact matches
                - 'partial': int - number of partial matches
        """
        return list(self._history)

    def evaluate_guess(self, guess: List[str]) -> Tuple[int, int]:
        """
        Evaluate a player's guess against the secret code.

        Provides feedback as exact matches (correct symbol in correct position)
        and partial matches (correct symbol in wrong position).

        Args:
            guess: The guessed code as a list of symbols.

        Returns:
            A tuple of (exact_matches, partial_matches).

        Raises:
            RuntimeError: If the game is already over.
            ValueError: If the guess is invalid (wrong length or invalid symbols).
        """
        self._validate_guess(guess)

        exact, partial = self._calculate_matches(guess)

        # Record the attempt
        self._attempts += 1
        if exact == self.code_length:
            self._won = True
            logger.info(f"Game won in {self._attempts} attempts")

        self._record_guess(guess, exact, partial)
        return exact, partial

    def _validate_guess(self, guess: List[str]) -> None:
        """
        Validate that a guess is legal.

        Args:
            guess: The guessed code to validate.

        Raises:
            RuntimeError: If the game is already over.
            ValueError: If the guess has wrong length or contains invalid symbols.
        """
        if self.is_over():
            raise RuntimeError("Game is already over.")
        if len(guess) != self.code_length:
            raise ValueError(f"Guess must have length {self.code_length}.")
        if any(symbol not in self.colors for symbol in guess):
            raise ValueError("Guess contains invalid symbols.")

    def _calculate_matches(self, guess: List[str]) -> Tuple[int, int]:
        """
        Calculate exact and partial matches between guess and secret.

        Algorithm:
        1. Count exact matches (position and symbol match).
        2. For remaining unmatched positions, count partial matches by comparing
           symbol frequencies in unmatched portions.

        Args:
            guess: The guessed code.

        Returns:
            A tuple of (exact_matches, partial_matches).
        """
        secret = self._secret
        exact = 0
        unmatched_secret: List[str] = []
        unmatched_guess: List[str] = []

        # First pass: identify exact matches and collect unmatched symbols
        for secret_symbol, guess_symbol in zip(secret, guess):
            if secret_symbol == guess_symbol:
                exact += 1
            else:
                unmatched_secret.append(secret_symbol)
                unmatched_guess.append(guess_symbol)

        # Second pass: count partial matches from unmatched symbols
        # Use Counter to find minimum overlap per symbol
        secret_counts = Counter(unmatched_secret)
        guess_counts = Counter(unmatched_guess)
        partial = sum(min(secret_counts[symbol], guess_counts[symbol]) for symbol in guess_counts)

        return exact, partial

    def _record_guess(self, guess: List[str], exact: int, partial: int) -> None:
        """
        Record a guess and its feedback in the game history.

        Args:
            guess: The guessed code.
            exact: Number of exact matches.
            partial: Number of partial matches.
        """
        record: Dict[str, object] = {
            "guess": list(guess),
            "exact": exact,
            "partial": partial,
        }
        self._history.append(record)
        logger.debug(f"Recorded guess: {guess} -> exact={exact}, partial={partial}")