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
COMPLETION_MESSAGE = "Congratulations! You filled in all correct words."
RESET_MESSAGE = "Puzzle reset. You can start over."
INVALID_NUMBER_MESSAGE = "Please enter a valid clue number."
INVALID_DIRECTION_MESSAGE = "Direction must be A (Across) or D (Down)."
EMPTY_ANSWER_MESSAGE = "Please enter an answer."


class CrosswordController:
    """
    Controller that manages interactions between the CrosswordModel and CrosswordView.
    
    Handles user input validation, answer submission, grid updates, and puzzle completion.
    Maintains synchronization between model state and view display.
    """

    def __init__(self, model: CrosswordModel, view: CrosswordView) -> None:
        """
        Initialize the controller with model and view instances.
        
        Args:
            model: The CrosswordModel instance containing puzzle logic.
            view: The CrosswordView instance for UI rendering.
        """
        self.model = model
        self.view = view

        self._initialize_grid()
        self._initialize_clue_selector()
        self._bind_view_actions()

        logger.info("CrosswordController initialized successfully")

    def _initialize_grid(self) -> None:
        """Build the grid UI and perform initial render."""
        rows, cols = self.model.get_dimensions()
        self.view.build_grid(rows, cols)
        self._refresh_all()

    def _initialize_clue_selector(self) -> None:
        """
        Set up the clue number selector with valid range.
        
        Initializes the spinbox to the minimum available clue number
        for improved usability.
        """
        min_number = self.model.min_number()
        max_number = self.model.max_number()
        self.view.set_number_range(min_number, max_number)
        self.view.number_var.set(str(min_number))

    def _bind_view_actions(self) -> None:
        """Bind view events to controller action handlers."""
        self.view.bind_submit(self.on_submit)
        self.view.bind_reset(self.on_reset)

    def _refresh_all(self) -> None:
        """
        Refresh the entire UI to reflect current model state.
        
        Recomputes filled flags from the grid before rendering to ensure
        clue checkmarks remain consistent even when entries are completed
        via crossings.
        """
        self.model.refresh_entry_flags()
        self._update_grid_display()
        self._update_clue_display()

    def _update_grid_display(self) -> None:
        """Update the grid view with current cell states from the model."""
        self.view.update_grid(self.model.get_cell)

    def _update_clue_display(self) -> None:
        """Update the clue lists (across and down) from the model."""
        across_entries = self.model.get_entries(DIRECTION_ACROSS)
        down_entries = self.model.get_entries(DIRECTION_DOWN)
        self.view.render_clues(
            across_entries=across_entries,
            down_entries=down_entries,
        )

    def on_submit(self) -> None:
        """
        Handle answer submission from the user.
        
        Validates input, submits answer to model, updates UI, and checks
        for puzzle completion.
        """
        number, direction, answer = self.view.get_input()

        # Validate input components
        if not self._validate_input(number, direction, answer):
            return

        # Attempt to place answer in model
        is_valid, feedback_message = self.model.place_answer(number, direction, answer)
        self.view.set_status(feedback_message, ok=is_valid)

        if is_valid:
            self._handle_valid_answer()
        else:
            self._handle_invalid_answer()

    def _validate_input(self, number: Optional[int], direction: str, answer: str) -> bool:
        """
        Validate user input before submission.
        
        Args:
            number: The clue number entered by the user.
            direction: The direction (A or D) entered by the user.
            answer: The answer text entered by the user.
            
        Returns:
            True if all inputs are valid, False otherwise.
        """
        if number is None:
            self.view.set_status(INVALID_NUMBER_MESSAGE, ok=False)
            return False

        if direction not in VALID_DIRECTIONS:
            self.view.set_status(INVALID_DIRECTION_MESSAGE, ok=False)
            return False

        if not answer or len(answer) < MIN_ANSWER_LENGTH:
            self.view.set_status(EMPTY_ANSWER_MESSAGE, ok=False)
            return False

        return True

    def _handle_valid_answer(self) -> None:
        """
        Process actions following a valid answer submission.
        
        Clears the input field, refreshes the display, and checks
        if the puzzle is complete.
        """
        self.view.clear_answer_field()
        self._refresh_all()

        if self.model.is_complete():
            self._announce_completion()

    def _handle_invalid_answer(self) -> None:
        """
        Process actions following an invalid answer submission.
        
        Keeps the answer in the input field to allow user correction.
        """
        logger.debug("Invalid answer submitted; answer retained for correction")

    def _announce_completion(self) -> None:
        """Display completion message when puzzle is solved."""
        logger.info("Crossword puzzle completed successfully")
        messagebox.showinfo("Crossword", COMPLETION_MESSAGE)

    def on_reset(self) -> None:
        """
        Handle puzzle reset action.
        
        Clears all entries from the model and refreshes the UI.
        """
        self.model.reset()
        self._refresh_all()
        self.view.set_status(RESET_MESSAGE, ok=True)
        logger.info("Crossword puzzle reset by user")