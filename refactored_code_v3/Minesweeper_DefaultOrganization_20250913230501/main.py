import tkinter as tk
import logging
from gui import MinesweeperApp

# Configuration constants
WINDOW_TITLE = "Minesweeper - ChatDev"
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def initialize_window() -> tk.Tk:
    """
    Create and configure the root Tkinter window.
    
    Returns:
        tk.Tk: Configured root window instance.
    """
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    logger.debug("Root window initialized with title: %s", WINDOW_TITLE)
    return root


def initialize_application(root: tk.Tk) -> MinesweeperApp:
    """
    Create and initialize the Minesweeper application.
    
    Args:
        root (tk.Tk): The root Tkinter window.
    
    Returns:
        MinesweeperApp: Initialized Minesweeper application instance.
    """
    app = MinesweeperApp(master=root)
    logger.debug("Minesweeper application initialized")
    return app


def main() -> None:
    """
    Main entry point for the Minesweeper application.
    
    Initializes the Tkinter GUI and starts the main event loop.
    """
    try:
        root = initialize_window()
        app = initialize_application(root)
        logger.info("Starting Minesweeper application")
        app.mainloop()
    except ImportError as e:
        logger.error("Failed to import required module: %s", e)
        raise
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
        raise


if __name__ == "__main__":
    main()