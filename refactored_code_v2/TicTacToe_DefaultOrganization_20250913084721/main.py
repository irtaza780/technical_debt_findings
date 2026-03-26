import tkinter as tk
import logging
from gui import TicTacToeGUI
from constants import WINDOW_TITLE, COLORS, WINDOW_RESIZABLE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def configure_root_window(root: tk.Tk) -> None:
    """
    Configure the root Tkinter window with title, background, and resize settings.
    
    Args:
        root: The root Tkinter window to configure.
    """
    root.title(WINDOW_TITLE)
    root.configure(bg=COLORS['bg'])
    root.resizable(WINDOW_RESIZABLE, WINDOW_RESIZABLE)
    logger.info(f"Root window configured with title: {WINDOW_TITLE}")


def initialize_application(root: tk.Tk) -> TicTacToeGUI:
    """
    Initialize the Tic-Tac-Toe GUI application.
    
    Args:
        root: The root Tkinter window.
        
    Returns:
        TicTacToeGUI: The initialized GUI application instance.
    """
    app = TicTacToeGUI(root)
    app.build_ui()
    logger.info("Application GUI initialized and built")
    return app


def main() -> None:
    """
    Start the Tic-Tac-Toe GUI application.
    
    Creates the root Tkinter window, configures it, initializes the GUI,
    and starts the event loop.
    """
    try:
        root = tk.Tk()
        configure_root_window(root)
        initialize_application(root)
        logger.info("Starting Tic-Tac-Toe application event loop")
        root.mainloop()
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()