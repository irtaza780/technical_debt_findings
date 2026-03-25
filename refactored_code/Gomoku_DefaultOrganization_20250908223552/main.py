import logging
import sys
from typing import Type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import fallback strategy for flexible module loading
PREFERRED_IMPORTS = [
    ('gomoku.controller', 'GameController'),
    ('gomoku.view', 'GomokuApp'),
]

FALLBACK_IMPORTS = [
    ('controller', 'GameController'),
    ('view', 'GomokuApp'),
]


def _import_module(module_name: str, class_name: str) -> Type:
    """
    Dynamically import a class from a module.
    
    Args:
        module_name: The name of the module to import from.
        class_name: The name of the class to import.
    
    Returns:
        The imported class.
    
    Raises:
        ModuleNotFoundError: If the module cannot be found.
        AttributeError: If the class does not exist in the module.
    """
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)


def _load_dependencies() -> tuple:
    """
    Load GameController and GomokuApp with fallback strategy.
    
    Attempts to import from the preferred package layout first,
    then falls back to flat-file layout if the package is not found.
    
    Returns:
        A tuple of (GameController, GomokuApp) classes.
    
    Raises:
        ModuleNotFoundError: If neither import strategy succeeds.
    """
    import_strategies = [PREFERRED_IMPORTS, FALLBACK_IMPORTS]
    
    for strategy in import_strategies:
        try:
            loaded_classes = {}
            for module_name, class_name in strategy:
                loaded_classes[class_name] = _import_module(module_name, class_name)
            
            logger.info(f"Successfully loaded modules using strategy: {strategy[0][0]}")
            return loaded_classes['GameController'], loaded_classes['GomokuApp']
        
        except (ModuleNotFoundError, AttributeError) as error:
            logger.debug(f"Import strategy failed: {error}")
            continue
    
    # If all strategies fail, raise an error
    raise ModuleNotFoundError(
        "Could not load GameController and GomokuApp. "
        "Ensure the gomoku package or controller/view modules are available."
    )


def _initialize_game(game_controller_class: Type, gomoku_app_class: Type) -> None:
    """
    Initialize the game controller and view, then start the application.
    
    Args:
        game_controller_class: The GameController class.
        gomoku_app_class: The GomokuApp class.
    """
    logger.info("Initializing game controller and view...")
    
    controller = game_controller_class()
    app = gomoku_app_class(controller)
    controller.attach_view(app)
    
    logger.info("Starting Gomoku application...")
    app.mainloop()


def main() -> None:
    """
    Main entry point for the Gomoku application.
    
    Loads dependencies, initializes the game, and starts the tkinter main loop.
    """
    try:
        game_controller_class, gomoku_app_class = _load_dependencies()
        _initialize_game(game_controller_class, gomoku_app_class)
    except ModuleNotFoundError as error:
        logger.error(f"Failed to start application: {error}")
        sys.exit(1)
    except Exception as error:
        logger.error(f"Unexpected error during application startup: {error}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user.")
        sys.exit(0)