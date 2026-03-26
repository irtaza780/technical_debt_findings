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
    
    Ensures all Pygame resources are properly released.
    """
    try:
        pygame.quit()
        logger.info("Pygame cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during Pygame cleanup: {e}")


def create_and_run_game() -> None:
    """
    Create a Game instance and run the main game loop.
    
    Raises:
        Exception: If game creation or execution fails.
    """
    try:
        game = Game()
        logger.info("Game instance created")
        game.run()
        logger.info("Game loop completed successfully")
    except Exception as e:
        logger.error(f"Error during game execution: {e}")
        raise


def main() -> None:
    """
    Entry point for the roguelike game.
    
    Initializes Pygame, creates and runs the Game instance,
    and ensures proper cleanup of resources.
    """
    initialize_pygame()
    try:
        create_and_run_game()
    finally:
        cleanup_pygame()


if __name__ == "__main__":
    main()