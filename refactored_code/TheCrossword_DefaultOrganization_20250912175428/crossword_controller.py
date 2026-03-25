import logging
from tkinter import messagebox
from typing import Optional, Tuple
from crossword_model import CrosswordModel
from crossword_view import CrosswordView

# Configure logging
logger = logging.getLogger(__name__)

# Constants
VALID_DIRECTIONS = ("A", "D")
DIRECTION_ACROSS = "A"
DIRECTION_DOWN = "D"
MIN_ANSWER_LENGTH = 1
ERROR_STATUS_OK = False
SUCCESS_STATUS_OK = True
COMPLETION_MESSAGE = "Congratulations! You filled in all correct words."
RESET_MESSAGE = "Puzzle reset. You can start over."
INVALID_CLUE_MESSAGE = "Please enter a valid clue number."
INVALID_DIRECTION_MESSAGE = "Direction must be A (Across) or D (Down)."
EMPTY_ANSWER_MESSAGE = "Please enter an answer."


class CrosswordController:
    """
    Controller for the crossword puzzle application.
    
    Manages interactions between the CrosswordModel and CrosswordView,
    handling user input validation, answer submission, and UI updates.
    """

    def __init__(self, model: CrosswordModel, view: CrosswordView) -> None:
        """
        Initialize the crossword controller.
        
        Args:
            model: The CrosswordModel instance managing puzzle state.
            view: The CrosswordView instance managing the UI.
        """
        self.model = model
        self.view = view

        self._initialize_grid()
        self._initialize_ui()
        self._bind_event_handlers()

    def _initialize_grid(self) -> None:
        """Initialize the grid display with dimensions from the model."""
        rows, cols = self.model.get_dimensions()
        self.view.build_grid(rows, cols)
        logger.debug(f"Grid initialized with dimensions: {rows}x{cols}")

    def _initialize_ui(self) -> None:
        """Initialize UI components with model data."""
        # Perform initial render to display puzzle state
        self._refresh_all()

        # Configure clue number selector with valid range
        min_number = self.model.min_number()
        max_number = self.model.max_number()
        self.view.set_number_range(min_number, max_number)
        self.view.number_var.set(str(min_number))
        logger.debug(f"Clue number range set: {min_number}-{max_number}")

    def _bind_event_handlers(self) -> None:
        """Bind user action handlers to view events."""
        self.view.bind_submit(self.on_submit)
        self.view.bind_reset(self.on_reset)

    def _refresh_all(self) -> None:
        """
        Refresh all UI components to reflect current model state.
        
        Ensures filled flags are synchronized with the grid before rendering
        to maintain consistency when entries are completed via crossings.
        """
        # Synchronize filled flags with current grid state
        self.model.refresh_entry_flags()

        # Update grid display
        self.view.update_grid(self.model.get_cell)

        # Update clue lists with current entry states
        self.view.render_clues(
            across_entries=self.model.get_entries(DIRECTION_ACROSS),
            down_entries=self.model.get_entries(DIRECTION_DOWN),
        )
        logger.debug("UI refresh completed")

    def _validate_user_input(
        self, number: Optional[int], direction: str, answer: str
    ) -> Tuple[bool, str]:
        """
        Validate user input for answer submission.
        
        Args:
            number: The clue number entered by the user.
            direction: The direction (A or D) entered by the user.
            answer: The answer text entered by the user.
        
        Returns:
            A tuple of (is_valid, error_message). If valid, error_message is empty.
        """
        if number is None:
            return False, INVALID_CLUE_MESSAGE

        if direction not in VALID_DIRECTIONS:
            return False, INVALID_DIRECTION_MESSAGE

        if not answer or len(answer) < MIN_ANSWER_LENGTH:
            return False, EMPTY_ANSWER_MESSAGE

        return True, ""

    def _handle_successful_submission(self) -> None:
        """Handle UI updates after a successful answer submission."""
        self.view.clear_answer_field()
        self._refresh_all()

        # Check if puzzle is complete and notify user
        if self.model.is_complete():
            logger.info("Crossword puzzle completed successfully")
            messagebox.showinfo("Crossword", COMPLETION_MESSAGE)

    def _handle_failed_submission(self, error_message: str) -> None:
        """
        Handle UI updates after a failed answer submission.
        
        Args:
            error_message: The error message to display to the user.
        """
        self.view.set_status(error_message, ok=ERROR_STATUS_OK)
        logger.warning(f"Answer submission failed: {error_message}")

    def on_submit(self) -> None:
        """
        Handle answer submission from the user.
        
        Validates input, submits to model for verification, and updates UI
        based on success or failure.
        """
        number, direction, answer = self.view.get_input()

        # Validate user input
        is_valid, error_message = self._validate_user_input(number, direction, answer)
        if not is_valid:
            self._handle_failed_submission(error_message)
            return

        # Attempt to place answer in model
        try:
            is_correct, result_message = self.model.place_answer(number, direction, answer)
            self.view.set_status(result_message, ok=is_correct)

            if is_correct:
                self._handle_successful_submission()
            else:
                logger.info(f"Incorrect answer for clue {number}{direction}: {result_message}")

        except ValueError as e:
            error_msg = f"Error processing answer: {str(e)}"
            self._handle_failed_submission(error_msg)
            logger.error(error_msg, exc_info=True)

    def on_reset(self) -> None:
        """
        Handle puzzle reset action.
        
        Clears all entries and refreshes the UI to initial state.
        """
        self.model.reset()
        self._refresh_all()
        self.view.set_status(RESET_MESSAGE, ok=SUCCESS_STATUS_OK)
        logger.info("Puzzle reset by user")