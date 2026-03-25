"""
Global configuration, colors, physics, and difficulty tuning for the game.
"""

import logging

logger = logging.getLogger(__name__)

# Screen and timing
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 720
FPS = 60
FRAME_TIME_MS = 1000 / FPS

# Ground
GROUND_HEIGHT = 90
GROUND_COLOR = (200, 170, 90)

# Colors
BG_COLOR = (135, 206, 235)      # Sky blue
PIPE_COLOR = (70, 180, 80)      # Green pipe
PIPE_OUTLINE = (30, 120, 40)
BIRD_COLOR = (255, 215, 0)      # Gold
BIRD_OUTLINE = (120, 100, 0)
TEXT_COLOR = (255, 255, 255)
UI_COLOR = (20, 20, 20)

# Bird
BIRD_SIZE = 34
BIRD_RADIUS = BIRD_SIZE // 2

# Pipes
PIPE_WIDTH = 70

# Physics
GRAVITY = 0.50                   # pixels per frame^2
FLAP_STRENGTH = -9.5             # pixels per frame impulse
MAX_DROP_SPEED = 12.0            # terminal velocity

# Difficulty (starting values and caps)
START_GAP = 180
MIN_GAP = 100
START_SPEED = 3.2
MAX_SPEED = 7.5
START_SPAWN_MS = 1500
MIN_SPAWN_MS = 900

# Difficulty progression
SPEED_INCREMENT_PER_SCORE = 0.1
GAP_DECREMENT_PER_SCORE = 2
SPAWN_DECREMENT_PER_SCORE = 20


def get_difficulty_parameters(score: int) -> dict:
    """
    Calculate current difficulty parameters based on score.
    
    Args:
        score: Current player score (number of pipes passed).
        
    Returns:
        Dictionary containing current pipe_gap, pipe_speed, and spawn_interval_ms.
    """
    # Calculate pipe gap, clamped to minimum
    pipe_gap = max(
        MIN_GAP,
        START_GAP - (score * GAP_DECREMENT_PER_SCORE)
    )
    
    # Calculate pipe speed, clamped to maximum
    pipe_speed = min(
        MAX_SPEED,
        START_SPEED + (score * SPEED_INCREMENT_PER_SCORE)
    )
    
    # Calculate spawn interval, clamped to minimum
    spawn_interval_ms = max(
        MIN_SPAWN_MS,
        START_SPAWN_MS - (score * SPAWN_DECREMENT_PER_SCORE)
    )
    
    return {
        "pipe_gap": pipe_gap,
        "pipe_speed": pipe_speed,
        "spawn_interval_ms": spawn_interval_ms,
    }


def validate_configuration() -> bool:
    """
    Validate that configuration values are sensible.
    
    Returns:
        True if all validations pass, False otherwise.
    """
    validations = [
        (SCREEN_WIDTH > 0, "SCREEN_WIDTH must be positive"),
        (SCREEN_HEIGHT > 0, "SCREEN_HEIGHT must be positive"),
        (FPS > 0, "FPS must be positive"),
        (GROUND_HEIGHT > 0, "GROUND_HEIGHT must be positive"),
        (BIRD_SIZE > 0, "BIRD_SIZE must be positive"),
        (PIPE_WIDTH > 0, "PIPE_WIDTH must be positive"),
        (GRAVITY > 0, "GRAVITY must be positive"),
        (MAX_DROP_SPEED > 0, "MAX_DROP_SPEED must be positive"),
        (START_GAP > MIN_GAP, "START_GAP must be greater than MIN_GAP"),
        (START_SPEED < MAX_SPEED, "START_SPEED must be less than MAX_SPEED"),
        (START_SPAWN_MS > MIN_SPAWN_MS, "START_SPAWN_MS must be greater than MIN_SPAWN_MS"),
    ]
    
    all_valid = True
    for is_valid, message in validations:
        if not is_valid:
            logger.error(f"Configuration validation failed: {message}")
            all_valid = False
    
    return all_valid