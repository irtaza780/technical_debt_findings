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
SPEED_INCREMENT_PER_SCORE = 0.15
GAP_DECREMENT_PER_SCORE = 2
SPAWN_DECREMENT_PER_SCORE = 30


def get_current_pipe_gap(score: int) -> int:
    """
    Calculate the current pipe gap based on score.
    
    Gap decreases as score increases, with a minimum threshold.
    
    Args:
        score: Current game score
        
    Returns:
        Current pipe gap in pixels
    """
    gap = START_GAP - (score * GAP_DECREMENT_PER_SCORE)
    return max(gap, MIN_GAP)


def get_current_pipe_speed(score: int) -> float:
    """
    Calculate the current pipe speed based on score.
    
    Speed increases as score increases, with a maximum threshold.
    
    Args:
        score: Current game score
        
    Returns:
        Current pipe speed in pixels per frame
    """
    speed = START_SPEED + (score * SPEED_INCREMENT_PER_SCORE)
    return min(speed, MAX_SPEED)


def get_current_spawn_interval(score: int) -> int:
    """
    Calculate the current pipe spawn interval based on score.
    
    Spawn interval decreases as score increases, with a minimum threshold.
    
    Args:
        score: Current game score
        
    Returns:
        Current spawn interval in milliseconds
    """
    interval = START_SPAWN_MS - (score * SPAWN_DECREMENT_PER_SCORE)
    return max(interval, MIN_SPAWN_MS)


def log_difficulty_settings(score: int) -> None:
    """
    Log current difficulty settings for debugging purposes.
    
    Args:
        score: Current game score
    """
    gap = get_current_pipe_gap(score)
    speed = get_current_pipe_speed(score)
    spawn = get_current_spawn_interval(score)
    
    logger.debug(
        f"Difficulty at score {score}: gap={gap}px, "
        f"speed={speed:.2f}px/frame, spawn={spawn}ms"
    )