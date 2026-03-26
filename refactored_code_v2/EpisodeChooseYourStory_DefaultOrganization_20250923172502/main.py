import tkinter as tk
import logging
from gui import StoryApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Entry point for the interactive storytelling game.
    
    Initializes and launches the GUI application window.
    Handles application startup and lifecycle management.
    """
    try:
        logger.info("Starting interactive storytelling game application")
        app = StoryApp()
        app.mainloop()
        logger.info("Application closed successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()