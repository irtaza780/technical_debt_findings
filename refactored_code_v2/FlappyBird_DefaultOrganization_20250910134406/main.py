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
DUMMY_VIDEODRIVER = "dummy"


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
    (e.g., CI/CD pipeline) where no display is available.
    """
    has_video_driver = os.environ.get(SDL_VIDEODRIVER_ENV_VAR) is not None
    has_display = os.environ.get(DISPLAY_ENV_VAR) is not None
    
    # Configure dummy driver only if no display infrastructure is detected
    if not has_video_driver and not has_display:
        os.environ[SDL_VIDEODRIVER_ENV_VAR] = DUMMY_VIDEODRIVER
        logger.debug("Configured dummy SDL video driver for headless environment")


def _run_game() -> None:
    """
    Initialize and run the game instance.
    
    Raises:
        SystemExit: When the game window is closed normally.
        Exception: For unexpected runtime errors during game execution.
    """
    from game import Game
    
    game = Game()
    game.run()


def main() -> None:
    """
    Main entry point for the Flappy Bird clone application.
    
    Handles pygame dependency verification, headless environment configuration,
    and graceful error handling for the game loop.
    """
    if not _check_pygame_availability():
        return
    
    _configure_headless_environment()
    
    try:
        _run_game()
    except SystemExit:
        # Allow clean exit on window close
        logger.info("Game closed normally")
    except Exception as exc:
        logger.exception("Unexpected error during game execution: %s", exc)
        raise


if __name__ == "__main__":
    main()