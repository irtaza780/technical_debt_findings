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
        Exception: If game creation or execution fails.
    """
    from game import Game
    
    game = Game()
    game.run()


def main():
    """
    Main entry point for the Space Invaders game.
    
    Handles pygame dependency checking, initialization, and graceful cleanup.
    Exits with status code 1 if pygame is not available.
    """
    if not _check_pygame_availability():
        sys.exit(1)
    
    try:
        _initialize_pygame()
        _run_game()
    except Exception as e:
        logger.exception(f"An error occurred during game execution: {e}")
        sys.exit(1)
    finally:
        import pygame
        pygame.quit()
        logger.info("Game closed successfully.")


if __name__ == "__main__":
    main()