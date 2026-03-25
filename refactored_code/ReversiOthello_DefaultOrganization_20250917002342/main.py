import tkinter as tk
import logging
from gui import ReversiGUI

# Window configuration constants
WINDOW_TITLE = "Reversi (Othello)"
WINDOW_MIN_WIDTH = 760
WINDOW_MIN_HEIGHT = 700

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def configure_root_window(root: tk.Tk) -> None:
    """
    Configure the Tkinter root window with title and minimum size constraints.
    
    Args:
        root: The Tkinter root window to configure.
    """
    root.title(WINDOW_TITLE)
    root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
    logger.debug("Root window configured with title and minimum size")


def initialize_application(root: tk.Tk) -> ReversiGUI:
    """
    Initialize the Reversi GUI application.
    
    Args:
        root: The Tkinter root window.
        
    Returns:
        The initialized ReversiGUI instance.
    """
    try:
        app = ReversiGUI(root)
        logger.info("Reversi GUI application initialized successfully")
        return app
    except Exception as e:
        logger.error(f"Failed to initialize Reversi GUI: {e}", exc_info=True)
        raise


def main() -> None:
    """
    Create the Tk root window and start the Reversi GUI application.
    
    This is the main entry point for the application. It sets up the window,
    initializes the GUI, and starts the event loop.
    """
    try:
        root = tk.Tk()
        configure_root_window(root)
        initialize_application(root)
        logger.info("Starting Reversi application event loop")
        root.mainloop()
    except Exception as e:
        logger.critical(f"Fatal error in main application: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()