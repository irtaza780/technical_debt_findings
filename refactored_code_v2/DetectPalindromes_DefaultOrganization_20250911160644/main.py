import sys
import logging
from gui_app import PalindromeGUI

# Application configuration constants
APP_TITLE = "Palindrome Detector"
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def configure_window(app):
    """
    Configure the main application window with title and minimum size.
    
    Args:
        app (PalindromeGUI): The GUI application instance to configure.
    """
    app.title(APP_TITLE)
    app.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
    logger.info(f"Window configured: {APP_TITLE} ({MIN_WINDOW_WIDTH}x{MIN_WINDOW_HEIGHT})")


def main():
    """
    Main entry point for the Palindrome Detector GUI application.
    
    Initializes the GUI application, configures the window, and starts the event loop.
    """
    try:
        logger.info("Starting Palindrome Detector application")
        app = PalindromeGUI()
        configure_window(app)
        app.mainloop()
        logger.info("Application closed successfully")
    except ImportError as e:
        logger.error(f"Failed to import required module: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()