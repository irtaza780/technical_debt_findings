import logging
from enum import Enum
from typing import Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# App metadata
WINDOW_TITLE = "Tic-Tac-Toe"
APP_VERSION = "1.0.0"

# Game symbols and dimensions
GRID_SIZE = 3
SYMBOL_X = 'X'
SYMBOL_O = 'O'
EMPTY_CELL = ''

# Font sizes (in points)
FONT_SIZE_CELL = 32
FONT_SIZE_STATUS = 14
FONT_SIZE_CONTROL = 12

# Font family
FONT_FAMILY = 'Helvetica'

# Color palette
class ColorScheme(Enum):
    """Enumeration of color values used throughout the application."""
    BACKGROUND = '#f7f7f7'
    GRID_BACKGROUND = '#f7f7f7'
    BUTTON_BACKGROUND = '#ffffff'
    BUTTON_FOREGROUND = '#222222'
    BUTTON_DISABLED_FOREGROUND = '#9e9e9e'
    PLAYER_X_FOREGROUND = '#e53935'  # Red for X
    PLAYER_O_FOREGROUND = '#1e88e5'  # Blue for O
    WINNING_HIGHLIGHT = '#ffeb3b'    # Yellow highlight for winning cells
    STATUS_FOREGROUND = '#222222'


def get_color(color_name: str) -> str:
    """
    Retrieve a color value by name from the color scheme.
    
    Args:
        color_name: The name of the color to retrieve (e.g., 'background', 'x_fg').
    
    Returns:
        The hex color code as a string.
    
    Raises:
        ValueError: If the color name is not found in the color scheme.
    """
    color_mapping = {
        'bg': ColorScheme.BACKGROUND.value,
        'grid_bg': ColorScheme.GRID_BACKGROUND.value,
        'button_bg': ColorScheme.BUTTON_BACKGROUND.value,
        'button_fg': ColorScheme.BUTTON_FOREGROUND.value,
        'button_disabled_fg': ColorScheme.BUTTON_DISABLED_FOREGROUND.value,
        'x_fg': ColorScheme.PLAYER_X_FOREGROUND.value,
        'o_fg': ColorScheme.PLAYER_O_FOREGROUND.value,
        'highlight': ColorScheme.WINNING_HIGHLIGHT.value,
        'status_fg': ColorScheme.STATUS_FOREGROUND.value,
    }
    
    if color_name not in color_mapping:
        logger.error(f"Color '{color_name}' not found in color scheme")
        raise ValueError(f"Unknown color name: {color_name}")
    
    return color_mapping[color_name]


def get_font(font_type: str) -> Tuple[str, int, str]:
    """
    Retrieve a font specification by type.
    
    Args:
        font_type: The type of font to retrieve ('cell', 'status', or 'control').
    
    Returns:
        A tuple of (font_family, font_size, font_weight).
    
    Raises:
        ValueError: If the font type is not recognized.
    """
    font_specs = {
        'cell': (FONT_FAMILY, FONT_SIZE_CELL, 'bold'),
        'status': (FONT_FAMILY, FONT_SIZE_STATUS, 'normal'),
        'control': (FONT_FAMILY, FONT_SIZE_CONTROL, 'normal'),
    }
    
    if font_type not in font_specs:
        logger.error(f"Font type '{font_type}' not found in font specifications")
        raise ValueError(f"Unknown font type: {font_type}")
    
    return font_specs[font_type]


# Legacy dictionary interfaces for backward compatibility
COLORS: Dict[str, str] = {
    'bg': ColorScheme.BACKGROUND.value,
    'grid_bg': ColorScheme.GRID_BACKGROUND.value,
    'button_bg': ColorScheme.BUTTON_BACKGROUND.value,
    'button_fg': ColorScheme.BUTTON_FOREGROUND.value,
    'button_disabled_fg': ColorScheme.BUTTON_DISABLED_FOREGROUND.value,
    'x_fg': ColorScheme.PLAYER_X_FOREGROUND.value,
    'o_fg': ColorScheme.PLAYER_O_FOREGROUND.value,
    'highlight': ColorScheme.WINNING_HIGHLIGHT.value,
    'status_fg': ColorScheme.STATUS_FOREGROUND.value,
}

FONTS: Dict[str, Tuple[str, int, str]] = {
    'cell': (FONT_FAMILY, FONT_SIZE_CELL, 'bold'),
    'status': (FONT_FAMILY, FONT_SIZE_STATUS, 'normal'),
    'control': (FONT_FAMILY, FONT_SIZE_CONTROL, 'normal'),
}