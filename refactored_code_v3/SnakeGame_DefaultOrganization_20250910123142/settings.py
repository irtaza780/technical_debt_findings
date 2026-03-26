'''
Global configuration and constants for the Snake game.
'''

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Grid and sizing constants
CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 30
WIDTH = CELL_SIZE * GRID_WIDTH
HEIGHT = CELL_SIZE * GRID_HEIGHT

# Color constants (RGB tuples)
BG_COLOR = (18, 18, 18)
GRID_COLOR = (36, 36, 36)
SNAKE_HEAD_COLOR = (0, 200, 0)
SNAKE_BODY_COLOR = (0, 150, 0)
FOOD_COLOR = (220, 60, 60)
TEXT_COLOR = (255, 255, 255)
TEXT_SHADOW = (0, 0, 0)

# Game metadata
GAME_TITLE = "Snake by ChatDev"

# Difficulty levels and their corresponding game speeds (moves per second)
DIFFICULTY_SPEEDS = {
    "Easy": 8,
    "Normal": 12,
    "Hard": 16,
    "Insane": 22,
}

# Scoring constants
FOOD_SCORE = 1


def get_difficulty_speed(difficulty_level: str) -> int:
    """
    Retrieve the game speed for a given difficulty level.
    
    Args:
        difficulty_level: The difficulty level as a string key.
        
    Returns:
        The number of moves per second for the difficulty level.
        
    Raises:
        KeyError: If the difficulty level is not found in DIFFICULTY_SPEEDS.
        
    Raises:
        ValueError: If difficulty_level is not a string.
    """
    if not isinstance(difficulty_level, str):
        raise ValueError(f"Difficulty level must be a string, got {type(difficulty_level)}")
    
    if difficulty_level not in DIFFICULTY_SPEEDS:
        available_levels = ", ".join(DIFFICULTY_SPEEDS.keys())
        raise KeyError(
            f"Unknown difficulty level '{difficulty_level}'. "
            f"Available levels: {available_levels}"
        )
    
    speed = DIFFICULTY_SPEEDS[difficulty_level]
    logger.info(f"Difficulty '{difficulty_level}' set to {speed} moves/second")
    return speed


def validate_game_dimensions() -> bool:
    """
    Validate that game dimensions are properly configured.
    
    Returns:
        True if dimensions are valid, False otherwise.
    """
    if CELL_SIZE <= 0 or GRID_WIDTH <= 0 or GRID_HEIGHT <= 0:
        logger.error(
            f"Invalid dimensions: CELL_SIZE={CELL_SIZE}, "
            f"GRID_WIDTH={GRID_WIDTH}, GRID_HEIGHT={GRID_HEIGHT}"
        )
        return False
    
    if WIDTH != CELL_SIZE * GRID_WIDTH or HEIGHT != CELL_SIZE * GRID_HEIGHT:
        logger.error("Calculated WIDTH or HEIGHT does not match expected values")
        return False
    
    logger.info(f"Game dimensions validated: {WIDTH}x{HEIGHT} pixels")
    return True