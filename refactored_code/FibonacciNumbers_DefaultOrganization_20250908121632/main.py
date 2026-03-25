import tkinter as tk
import logging
from gui import FibonacciApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_root_window() -> tk.Tk:
    """
    Create and configure the main Tkinter root window.
    
    Returns:
        tk.Tk: The configured root window instance.
    """
    root = tk.Tk()
    logger.debug("Root window created successfully")
    return root


def initialize_application(root: tk.Tk) -> FibonacciApp:
    """
    Initialize the Fibonacci application with the given root window.
    
    Args:
        root (tk.Tk): The Tkinter root window instance.
    
    Returns:
        FibonacciApp: The initialized application instance.
    
    Raises:
        Exception: If application initialization fails.
    """
    try:
        app = FibonacciApp(root)
        logger.info("FibonacciApp initialized successfully")
        return app
    except Exception as e:
        logger.error(f"Failed to initialize FibonacciApp: {e}", exc_info=True)
        raise


def main() -> None:
    """
    Create the main window, initialize the application, and start the event loop.
    
    This is the primary entry point for the Fibonacci Generator GUI application.
    """
    try:
        root = create_root_window()
        initialize_application(root)
        logger.info("Starting application event loop")
        root.mainloop()
    except Exception as e:
        logger.critical(f"Application startup failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()