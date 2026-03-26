import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# GEOMETRY AND LAYOUT CONSTANTS
# ============================================================================

BOARD_ROWS = 8
BOARD_COLS = 8
SQUARE_SIZE = 80
BOARD_SIZE = SQUARE_SIZE * BOARD_ROWS
PANEL_HEIGHT = 110
WINDOW_WIDTH = BOARD_SIZE
WINDOW_HEIGHT = BOARD_SIZE + PANEL_HEIGHT
FRAMES_PER_SECOND = 60

# ============================================================================
# COLOR PALETTE CONSTANTS
# ============================================================================

# Background and board colors
BACKGROUND_COLOR = (18, 18, 18)
LIGHT_SQUARE_COLOR = (230, 210, 180)
DARK_SQUARE_COLOR = (139, 69, 19)
BLACK_COLOR = (30, 30, 30)

# Piece and UI highlight colors
RED_COLOR = (220, 50, 50)
KING_INDICATOR_COLOR = (255, 255, 0)
VALID_MOVE_HIGHLIGHT_COLOR = (50, 180, 255)
CAPTURE_HIGHLIGHT_COLOR = (255, 140, 0)

# Text colors
PRIMARY_TEXT_COLOR = (235, 235, 235)
SECONDARY_TEXT_COLOR = (180, 180, 180)

# Status indicator colors
SUCCESS_STATUS_COLOR = (80, 200, 120)
ERROR_STATUS_COLOR = (255, 80, 80)

# Input field colors
INPUT_BACKGROUND_COLOR = (40, 40, 40)
INPUT_BORDER_COLOR = (90, 90, 90)
INPUT_ACTIVE_BORDER_COLOR = (140, 140, 140)


def get_board_dimensions():
    """
    Retrieve the board dimensions.

    Returns:
        tuple: A tuple of (rows, columns) representing the board grid size.
    """
    return (BOARD_ROWS, BOARD_COLS)


def get_window_dimensions():
    """
    Retrieve the window dimensions including the control panel.

    Returns:
        tuple: A tuple of (width, height) representing the total window size.
    """
    return (WINDOW_WIDTH, WINDOW_HEIGHT)


def get_square_size():
    """
    Retrieve the size of a single board square in pixels.

    Returns:
        int: The side length of a square in pixels.
    """
    return SQUARE_SIZE


def get_board_size():
    """
    Retrieve the total board size in pixels (excluding panel).

    Returns:
        int: The side length of the board in pixels.
    """
    return BOARD_SIZE


def get_panel_height():
    """
    Retrieve the height of the control panel.

    Returns:
        int: The height of the panel in pixels.
    """
    return PANEL_HEIGHT


def get_fps():
    """
    Retrieve the target frames per second for the game loop.

    Returns:
        int: The target FPS value.
    """
    return FRAMES_PER_SECOND


def get_color_palette():
    """
    Retrieve the complete color palette used throughout the application.

    Returns:
        dict: A dictionary mapping color names to RGB tuples.
    """
    return {
        'background': BACKGROUND_COLOR,
        'light_square': LIGHT_SQUARE_COLOR,
        'dark_square': DARK_SQUARE_COLOR,
        'black': BLACK_COLOR,
        'red': RED_COLOR,
        'king_indicator': KING_INDICATOR_COLOR,
        'valid_move_highlight': VALID_MOVE_HIGHLIGHT_COLOR,
        'capture_highlight': CAPTURE_HIGHLIGHT_COLOR,
        'primary_text': PRIMARY_TEXT_COLOR,
        'secondary_text': SECONDARY_TEXT_COLOR,
        'success_status': SUCCESS_STATUS_COLOR,
        'error_status': ERROR_STATUS_COLOR,
        'input_background': INPUT_BACKGROUND_COLOR,
        'input_border': INPUT_BORDER_COLOR,
        'input_active_border': INPUT_ACTIVE_BORDER_COLOR,
    }


def get_color(color_name):
    """
    Retrieve a specific color by name from the palette.

    Args:
        color_name (str): The name of the color to retrieve.

    Returns:
        tuple: An RGB color tuple.

    Raises:
        KeyError: If the color name is not found in the palette.
    """
    palette = get_color_palette()
    if color_name not in palette:
        logger.warning(f"Color '{color_name}' not found in palette. Using default.")
        return BACKGROUND_COLOR
    return palette[color_name]