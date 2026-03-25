import logging
from typing import Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# WINDOW CONFIGURATION
# ============================================================================

WINDOW_TITLE = "Simple Space Invaders"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
TARGET_FPS = 60

# ============================================================================
# COLOR DEFINITIONS (RGB tuples)
# ============================================================================

COLOR_BLACK = (0, 0, 0)
COLOR_DARK_GRAY = (30, 30, 30)
COLOR_WHITE = (240, 240, 240)
COLOR_GREEN = (50, 220, 120)
COLOR_YELLOW = (255, 235, 59)
COLOR_RED = (230, 70, 70)
COLOR_CYAN = (50, 200, 220)

ALIEN_COLOR_PALETTE = [
    (120, 200, 255),
    (80, 170, 240),
    (160, 240, 160),
    (240, 200, 120),
    (240, 120, 160),
]

# ============================================================================
# PLAYER CONFIGURATION
# ============================================================================

PLAYER_MOVEMENT_SPEED = 6
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 30
PLAYER_BOTTOM_OFFSET = 60  # Distance from bottom edge of screen
PLAYER_INITIAL_LIVES = 3
PLAYER_INVULNERABILITY_DURATION_MS = 1200

# ============================================================================
# PLAYER WEAPON CONFIGURATION
# ============================================================================

BULLET_MOVEMENT_SPEED = -10  # Negative value moves upward
BULLET_WIDTH = 4
BULLET_HEIGHT = 14
BULLET_FIRE_COOLDOWN_MS = 300  # Milliseconds between consecutive shots

# ============================================================================
# ALIEN CONFIGURATION
# ============================================================================

ALIEN_WIDTH = 40
ALIEN_HEIGHT = 28
ALIEN_GRID_COLUMNS = 10
ALIEN_GRID_ROWS = 5
ALIEN_HORIZONTAL_SPACING = 16
ALIEN_VERTICAL_SPACING = 16
ALIEN_FLEET_MARGIN_X = 30
ALIEN_FLEET_TOP_OFFSET = 60

# ============================================================================
# ALIEN FLEET MOVEMENT CONFIGURATION
# ============================================================================

ALIEN_FLEET_INITIAL_SPEED = 1.2  # Pixels per frame
ALIEN_FLEET_SPEED_MULTIPLIER = 1.06  # Applied each time fleet drops
ALIEN_FLEET_DROP_DISTANCE = 18  # Pixels to drop when hitting screen edge

# ============================================================================
# USER INTERFACE CONFIGURATION
# ============================================================================

POINTS_PER_ALIEN_DESTROYED = 10
FONT_SIZE_LARGE = 48
FONT_SIZE_HUD = 24
FONT_SIZE_SMALL = 18

# ============================================================================
# DERIVED CONSTANTS (calculated from base constants)
# ============================================================================

PLAYER_SPAWN_Y = WINDOW_HEIGHT - PLAYER_BOTTOM_OFFSET


def get_window_dimensions() -> Tuple[int, int]:
    """
    Retrieve the game window dimensions.

    Returns:
        Tuple[int, int]: A tuple of (width, height) in pixels.
    """
    return (WINDOW_WIDTH, WINDOW_HEIGHT)


def get_player_spawn_position() -> Tuple[int, int]:
    """
    Calculate the initial spawn position for the player.

    Returns:
        Tuple[int, int]: A tuple of (x, y) coordinates for player spawn.
    """
    player_x = (WINDOW_WIDTH - PLAYER_WIDTH) // 2
    return (player_x, PLAYER_SPAWN_Y)


def get_alien_fleet_grid_dimensions() -> Tuple[int, int]:
    """
    Retrieve the dimensions of the alien fleet grid.

    Returns:
        Tuple[int, int]: A tuple of (columns, rows) in the alien grid.
    """
    return (ALIEN_GRID_COLUMNS, ALIEN_GRID_ROWS)


def validate_configuration() -> bool:
    """
    Validate that all configuration values are within acceptable ranges.

    Returns:
        bool: True if all configuration values are valid, False otherwise.

    Raises:
        ValueError: If any critical configuration value is invalid.
    """
    validation_checks = [
        (WINDOW_WIDTH > 0, "Window width must be positive"),
        (WINDOW_HEIGHT > 0, "Window height must be positive"),
        (TARGET_FPS > 0, "Target FPS must be positive"),
        (PLAYER_WIDTH > 0 and PLAYER_HEIGHT > 0, "Player dimensions must be positive"),
        (PLAYER_INITIAL_LIVES > 0, "Player lives must be positive"),
        (ALIEN_GRID_COLUMNS > 0 and ALIEN_GRID_ROWS > 0, "Alien grid dimensions must be positive"),
        (ALIEN_FLEET_INITIAL_SPEED > 0, "Alien fleet speed must be positive"),
        (ALIEN_FLEET_SPEED_MULTIPLIER > 1.0, "Fleet speed multiplier must be greater than 1.0"),
    ]

    for condition, error_message in validation_checks:
        if not condition:
            logger.error(f"Configuration validation failed: {error_message}")
            raise ValueError(error_message)

    logger.info("Configuration validation passed")
    return True