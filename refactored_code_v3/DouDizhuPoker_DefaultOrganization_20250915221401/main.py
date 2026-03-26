import logging
import sys
from typing import Optional

from gui import GameUI

# Configuration constants
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
APPLICATION_NAME = "Dou Dizhu Game"

# Initialize logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('dou_dizhu.log')
    ]
)

logger = logging.getLogger(__name__)


def initialize_application() -> Optional[GameUI]:
    """
    Initialize the Dou Dizhu game application.
    
    Creates and configures the main game UI instance.
    
    Returns:
        GameUI: The initialized game UI instance, or None if initialization fails.
        
    Raises:
        Exception: If the GUI fails to initialize.
    """
    try:
        logger.info(f"Initializing {APPLICATION_NAME}")
        game_ui = GameUI()
        logger.info(f"{APPLICATION_NAME} initialized successfully")
        return game_ui
    except ImportError as e:
        logger.error(f"Failed to import required GUI module: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during application initialization: {e}")
        raise


def run_application(game_ui: GameUI) -> None:
    """
    Start the main event loop for the game application.
    
    Args:
        game_ui (GameUI): The initialized game UI instance to run.
        
    Raises:
        RuntimeError: If the game UI fails to start.
    """
    try:
        logger.info(f"Starting {APPLICATION_NAME} event loop")
        game_ui.run()
        logger.info(f"{APPLICATION_NAME} closed normally")
    except RuntimeError as e:
        logger.error(f"Runtime error while running application: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during application execution: {e}")
        raise


def main() -> None:
    """
    Main entry point for the Dou Dizhu game application.
    
    Initializes the GUI and starts the Tkinter event loop.
    """
    try:
        game_ui = initialize_application()
        if game_ui is not None:
            run_application(game_ui)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Critical error in main application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()