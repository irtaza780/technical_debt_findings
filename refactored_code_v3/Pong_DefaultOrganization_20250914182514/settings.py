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
    PADDLE_SPEED_PX_PER_SEC = 500.0
    
    # Ball settings
    BALL_RADIUS = 10
    BALL_INITIAL_SPEED_PX_PER_SEC = 360.0
    BALL_MAX_SPEED_PX_PER_SEC = 900.0
    BALL_SPEED_MULTIPLIER_ON_HIT = 1.06
    
    # Scoring settings
    WINNING_SCORE = 7
    SERVE_COOLDOWN_MS = 1000
    
    # Frame rate
    TARGET_FPS = 120
    
    # Font sizes
    SCORE_FONT_SIZE = 64
    INFO_FONT_SIZE = 28
    WIN_FONT_SIZE = 48
    
    # Center line visual settings
    CENTER_DASH_HEIGHT = 18
    CENTER_DASH_GAP = 12


class ControlKey(Enum):
    """
    Enumeration of control keys for player input.
    
    Maps logical control actions to their corresponding keyboard keys.
    """
    LEFT_PADDLE_UP = "w"
    LEFT_PADDLE_DOWN = "s"
    RIGHT_PADDLE_UP = "up"
    RIGHT_PADDLE_DOWN = "down"


def get_control_mapping():
    """
    Retrieve the complete control key mapping for the game.
    
    Returns:
        dict: Mapping of ControlKey enum members to their string values.
    """
    return {key: key.value for key in ControlKey}


# Backward compatibility aliases for legacy code
COLOR_BG = GameConfig.COLOR_BACKGROUND
COLOR_FG = GameConfig.COLOR_FOREGROUND
COLOR_DIM = GameConfig.COLOR_DIMMED
SCREEN_WIDTH = GameConfig.SCREEN_WIDTH
SCREEN_HEIGHT = GameConfig.SCREEN_HEIGHT
WINDOW_TITLE = GameConfig.WINDOW_TITLE
PADDLE_WIDTH = GameConfig.PADDLE_WIDTH
PADDLE_HEIGHT = GameConfig.PADDLE_HEIGHT
PADDLE_SPEED = GameConfig.PADDLE_SPEED_PX_PER_SEC
BALL_RADIUS = GameConfig.BALL_RADIUS
BALL_START_SPEED = GameConfig.BALL_INITIAL_SPEED_PX_PER_SEC
BALL_MAX_SPEED = GameConfig.BALL_MAX_SPEED_PX_PER_SEC
BALL_SPEEDUP_FACTOR = GameConfig.BALL_SPEED_MULTIPLIER_ON_HIT
WINNING_SCORE = GameConfig.WINNING_SCORE
SERVE_COOLDOWN_MS = GameConfig.SERVE_COOLDOWN_MS
FPS = GameConfig.TARGET_FPS
SCORE_FONT_SIZE = GameConfig.SCORE_FONT_SIZE
INFO_FONT_SIZE = GameConfig.INFO_FONT_SIZE
WIN_FONT_SIZE = GameConfig.WIN_FONT_SIZE
CENTER_DASH_HEIGHT = GameConfig.CENTER_DASH_HEIGHT
CENTER_DASH_GAP = GameConfig.CENTER_DASH_GAP
LEFT_UP_KEY = ControlKey.LEFT_PADDLE_UP.value
LEFT_DOWN_KEY = ControlKey.LEFT_PADDLE_DOWN.value
RIGHT_UP_KEY = ControlKey.RIGHT_PADDLE_UP.value
RIGHT_DOWN_KEY = ControlKey.RIGHT_PADDLE_DOWN.value