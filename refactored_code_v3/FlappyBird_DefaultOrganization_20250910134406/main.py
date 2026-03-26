import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PYGAME_INSTALL_MESSAGE = "Pygame is not installed. Please install it with:\n  pip install pygame"
SDL_VIDEODRIVER_ENV_VAR = "SDL_VIDEODRIVER"
DISPLAY_ENV_VAR = "DISPLAY"
DUMMY_VIDEO_DRIVER = "dummy"


def _check_pygame_availability() -> bool:
    """
    Check if pygame is installed and available.
    
    Returns:
        bool: True if pygame is available, False otherwise.
    """
    try:
        import pygame  # noqa: F401
        return True
    except ModuleNotFoundError:
        logger.error(PYGAME_INSTALL_MESSAGE)
        return False


def _configure_headless_environment() -> None:
    """
    Configure SDL video driver for headless environments.
    
    Sets SDL_VIDEODRIVER to 'dummy' if running in a headless environment
    (no display and no explicit video driver configured).
    """
    has_video_driver = os.environ.get(SDL_VIDEODRIVER_ENV_VAR) is not None
    has_display = os.environ.get(DISPLAY_ENV_VAR) is not None
    
    if not has_video_driver and not has_display:
        os.environ[SDL_VIDEODRIVER_ENV_VAR] = DUMMY_VIDEO_DRIVER
        logger.debug("Configured dummy video driver for headless environment")


def _run_game() -> None:
    """
    Initialize and run the game instance.
    
    Raises:
        SystemExit: When the user closes the game window.
        Exception: Any unexpected errors during game execution.
    """
    from game import Game
    
    _configure_headless_environment()
    game = Game()
    game.run()


def main() -> None:
    """
    Main entry point for the Flappy Bird clone application.
    
    Checks for pygame availability, configures the environment,
    creates a Game instance, and starts the main loop.
    Handles graceful exit on window close and logs unexpected errors.
    """
    if not _check_pygame_availability():
        return
    
    try:
        _run_game()
    except SystemExit:
        # Allow clean exit on window close
        logger.info("Game closed by user")
    except Exception as exc:
        logger.exception("Unexpected error during game execution: %s", exc)
        raise


if __name__ == "__main__":
    main()