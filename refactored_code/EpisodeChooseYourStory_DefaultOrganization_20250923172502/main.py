import tkinter as tk
import logging
from gui import StoryApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_gui_application():
    """
    Initialize and launch the interactive storytelling game GUI application.
    
    Creates a StoryApp instance and starts the main event loop.
    Handles any initialization errors gracefully.
    """
    try:
        logger.info("Initializing storytelling game application")
        app = StoryApp()
        logger.info("Application initialized successfully, starting main loop")
        app.mainloop()
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise


def main():
    """
    Entry point for the interactive storytelling game.
    
    Initializes and runs the GUI application.
    """
    initialize_gui_application()


if __name__ == "__main__":
    main()