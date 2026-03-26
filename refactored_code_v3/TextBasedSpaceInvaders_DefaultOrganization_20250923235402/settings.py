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
PLAYER_BOTTOM_OFFSET = 60
PLAYER_INITIAL_LIVES = 3
PLAYER_INVULNERABILITY_DURATION_MS = 1200

# ============================================================================
# PROJECTILE CONFIGURATION
# ============================================================================

BULLET_VELOCITY = -10
BULLET_WIDTH = 4
BULLET_HEIGHT = 14
BULLET_FIRE_COOLDOWN_MS = 300

# ============================================================================
# ALIEN FLEET CONFIGURATION
# ============================================================================

ALIEN_WIDTH = 40
ALIEN_HEIGHT = 28
ALIEN_GRID_COLUMNS = 10
ALIEN_GRID_ROWS = 5
ALIEN_HORIZONTAL_SPACING = 16
ALIEN_VERTICAL_SPACING = 16
FLEET_BOUNDARY_MARGIN_X = 30
FLEET_TOP_MARGIN = 60
FLEET_INITIAL_SPEED = 1.2
FLEET_ACCELERATION_FACTOR = 1.06
FLEET_VERTICAL_DROP_DISTANCE = 18

# ============================================================================
# GAMEPLAY CONFIGURATION
# ============================================================================

POINTS_PER_ALIEN_DESTROYED = 10

# ============================================================================
# UI CONFIGURATION
# ============================================================================

FONT_SIZE_TITLE = 48
FONT_SIZE_HUD = 24
FONT_SIZE_SMALL = 18


def get_window_dimensions() -> Tuple[int, int]:
    """
    Retrieve the game window dimensions.

    Returns:
        Tuple[int, int]: A tuple of (width, height) in pixels.
    """
    return (WINDOW_WIDTH, WINDOW_HEIGHT)


def get_player_spawn_position() -> Tuple[int, int]:
    """
    Calculate the initial player spawn position (centered horizontally, near bottom).

    Returns:
        Tuple[int, int]: A tuple of (x, y) coordinates for player spawn.
    """
    player_x = (WINDOW_WIDTH - PLAYER_WIDTH) // 2
    player_y = WINDOW_HEIGHT - PLAYER_BOTTOM_OFFSET
    return (player_x, player_y)


def get_alien_color(alien_index: int) -> Tuple[int, int, int]:
    """
    Retrieve a color from the alien palette based on index.

    Args:
        alien_index (int): The index of the alien (used for cycling through colors).

    Returns:
        Tuple[int, int, int]: An RGB color tuple.
    """
    color_index = alien_index % len(ALIEN_COLOR_PALETTE)
    return ALIEN_COLOR_PALETTE[color_index]


def log_configuration() -> None:
    """
    Log the current game configuration settings for debugging purposes.
    """
    logger.info(f"Game Configuration: {WINDOW_TITLE}")
    logger.info(f"Window: {WINDOW_WIDTH}x{WINDOW_HEIGHT} @ {TARGET_FPS} FPS")
    logger.info(f"Player: Speed={PLAYER_MOVEMENT_SPEED}, Lives={PLAYER_INITIAL_LIVES}")
    logger.info(
        f"Aliens: Grid={ALIEN_GRID_COLUMNS}x{ALIEN_GRID_ROWS}, "
        f"Speed={FLEET_INITIAL_SPEED}"
    )