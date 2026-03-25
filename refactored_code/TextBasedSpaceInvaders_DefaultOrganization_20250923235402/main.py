import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PYGAME_INSTALL_MESSAGE = (
    "Required dependency 'pygame' is not installed.\n"
    "Install it with:\n"
    "  pip install pygame\n"
    "Exiting gracefully."
)


def _check_pygame_availability():
    """
    Check if pygame is available and importable.
    
    Returns:
        bool: True if pygame is available, False otherwise.
    """
    try:
        import pygame
        return True
    except ModuleNotFoundError:
        logger.error(PYGAME_INSTALL_MESSAGE)
        return False


def _initialize_pygame():
    """
    Initialize the pygame library.
    
    Raises:
        RuntimeError: If pygame initialization fails.
    """
    try:
        import pygame
        pygame.init()
    except Exception as e:
        logger.error(f"Failed to initialize pygame: {e}")
        raise RuntimeError("Pygame initialization failed") from e


def _run_game():
    """
    Create and run the game instance.
    
    Raises:
        ImportError: If game module cannot be imported.
        Exception: If game execution fails.
    """
    try:
        from game import Game
        game = Game()
        game.run()
    except ImportError as e:
        logger.error(f"Failed to import game module: {e}")
        raise
    except Exception as e:
        logger.error(f"Game execution failed: {e}")
        raise


def _cleanup_pygame():
    """
    Clean up pygame resources.
    
    Safely quits pygame, logging any errors that occur.
    """
    try:
        import pygame
        pygame.quit()
        logger.info("Pygame cleaned up successfully")
    except Exception as e:
        logger.warning(f"Error during pygame cleanup: {e}")


def main():
    """
    Main entry point for the Space Invaders game.
    
    Handles pygame dependency checking, initialization, game execution,
    and cleanup. Gracefully handles missing pygame dependency.
    """
    if not _check_pygame_availability():
        return

    try:
        _initialize_pygame()
        _run_game()
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        _cleanup_pygame()


if __name__ == "__main__":
    main()