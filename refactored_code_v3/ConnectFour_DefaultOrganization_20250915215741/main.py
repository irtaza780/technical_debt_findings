import tkinter as tk
import logging
from gui import ConnectFourGUI
from game import ConnectFourGame

# Game configuration constants
GAME_ROWS = 6
GAME_COLS = 7
WINDOW_TITLE = "Connect Four - ChatDev"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_game_window() -> tk.Tk:
    """
    Create and configure the root Tk window.
    
    Returns:
        tk.Tk: Configured root window instance.
    """
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    logger.info("Game window initialized with title: %s", WINDOW_TITLE)
    return root


def initialize_game_logic() -> ConnectFourGame:
    """
    Create and initialize the game logic engine.
    
    Returns:
        ConnectFourGame: Initialized game instance with configured board dimensions.
    """
    game = ConnectFourGame(rows=GAME_ROWS, cols=GAME_COLS)
    logger.info("Game logic initialized with %d rows and %d columns", GAME_ROWS, GAME_COLS)
    return game


def initialize_gui(root: tk.Tk, game: ConnectFourGame) -> ConnectFourGUI:
    """
    Create and initialize the GUI application.
    
    Args:
        root (tk.Tk): The root window instance.
        game (ConnectFourGame): The game logic instance.
    
    Returns:
        ConnectFourGUI: Initialized GUI instance.
    """
    app = ConnectFourGUI(root, game)
    # Give focus to the column entry for immediate typing
    app.focus_column_entry()
    logger.info("GUI initialized and focus set to column entry")
    return app


def main() -> None:
    """
    Launch the Connect Four GUI application.
    
    Initializes the game window, game logic, and GUI components,
    then starts the main event loop.
    """
    try:
        root = initialize_game_window()
        game = initialize_game_logic()
        initialize_gui(root, game)
        logger.info("Starting Connect Four application event loop")
        root.mainloop()
    except Exception as e:
        logger.error("Failed to start Connect Four application: %s", str(e), exc_info=True)
        raise


if __name__ == "__main__":
    main()