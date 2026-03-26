import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PYGAME_INSTALL_MESSAGE = "Pygame is required to run this game. Please install it with:\n  pip install pygame"


def _validate_pygame_installation():
    """
    Validate that pygame is installed and available.
    
    Returns:
        module: The pygame module if available.
        
    Raises:
        ImportError: If pygame cannot be imported.
    """
    try:
        import pygame
        return pygame
    except ImportError as e:
        logger.error(PYGAME_INSTALL_MESSAGE)
        raise ImportError(PYGAME_INSTALL_MESSAGE) from e


def _import_game_class():
    """
    Import and return the Game class.
    
    Returns:
        class: The Game class from the game module.
    """
    from game import Game
    return Game


def _run_game_safely(game_instance, pygame_module):
    """
    Execute the game loop with proper cleanup.
    
    Args:
        game_instance: An instance of the Game class.
        pygame_module: The pygame module for cleanup.
        
    Raises:
        Exception: Any exception raised during game execution.
    """
    try:
        game_instance.run()
    finally:
        # Ensure pygame resources are properly released
        pygame_module.quit()
        logger.info("Game closed and pygame resources released.")


def main():
    """
    Entry point for the Pong game application.
    
    Initializes pygame, creates a Game instance, and runs the game loop
    with proper error handling and resource cleanup.
    """
    try:
        pygame = _validate_pygame_installation()
        Game = _import_game_class()
        
        game = Game()
        _run_game_safely(game, pygame)
        
    except ImportError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()