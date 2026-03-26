import logging
import tkinter as tk
from data import get_puzzle
from crossword_model import CrosswordModel
from crossword_view import CrosswordView
from crossword_controller import CrosswordController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application constants
DEFAULT_PUZZLE_TITLE = "Crossword"
PUZZLE_DATA_KEYS = {
    "solution_rows": "solution_rows",
    "across_clues_by_answer": "across_clues_by_answer",
    "down_clues_by_answer": "down_clues_by_answer",
    "across_clues_by_number": "across_clues_by_number",
    "down_clues_by_number": "down_clues_by_number",
    "title": "name",
}


def _extract_puzzle_data(puzzle: dict) -> dict:
    """
    Extract and normalize puzzle data from raw puzzle dictionary.
    
    Args:
        puzzle: Raw puzzle data dictionary from get_puzzle()
        
    Returns:
        Dictionary containing normalized puzzle data with safe defaults
        
    Raises:
        KeyError: If required 'solution_rows' key is missing from puzzle
    """
    if "solution_rows" not in puzzle:
        raise KeyError("Puzzle data must contain 'solution_rows' key")
    
    return {
        "solution_rows": puzzle["solution_rows"],
        "across_clues_by_answer": puzzle.get(
            PUZZLE_DATA_KEYS["across_clues_by_answer"], {}
        ),
        "down_clues_by_answer": puzzle.get(
            PUZZLE_DATA_KEYS["down_clues_by_answer"], {}
        ),
        "across_clues_by_number": puzzle.get(
            PUZZLE_DATA_KEYS["across_clues_by_number"]
        ),
        "down_clues_by_number": puzzle.get(
            PUZZLE_DATA_KEYS["down_clues_by_number"]
        ),
        "title": puzzle.get(PUZZLE_DATA_KEYS["title"], DEFAULT_PUZZLE_TITLE),
    }


def _initialize_model(puzzle_data: dict) -> CrosswordModel:
    """
    Create and initialize the crossword model with puzzle data.
    
    Args:
        puzzle_data: Dictionary containing normalized puzzle data
        
    Returns:
        Initialized CrosswordModel instance
    """
    logger.info(f"Initializing model with puzzle: {puzzle_data['title']}")
    
    model = CrosswordModel(
        solution_rows=puzzle_data["solution_rows"],
        across_clues_by_answer=puzzle_data["across_clues_by_answer"],
        down_clues_by_answer=puzzle_data["down_clues_by_answer"],
        across_clues_by_number=puzzle_data["across_clues_by_number"],
        down_clues_by_number=puzzle_data["down_clues_by_number"],
        title=puzzle_data["title"],
    )
    
    return model


def _initialize_view(model: CrosswordModel) -> tuple[tk.Tk, CrosswordView]:
    """
    Create and initialize the GUI view with Tkinter root window.
    
    Args:
        model: CrosswordModel instance to display
        
    Returns:
        Tuple of (Tk root window, CrosswordView instance)
    """
    logger.info("Initializing GUI view")
    
    root = tk.Tk()
    view = CrosswordView(root, title=model.title)
    
    return root, view


def _initialize_controller(
    model: CrosswordModel, view: CrosswordView
) -> CrosswordController:
    """
    Create and initialize the controller to connect model and view.
    
    Args:
        model: CrosswordModel instance
        view: CrosswordView instance
        
    Returns:
        Initialized CrosswordController instance
    """
    logger.info("Initializing controller")
    
    controller = CrosswordController(model, view)
    
    return controller


def main() -> None:
    """
    Main entry point for the Crossword Puzzle application.
    
    Initializes the model with puzzle data, sets up the GUI view,
    connects them via the controller, and starts the Tkinter event loop.
    
    Raises:
        KeyError: If puzzle data is malformed
        Exception: If initialization fails at any stage
    """
    try:
        logger.info("Starting Crossword Puzzle application")
        
        # Load and validate puzzle data
        puzzle = get_puzzle()
        puzzle_data = _extract_puzzle_data(puzzle)
        
        # Initialize MVC components
        model = _initialize_model(puzzle_data)
        root, view = _initialize_view(model)
        _initialize_controller(model, view)
        
        logger.info("Application initialized successfully")
        
        # Start Tkinter event loop
        root.mainloop()
        
    except KeyError as key_error:
        logger.error(f"Invalid puzzle data structure: {key_error}")
        raise
    except Exception as initialization_error:
        logger.error(f"Failed to initialize application: {initialization_error}")
        raise


if __name__ == "__main__":
    main()