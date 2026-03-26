import tkinter as tk
import logging
from gui import MonopolyApp

# Configuration constants
WINDOW_TITLE = "Monopoly Go! - Simplified"
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def configure_root_window(root: tk.Tk) -> None:
    """
    Configure the root Tkinter window with title and basic settings.
    
    Args:
        root: The root Tkinter window to configure.
    """
    root.title(WINDOW_TITLE)
    logger.debug("Root window configured with title: %s", WINDOW_TITLE)


def initialize_application(root: tk.Tk) -> MonopolyApp:
    """
    Initialize the Monopoly application and pack it into the root window.
    
    Args:
        root: The root Tkinter window.
        
    Returns:
        MonopolyApp: The initialized Monopoly application instance.
        
    Raises:
        Exception: If application initialization fails.
    """
    try:
        app = MonopolyApp(root)
        app.pack(fill="both", expand=True)
        logger.info("Monopoly application initialized successfully")
        return app
    except Exception as e:
        logger.error("Failed to initialize Monopoly application: %s", str(e))
        raise


def main() -> None:
    """
    Entry point for the Monopoly Go! simplified game application.
    
    Initializes the Tkinter root window, configures it, creates the application,
    and starts the main event loop.
    """
    try:
        root = tk.Tk()
        configure_root_window(root)
        initialize_application(root)
        logger.info("Starting main event loop")
        root.mainloop()
    except Exception as e:
        logger.critical("Application startup failed: %s", str(e))
        raise
    finally:
        logger.info("Application terminated")


if __name__ == "__main__":
    main()