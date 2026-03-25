import json
import logging
import os
from typing import Any, Callable, Dict

from tkinter import filedialog, messagebox

# Constants
DEFAULT_FILE_EXTENSION = ".json"
FILE_TYPES = [("JSON files", "*.json"), ("All files", "*.*")]
ENCODING = "utf-8"
JSON_INDENT = 2

# Configure logging
logger = logging.getLogger(__name__)


def _get_file_path_from_dialog(
    dialog_type: str, title: str
) -> str:
    """
    Open a file dialog and return the selected file path.
    
    Args:
        dialog_type: Either "save" or "open" to determine dialog type.
        title: The title to display in the dialog.
    
    Returns:
        The selected file path, or empty string if cancelled.
    """
    if dialog_type == "save":
        return filedialog.asksaveasfilename(
            title=title,
            defaultextension=DEFAULT_FILE_EXTENSION,
            filetypes=FILE_TYPES,
        )
    elif dialog_type == "open":
        return filedialog.askopenfilename(
            title=title,
            defaultextension=DEFAULT_FILE_EXTENSION,
            filetypes=FILE_TYPES,
        )
    return ""


def _write_json_to_file(file_path: str, data: Dict[str, Any]) -> None:
    """
    Write data to a JSON file.
    
    Args:
        file_path: Path where the JSON file will be written.
        data: Dictionary to serialize and write.
    
    Raises:
        IOError: If file writing fails.
        json.JSONDecodeError: If data cannot be serialized to JSON.
    """
    with open(file_path, "w", encoding=ENCODING) as f:
        json.dump(data, f, indent=JSON_INDENT)
    logger.info(f"Successfully wrote JSON to {file_path}")


def _read_json_from_file(file_path: str) -> Dict[str, Any]:
    """
    Read and parse JSON data from a file.
    
    Args:
        file_path: Path to the JSON file to read.
    
    Returns:
        Parsed JSON data as a dictionary.
    
    Raises:
        IOError: If file reading fails.
        json.JSONDecodeError: If file content is not valid JSON.
    """
    with open(file_path, "r", encoding=ENCODING) as f:
        data: Dict[str, Any] = json.load(f)
    logger.info(f"Successfully read JSON from {file_path}")
    return data


def save_game_dialog(data_provider_callable: Callable[[], Dict[str, Any]]) -> None:
    """
    Open a Save As dialog and save the session JSON provided by data_provider_callable().
    
    Args:
        data_provider_callable: A callable that returns a dictionary to be saved.
    """
    file_path = _get_file_path_from_dialog("save", "Save Game")
    if not file_path:
        logger.debug("Save dialog cancelled by user")
        return

    try:
        data = data_provider_callable()
        _write_json_to_file(file_path, data)
        messagebox.showinfo(
            "Saved", f"Game saved to:\n{os.path.basename(file_path)}"
        )
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Failed to save game: {e}")
        messagebox.showerror("Error", f"Failed to save game:\n{e}")
    except Exception as e:
        logger.error(f"Unexpected error during save: {e}")
        messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")


def load_game_dialog(loader_callable: Callable[[Dict[str, Any]], None]) -> bool:
    """
    Open an Open dialog, read JSON, and pass it to loader_callable(data).
    
    Args:
        loader_callable: A callable that accepts the loaded data dictionary.
    
    Returns:
        True if a game was successfully loaded, False if the user cancelled or an error occurred.
    """
    file_path = _get_file_path_from_dialog("open", "Load Game")
    if not file_path:
        logger.debug("Load dialog cancelled by user")
        return False

    try:
        data = _read_json_from_file(file_path)
        loader_callable(data)
        messagebox.showinfo(
            "Loaded", f"Game loaded from:\n{os.path.basename(file_path)}"
        )
        return True
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load game: {e}")
        messagebox.showerror("Error", f"Failed to load game:\n{e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during load: {e}")
        messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
        return False