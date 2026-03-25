import sys
import logging
from gui_app import PalindromeGUI

# Configuration constants
WINDOW_TITLE = "Palindrome Detector"
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def configure_window(window):
    """
    Configure the main application window with title and minimum size.
    
    Args:
        window (PalindromeGUI): The GUI window instance to configure.
    """
    window.title(WINDOW_TITLE)
    window.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
    logger.info(f"Window configured: {WINDOW_TITLE} ({WINDOW_MIN_WIDTH}x{WINDOW_MIN_HEIGHT})")


def main():
    """
    Main entry point for the Palindrome Detector GUI application.
    
    Initializes the GUI window, configures it, and starts the event loop.
    """
    try:
        app = PalindromeGUI()
        configure_window(app)
        logger.info("Starting Palindrome Detector application")
        app.mainloop()
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()