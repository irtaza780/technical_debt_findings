import logging
import os
import sys
import tkinter as tk
from tkinter import messagebox

from ui import BudgetApp

# Configuration constants
DATA_FILENAME = "budget_data.xlsx"
EXIT_CODE_DEPENDENCY_ERROR = 1
EXIT_CODE_INITIALIZATION_ERROR = 1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_data_file_path() -> str:
    """
    Construct the absolute path to the budget data file.
    
    Returns:
        str: Absolute path to the budget data Excel file.
    """
    current_directory = os.path.abspath(os.getcwd())
    return os.path.join(current_directory, DATA_FILENAME)


def show_error_dialog(title: str, message: str) -> None:
    """
    Display an error dialog to the user.
    
    Args:
        title (str): The title of the error dialog.
        message (str): The error message to display.
    """
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, message)


def handle_import_error(import_error: ImportError) -> None:
    """
    Handle missing dependency errors gracefully.
    
    Args:
        import_error (ImportError): The import error that was raised.
    """
    logger.error(f"Missing required dependency: {import_error}")
    error_message = (
        f"Required package is missing:\n\n{import_error}\n\n"
        "Please install it, e.g.:\n    pip install openpyxl"
    )
    show_error_dialog("Missing dependency", error_message)
    sys.exit(EXIT_CODE_DEPENDENCY_ERROR)


def handle_initialization_error(error: Exception) -> None:
    """
    Handle storage initialization errors gracefully.
    
    Args:
        error (Exception): The exception that was raised during initialization.
    """
    logger.error(f"Failed to initialize storage: {error}")
    error_message = f"Failed to initialize storage:\n{error}"
    show_error_dialog("Error", error_message)
    sys.exit(EXIT_CODE_INITIALIZATION_ERROR)


def initialize_storage(data_file_path: str):
    """
    Initialize the storage system and load the budget model.
    
    Lazy imports ExcelStorage to catch ImportError gracefully if openpyxl
    is not installed.
    
    Args:
        data_file_path (str): Path to the Excel data file.
        
    Returns:
        tuple: A tuple containing (storage, model) objects.
        
    Raises:
        ImportError: If required dependencies are missing.
        Exception: If storage initialization fails.
    """
    from storage import ExcelStorage
    
    storage = ExcelStorage(data_file_path)
    model = storage.load_model()
    logger.info("Storage initialized successfully")
    return storage, model


def launch_application(storage, model) -> None:
    """
    Launch the Budget Tracker GUI application.
    
    Args:
        storage: The storage backend instance.
        model: The budget model instance.
    """
    logger.info("Launching Budget Tracker application")
    app = BudgetApp(model=model, storage=storage)
    app.mainloop()


def main() -> None:
    """
    Main entry point for the Budget Tracker application.
    
    Initializes storage (Excel), loads the budget model, and launches
    the GUI application. Handles errors gracefully with user-friendly
    error dialogs.
    """
    data_file_path = get_data_file_path()
    logger.info(f"Using data file: {data_file_path}")
    
    try:
        storage, model = initialize_storage(data_file_path)
    except ImportError as import_error:
        handle_import_error(import_error)
        return
    except Exception as initialization_error:
        handle_initialization_error(initialization_error)
        return
    
    launch_application(storage, model)


if __name__ == "__main__":
    main()