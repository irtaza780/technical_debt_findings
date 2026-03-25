import logging
from enum import Enum
from typing import Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# SCREEN CONFIGURATION
# ============================================================================
SCREEN_WIDTH: int = 900
SCREEN_HEIGHT: int = 600
WINDOW_TITLE: str = "ChatDev Pong - Two Player"
FPS: int = 120

# ============================================================================
# COLOR PALETTE (RGB)
# ============================================================================
class ColorPalette(Enum):
    """Enumeration of all colors used in the Pong game."""
    BACKGROUND = (15, 15, 20)
    FOREGROUND = (240, 240, 240)
    DIMMED = (120, 120, 120)
    ACCENT = (200, 80, 80)


COLOR_BG: Tuple[int, int, int] = ColorPalette.BACKGROUND.value
COLOR_FG: Tuple[int, int, int] = ColorPalette.FOREGROUND.value
COLOR_DIM: Tuple[int, int, int] = ColorPalette.DIMMED.value
COLOR_ACCENT: Tuple[int, int, int] = ColorPalette.ACCENT.value

# ============================================================================
# PADDLE CONFIGURATION
# ============================================================================
PADDLE_WIDTH: int = 14
PADDLE_HEIGHT: int = 100
PADDLE_SPEED: float = 500.0  # pixels per second

# ============================================================================
# BALL CONFIGURATION
# ============================================================================
BALL_RADIUS: int = 10
BALL_START_SPEED: float = 360.0  # initial speed magnitude in pixels per second
BALL_MAX_SPEED: float = 900.0  # maximum achievable ball speed
BALL_SPEEDUP_FACTOR: float = 1.06  # multiplier applied on each paddle hit

# ============================================================================
# GAMEPLAY CONFIGURATION
# ============================================================================
WINNING_SCORE: int = 7
SERVE_COOLDOWN_MS: int = 1000  # milliseconds to wait after scoring before serve

# ============================================================================
# UI FONT SIZES
# ============================================================================
SCORE_FONT_SIZE: int = 64
INFO_FONT_SIZE: int = 28
WIN_FONT_SIZE: int = 48

# ============================================================================
# CENTER LINE VISUAL CONFIGURATION
# ============================================================================
CENTER_DASH_HEIGHT: int = 18
CENTER_DASH_GAP: int = 12

# ============================================================================
# PLAYER CONTROLS
# ============================================================================
class PlayerControls(Enum):
    """Enumeration of keyboard controls for both players."""
    LEFT_UP = "w"
    LEFT_DOWN = "s"
    RIGHT_UP = "up"
    RIGHT_DOWN = "down"


LEFT_UP_KEY: str = PlayerControls.LEFT_UP.value
LEFT_DOWN_KEY: str = PlayerControls.LEFT_DOWN.value
RIGHT_UP_KEY: str = PlayerControls.RIGHT_UP.value
RIGHT_DOWN_KEY: str = PlayerControls.RIGHT_DOWN.value


def validate_configuration() -> None:
    """
    Validate that all configuration values are within acceptable ranges.
    
    Raises:
        ValueError: If any configuration value is invalid.
    """
    if SCREEN_WIDTH <= 0 or SCREEN_HEIGHT <= 0:
        raise ValueError("Screen dimensions must be positive integers")
    
    if FPS <= 0:
        raise ValueError("FPS must be a positive integer")
    
    if PADDLE_SPEED <= 0:
        raise ValueError("Paddle speed must be positive")
    
    if BALL_START_SPEED <= 0 or BALL_MAX_SPEED <= 0:
        raise ValueError("Ball speeds must be positive")
    
    if BALL_SPEEDUP_FACTOR <= 1.0:
        raise ValueError("Ball speedup factor must be greater than 1.0")
    
    if WINNING_SCORE <= 0:
        raise ValueError("Winning score must be positive")
    
    if SERVE_COOLDOWN_MS < 0:
        raise ValueError("Serve cooldown cannot be negative")
    
    logger.info("Configuration validation passed")


if __name__ == "__main__":
    validate_configuration()
    logger.info(f"Pong game configured: {SCREEN_WIDTH}x{SCREEN_HEIGHT} @ {FPS} FPS")