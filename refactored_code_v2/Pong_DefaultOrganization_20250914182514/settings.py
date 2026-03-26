import logging
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GameConfig:
    """
    Global configuration constants for the Pong game.
    
    Centralizes all game settings including screen dimensions, colors,
    gameplay parameters, and control mappings.
    """
    
    # Window settings
    SCREEN_WIDTH = 900
    SCREEN_HEIGHT = 600
    WINDOW_TITLE = "ChatDev Pong - Two Player"
    
    # Colors (R, G, B)
    COLOR_BACKGROUND = (15, 15, 20)
    COLOR_FOREGROUND = (240, 240, 240)
    COLOR_DIMMED = (120, 120, 120)
    COLOR_ACCENT = (200, 80, 80)
    
    # Paddle settings
    PADDLE_WIDTH = 14
    PADDLE_HEIGHT = 100
    PADDLE_SPEED = 500.0  # pixels per second
    
    # Ball settings
    BALL_RADIUS = 10
    BALL_INITIAL_SPEED = 360.0  # pixels per second
    BALL_MAX_SPEED = 900.0
    BALL_ACCELERATION_FACTOR = 1.06  # multiplier applied on paddle hit
    
    # Scoring settings
    WINNING_SCORE = 7
    SERVE_COOLDOWN_MS = 1000  # milliseconds between points
    
    # Frame rate
    FPS = 120
    
    # Font sizes
    SCORE_FONT_SIZE = 64
    INFO_FONT_SIZE = 28
    WIN_FONT_SIZE = 48
    
    # Center line visual settings
    CENTER_DASH_HEIGHT = 18
    CENTER_DASH_GAP = 12


class ControlKey(Enum):
    """
    Enumeration of control key mappings for both players.
    
    Attributes:
        LEFT_UP: Key for left paddle upward movement
        LEFT_DOWN: Key for left paddle downward movement
        RIGHT_UP: Key for right paddle upward movement
        RIGHT_DOWN: Key for right paddle downward movement
    """
    LEFT_UP = "w"
    LEFT_DOWN = "s"
    RIGHT_UP = "up"
    RIGHT_DOWN = "down"


def get_control_mapping():
    """
    Retrieve the complete control key mapping for the game.
    
    Returns:
        dict: Mapping of control actions to their respective keys
    """
    return {
        'left_up': ControlKey.LEFT_UP.value,
        'left_down': ControlKey.LEFT_DOWN.value,
        'right_up': ControlKey.RIGHT_UP.value,
        'right_down': ControlKey.RIGHT_DOWN.value,
    }


def validate_config():
    """
    Validate game configuration values for consistency and correctness.
    
    Raises:
        ValueError: If any configuration value is invalid
    """
    config = GameConfig()
    
    # Validate screen dimensions
    if config.SCREEN_WIDTH <= 0 or config.SCREEN_HEIGHT <= 0:
        raise ValueError("Screen dimensions must be positive integers")
    
    # Validate speeds
    if config.PADDLE_SPEED <= 0:
        raise ValueError("Paddle speed must be positive")
    
    if config.BALL_INITIAL_SPEED <= 0:
        raise ValueError("Ball initial speed must be positive")
    
    if config.BALL_MAX_SPEED < config.BALL_INITIAL_SPEED:
        raise ValueError("Ball max speed must be >= initial speed")
    
    # Validate acceleration factor
    if config.BALL_ACCELERATION_FACTOR <= 1.0:
        raise ValueError("Ball acceleration factor must be > 1.0")
    
    # Validate scoring
    if config.WINNING_SCORE <= 0:
        raise ValueError("Winning score must be positive")
    
    # Validate frame rate
    if config.FPS <= 0:
        raise ValueError("FPS must be positive")
    
    logger.info("Game configuration validated successfully")


if __name__ == "__main__":
    try:
        validate_config()
        logger.info(f"Game initialized with {GameConfig.FPS} FPS")
        logger.info(f"Screen size: {GameConfig.SCREEN_WIDTH}x{GameConfig.SCREEN_HEIGHT}")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise