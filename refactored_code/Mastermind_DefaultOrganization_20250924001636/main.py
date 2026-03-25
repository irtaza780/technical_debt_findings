import tkinter as tk
import logging
from gui import MastermindGUI

# Window configuration constants
WINDOW_TITLE = "Mastermind - Code Breaking Game"
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 760
MIN_WINDOW_WIDTH = 560
MIN_WINDOW_HEIGHT = 600

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _configure_window(root: tk.Tk) -> None:
    """
    Configure the root window with title, size, and minimum dimensions.
    
    Args:
        root: The Tkinter root window to configure.
    """
    root.title(WINDOW_TITLE)
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
    logger.info("Window configured with title and dimensions")


def main() -> None:
    """
    Initialize and launch the Mastermind game application.
    
    Creates the root Tkinter window, configures it, initializes the GUI,
    and starts the main event loop.
    """
    try:
        root = tk.Tk()
        _configure_window(root)
        
        app = MastermindGUI(root)
        logger.info("Mastermind GUI initialized successfully")
        
        root.mainloop()
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()