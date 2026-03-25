import logging
import sys
from typing import Optional

from gui import GameUI

# Configuration constants
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
APPLICATION_NAME = "Dou Dizhu Game"

# Initialize logging
logger = logging.getLogger(APPLICATION_NAME)
logger.setLevel(LOG_LEVEL)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(LOG_LEVEL)
formatter = logging.Formatter(LOG_FORMAT)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def initialize_game_ui() -> Optional[GameUI]:
    """
    Initialize the game UI instance.
    
    Returns:
        GameUI: An instance of the game UI, or None if initialization fails.
        
    Raises:
        Exception: If GUI initialization encounters an error.
    """
    try:
        logger.info("Initializing %s", APPLICATION_NAME)
        game_ui = GameUI()
        logger.info("%s initialized successfully", APPLICATION_NAME)
        return game_ui
    except ImportError as import_error:
        logger.error("Failed to import GUI module: %s", import_error)
        return None
    except Exception as initialization_error:
        logger.error("Failed to initialize %s: %s", APPLICATION_NAME, initialization_error)
        return None


def run_application() -> None:
    """
    Main entry point for the Dou Dizhu game application.
    
    Initializes the GUI and starts the Tkinter event loop.
    Handles graceful shutdown and error logging.
    """
    logger.info("Starting %s", APPLICATION_NAME)
    
    game_ui = initialize_game_ui()
    
    if game_ui is None:
        logger.critical("Failed to initialize application. Exiting.")
        sys.exit(1)
    
    try:
        logger.info("Launching game event loop")
        game_ui.run()
        logger.info("%s closed successfully", APPLICATION_NAME)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as runtime_error:
        logger.critical("Unexpected error during application runtime: %s", runtime_error)
        sys.exit(1)


if __name__ == "__main__":
    run_application()