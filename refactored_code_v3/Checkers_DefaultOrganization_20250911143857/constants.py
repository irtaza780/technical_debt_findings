import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# GEOMETRY CONSTANTS
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
# COLOR CONSTANTS
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

# ============================================================================
# DEPRECATED ALIASES (for backward compatibility)
# ============================================================================

BG_COLOR = BACKGROUND_COLOR
LIGHT_COLOR = LIGHT_SQUARE_COLOR
DARK_COLOR = DARK_SQUARE_COLOR
KING_TEXT_COLOR = KING_INDICATOR_COLOR
HILITE_MOVE_COLOR = VALID_MOVE_HIGHLIGHT_COLOR
HILITE_CAPTURE_COLOR = CAPTURE_HIGHLIGHT_COLOR
TEXT_COLOR = PRIMARY_TEXT_COLOR
INFO_TEXT_COLOR = SECONDARY_TEXT_COLOR
STATUS_OK_COLOR = SUCCESS_STATUS_COLOR
STATUS_ERR_COLOR = ERROR_STATUS_COLOR
INPUT_BG_COLOR = INPUT_BACKGROUND_COLOR
INPUT_BORDER_COLOR = INPUT_BORDER_COLOR
INPUT_ACTIVE_BORDER_COLOR = INPUT_ACTIVE_BORDER_COLOR
ROWS = BOARD_ROWS
COLS = BOARD_COLS
WIDTH = WINDOW_WIDTH
HEIGHT = WINDOW_HEIGHT
FPS = FRAMES_PER_SECOND