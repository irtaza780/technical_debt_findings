import json
import logging
import os
from typing import Any, Callable, Dict

from tkinter import filedialog, messagebox

# Constants
DEFAULT_ENCODING = "utf-8"
JSON_INDENT = 2
JSON_FILE_EXTENSION = ".json"
JSON_FILE_FILTER = [("JSON files", "*.json"), ("All files", "*.*")]

# Configure logging
logger = logging.getLogger(__name__)


def _get_file_dialog_path(
    dialog_type: str,
    title: str,
) -> str:
    """
    Open a file dialog and return the selected file path.

    Args:
        dialog_type: Either "save" or "open" to determine which dialog to show.
        title: The title text for the dialog window.

    Returns:
        The selected file path, or an empty string if cancelled.
    """
    if dialog_type == "save":
        return filedialog.asksaveasfilename(
            title=title,
            defaultextension=JSON_FILE_EXTENSION,
            filetypes=JSON_FILE_FILTER,
        )
    else:
        return filedialog.askopenfilename(
            title=title,
            defaultextension=JSON_FILE_EXTENSION,
            filetypes=JSON_FILE_FILTER,
        )


def _load_json_from_file(file_path: str) -> Dict[str, Any]:
    """
    Load and parse JSON data from a file.

    Args:
        file_path: Path to the JSON file to read.

    Returns:
        Parsed JSON data as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        IOError: If there is an error reading the file.
    """
    with open(file_path, "r", encoding=DEFAULT_ENCODING) as f:
        return json.load(f)


def _save_json_to_file(file_path: str, data: Dict[str, Any]) -> None:
    """
    Write JSON data to a file.

    Args:
        file_path: Path where the JSON file will be saved.
        data: Dictionary to serialize and save.

    Raises:
        IOError: If there is an error writing to the file.
        TypeError: If the data contains non-serializable objects.
    """
    with open(file_path, "w", encoding=DEFAULT_ENCODING) as f:
        json.dump(data, f, indent=JSON_INDENT)


def save_game_dialog(data_provider_callable: Callable[[], Dict[str, Any]]) -> None:
    """
    Open a Save As dialog and save the session JSON provided by data_provider_callable().

    Args:
        data_provider_callable: A callable that returns a dictionary of game data to save.
    """
    file_path = _get_file_dialog_path("save", "Save Game")
    if not file_path:
        logger.info("Save dialog cancelled by user")
        return

    try:
        game_data = data_provider_callable()
        _save_json_to_file(file_path, game_data)
        file_name = os.path.basename(file_path)
        messagebox.showinfo("Saved", f"Game saved to:\n{file_name}")
        logger.info(f"Game successfully saved to {file_path}")
    except (IOError, TypeError, json.JSONDecodeError) as e:
        error_message = f"Failed to save game:\n{e}"
        messagebox.showerror("Error", error_message)
        logger.error(error_message, exc_info=True)


def load_game_dialog(loader_callable: Callable[[Dict[str, Any]], None]) -> bool:
    """
    Open an Open dialog, read JSON, and pass it to loader_callable(data).

    Args:
        loader_callable: A callable that accepts the loaded game data dictionary.

    Returns:
        True if a game was successfully loaded, False if the user cancelled or an error occurred.
    """
    file_path = _get_file_dialog_path("open", "Load Game")
    if not file_path:
        logger.info("Load dialog cancelled by user")
        return False

    try:
        game_data = _load_json_from_file(file_path)
        loader_callable(game_data)
        file_name = os.path.basename(file_path)
        messagebox.showinfo("Loaded", f"Game loaded from:\n{file_name}")
        logger.info(f"Game successfully loaded from {file_path}")
        return True
    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        error_message = f"Failed to load game:\n{e}"
        messagebox.showerror("Error", error_message)
        logger.error(error_message, exc_info=True)
        return False