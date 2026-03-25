import logging
import pygame
from game import Game

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_pygame() -> None:
    """
    Initialize the Pygame library.
    
    Raises:
        Exception: If Pygame initialization fails.
    """
    try:
        pygame.init()
        logger.info("Pygame initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Pygame: {e}")
        raise


def cleanup_pygame() -> None:
    """
    Clean up and quit the Pygame library.
    
    Ensures proper resource cleanup when the game exits.
    """
    try:
        pygame.quit()
        logger.info("Pygame cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during Pygame cleanup: {e}")


def run_game() -> None:
    """
    Initialize and run the roguelike game.
    
    Handles the complete game lifecycle including initialization,
    execution, and cleanup of resources.
    """
    initialize_pygame()
    try:
        game = Game()
        logger.info("Game instance created")
        game.run()
        logger.info("Game completed successfully")
    except Exception as e:
        logger.error(f"Game execution failed: {e}")
        raise
    finally:
        cleanup_pygame()


def main() -> None:
    """
    Entry point for the roguelike game application.
    
    Orchestrates the initialization and execution of the game,
    ensuring proper resource management and error handling.
    """
    try:
        run_game()
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()