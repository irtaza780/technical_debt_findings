import logging
import sys
from typing import Optional

from gui import GameUI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_application() -> Optional[GameUI]:
    """
    Initialize the Dou Dizhu game application.
    
    Creates and returns a GameUI instance for the Dou Dizhu card game.
    Handles initialization errors gracefully.
    
    Returns:
        Optional[GameUI]: The initialized game UI instance, or None if initialization fails.
    """
    try:
        logger.info("Initializing Dou Dizhu game application")
        game_ui = GameUI()
        logger.info("Application initialized successfully")
        return game_ui
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        return None


def run_application(game_ui: GameUI) -> None:
    """
    Start the Tkinter event loop for the game application.
    
    Args:
        game_ui (GameUI): The initialized game UI instance to run.
    """
    try:
        logger.info("Starting application event loop")
        game_ui.run()
        logger.info("Application closed normally")
    except Exception as e:
        logger.error(f"Application encountered an error: {e}", exc_info=True)
        sys.exit(1)


def main() -> None:
    """
    Main entry point for the Dou Dizhu game application.
    
    Initializes the GUI and starts the Tkinter event loop.
    """
    game_ui = initialize_application()
    
    if game_ui is None:
        logger.critical("Failed to initialize application. Exiting.")
        sys.exit(1)
    
    run_application(game_ui)


if __name__ == "__main__":
    main()