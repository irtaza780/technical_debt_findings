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
    Extract and normalize puzzle data from the raw puzzle dictionary.
    
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


def _create_model(puzzle_data: dict) -> CrosswordModel:
    """
    Create and initialize the CrosswordModel with puzzle data.
    
    Args:
        puzzle_data: Dictionary containing normalized puzzle data
        
    Returns:
        Initialized CrosswordModel instance
    """
    logger.info(f"Creating model for puzzle: {puzzle_data['title']}")
    
    model = CrosswordModel(
        solution_rows=puzzle_data["solution_rows"],
        across_clues_by_answer=puzzle_data["across_clues_by_answer"],
        down_clues_by_answer=puzzle_data["down_clues_by_answer"],
        across_clues_by_number=puzzle_data["across_clues_by_number"],
        down_clues_by_number=puzzle_data["down_clues_by_number"],
        title=puzzle_data["title"],
    )
    
    return model


def _create_view(root: tk.Tk, model: CrosswordModel) -> CrosswordView:
    """
    Create and initialize the CrosswordView GUI.
    
    Args:
        root: Tkinter root window
        model: CrosswordModel instance for title reference
        
    Returns:
        Initialized CrosswordView instance
    """
    logger.info("Creating GUI view")
    view = CrosswordView(root, title=model.title)
    return view


def _initialize_application() -> tuple[CrosswordModel, CrosswordView, tk.Tk]:
    """
    Initialize all application components (model, view, controller).
    
    Returns:
        Tuple of (model, view, root_window) for the application
        
    Raises:
        KeyError: If puzzle data is invalid
        Exception: If puzzle loading fails
    """
    try:
        logger.info("Loading puzzle data")
        puzzle = get_puzzle()
        
        puzzle_data = _extract_puzzle_data(puzzle)
        model = _create_model(puzzle_data)
        
        root = tk.Tk()
        view = _create_view(root, model)
        
        logger.info("Initializing controller")
        CrosswordController(model, view)
        
        return model, view, root
        
    except KeyError as e:
        logger.error(f"Invalid puzzle data structure: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise


def main() -> None:
    """
    Main entry point for the Crossword Puzzle application.
    
    Initializes the model with puzzle data, sets up the GUI view,
    and connects them via the controller. Starts the Tkinter event loop.
    """
    try:
        logger.info("Starting Crossword Puzzle application")
        _, _, root = _initialize_application()
        
        logger.info("Launching GUI event loop")
        root.mainloop()
        
    except Exception as e:
        logger.critical(f"Application failed to start: {e}")
        raise


if __name__ == "__main__":
    main()