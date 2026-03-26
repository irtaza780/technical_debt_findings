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
class Colors:
    """RGB color definitions for game elements."""
    BACKGROUND = (18, 18, 18)
    GRID = (36, 36, 36)
    SNAKE_HEAD = (0, 200, 0)
    SNAKE_BODY = (0, 150, 0)
    FOOD = (220, 60, 60)
    TEXT = (255, 255, 255)
    TEXT_SHADOW = (0, 0, 0)


# Game UI constants
GAME_TITLE = "Snake by ChatDev"

# Difficulty settings mapping difficulty levels to game speed (moves per second)
DIFFICULTY_SPEEDS = {
    "Easy": 8,
    "Normal": 12,
    "Hard": 16,
    "Insane": 22,
}

# Scoring constants
FOOD_SCORE_VALUE = 1

# Validation constants
MIN_DIFFICULTY = min(DIFFICULTY_SPEEDS.values())
MAX_DIFFICULTY = max(DIFFICULTY_SPEEDS.values())
VALID_DIFFICULTIES = set(DIFFICULTY_SPEEDS.keys())


def get_difficulty_speed(difficulty_level: str) -> int:
    """
    Retrieve the game speed for a given difficulty level.
    
    Args:
        difficulty_level: The difficulty level as a string key.
        
    Returns:
        The number of moves per second for the difficulty level.
        
    Raises:
        ValueError: If the difficulty level is not recognized.
    """
    if difficulty_level not in DIFFICULTY_SPEEDS:
        logger.error(f"Invalid difficulty level: {difficulty_level}")
        raise ValueError(
            f"Difficulty must be one of {VALID_DIFFICULTIES}, "
            f"got '{difficulty_level}'"
        )
    return DIFFICULTY_SPEEDS[difficulty_level]


def validate_grid_dimensions() -> bool:
    """
    Validate that grid dimensions are positive and consistent.
    
    Returns:
        True if dimensions are valid, False otherwise.
    """
    if CELL_SIZE <= 0 or GRID_WIDTH <= 0 or GRID_HEIGHT <= 0:
        logger.error(
            f"Invalid grid dimensions: CELL_SIZE={CELL_SIZE}, "
            f"GRID_WIDTH={GRID_WIDTH}, GRID_HEIGHT={GRID_HEIGHT}"
        )
        return False
    
    if WIDTH != CELL_SIZE * GRID_WIDTH or HEIGHT != CELL_SIZE * GRID_HEIGHT:
        logger.error("Calculated WIDTH/HEIGHT do not match grid dimensions")
        return False
    
    logger.info(
        f"Grid dimensions validated: {GRID_WIDTH}x{GRID_HEIGHT} "
        f"cells, {WIDTH}x{HEIGHT} pixels"
    )
    return True
</code>