import logging
import sys
from typing import Type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Module import configuration
PREFERRED_IMPORT_PACKAGE = 'gomoku'
FALLBACK_MODULES = {
    'GameController': 'controller',
    'GomokuApp': 'view'
}


def _import_module_with_fallback(module_name: str, class_name: str) -> Type:
    """
    Attempt to import a class from a package, with fallback to flat-file layout.
    
    Args:
        module_name: The module name to import from (e.g., 'controller', 'view')
        class_name: The class name to import (e.g., 'GameController', 'GomokuApp')
    
    Returns:
        The imported class
    
    Raises:
        ImportError: If the class cannot be imported from either layout
    """
    # Try preferred package layout first
    try:
        package_path = f'{PREFERRED_IMPORT_PACKAGE}.{module_name}'
        module = __import__(package_path, fromlist=[class_name])
        logger.debug(f'Successfully imported {class_name} from {package_path}')
        return getattr(module, class_name)
    except ModuleNotFoundError:
        logger.debug(f'Package layout not found, attempting flat-file layout')
    
    # Fallback to flat-file layout
    try:
        module = __import__(module_name, fromlist=[class_name])
        logger.debug(f'Successfully imported {class_name} from {module_name}')
        return getattr(module, class_name)
    except (ModuleNotFoundError, AttributeError) as error:
        error_message = f'Failed to import {class_name} from {module_name}'
        logger.error(error_message)
        raise ImportError(error_message) from error


def _initialize_game_components() -> tuple:
    """
    Initialize the game controller and view components.
    
    Returns:
        A tuple of (GameController, GomokuApp) instances
    
    Raises:
        ImportError: If required modules cannot be imported
    """
    GameController = _import_module_with_fallback('controller', 'GameController')
    GomokuApp = _import_module_with_fallback('view', 'GomokuApp')
    
    controller = GameController()
    app = GomokuApp(controller)
    controller.attach_view(app)
    
    logger.info('Game components initialized successfully')
    return controller, app


def main() -> None:
    """
    Main entry point for the Gomoku application.
    
    Initializes the game controller and view, then starts the tkinter main loop.
    
    Raises:
        ImportError: If required modules cannot be imported
    """
    try:
        controller, app = _initialize_game_components()
        logger.info('Starting Gomoku application')
        app.mainloop()
    except ImportError as error:
        logger.error(f'Failed to start application: {error}')
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info('Application interrupted by user')
        sys.exit(0)