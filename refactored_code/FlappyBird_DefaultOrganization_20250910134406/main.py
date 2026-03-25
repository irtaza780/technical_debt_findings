import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
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


def _configure_video_driver() -> None:
    """
    Configure SDL video driver for headless environments.

    Sets the SDL_VIDEODRIVER to 'dummy' if running in a headless environment
    (no display server and no explicit video driver configured).
    """
    has_video_driver = os.environ.get(SDL_VIDEODRIVER_ENV_VAR) is not None
    has_display = os.environ.get(DISPLAY_ENV_VAR) is not None

    if not has_video_driver and not has_display:
        os.environ[SDL_VIDEODRIVER_ENV_VAR] = DUMMY_VIDEO_DRIVER
        logger.debug(f"Set {SDL_VIDEODRIVER_ENV_VAR} to {DUMMY_VIDEO_DRIVER}")


def _run_game() -> None:
    """
    Initialize and run the game instance.

    Raises:
        SystemExit: When the user closes the game window.
        Exception: Any unexpected errors during game execution.
    """
    from game import Game

    game = Game()
    game.run()


def main() -> None:
    """
    Main entry point for the Flappy Bird clone application.

    Checks for pygame availability, configures the environment for headless
    execution if needed, and starts the game loop. Handles graceful shutdown
    and error reporting.
    """
    if not _check_pygame_availability():
        return

    _configure_video_driver()

    try:
        _run_game()
    except SystemExit:
        # Allow clean exit on window close
        logger.info("Game closed by user")
    except Exception as exc:
        logger.exception(f"Unexpected error during game execution: {exc}")
        raise


if __name__ == "__main__":
    main()