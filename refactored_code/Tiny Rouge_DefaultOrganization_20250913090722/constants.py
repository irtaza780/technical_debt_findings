import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Grid settings
GRID_WIDTH = 80
GRID_HEIGHT = 80
TILE_SIZE_PIXELS = 8

# UI panel dimensions
UI_PANEL_WIDTH = 240
WINDOW_WIDTH = GRID_WIDTH * TILE_SIZE_PIXELS + UI_PANEL_WIDTH
WINDOW_HEIGHT = GRID_HEIGHT * TILE_SIZE_PIXELS

# Frame rate
TARGET_FPS = 60

# Tile type identifiers
TILE_WALL = 0
TILE_FLOOR = 1
TILE_DOOR = 2
TILE_CHEST = 3
TILE_MONSTER = 4

# Passable tile types (used for collision detection)
PASSABLE_TILES = {TILE_FLOOR, TILE_DOOR}

# Color definitions (RGB tuples)
class ColorPalette:
    """Central color palette for the roguelike game."""
    
    # Background colors
    BACKGROUND = (10, 10, 10)
    UI_BACKGROUND = (20, 20, 20)
    GRID_LINES = (30, 30, 30)
    
    # Tile colors
    WALL = (50, 50, 70)
    FLOOR = (120, 120, 120)
    DOOR = (60, 120, 200)
    
    # Entity colors
    PLAYER = (50, 200, 70)
    MONSTER = (200, 60, 60)
    CHEST = (220, 180, 60)
    
    # UI colors
    TEXT = (230, 230, 230)
    HIGHLIGHT = (100, 100, 100)


# Player gameplay constants
class PlayerStats:
    """Player character statistics and configuration."""
    
    STARTING_HP = 100


# Monster gameplay constants
class MonsterStats:
    """Monster entity statistics and configuration."""
    
    HP_MIN = 5
    HP_MAX = 30


# Chest/loot constants
class LootStats:
    """Loot and chest configuration."""
    
    HEAL_AMOUNT_MIN = 20
    HEAL_AMOUNT_MAX = 30


# Font configuration
class FontConfig:
    """Font settings for UI rendering."""
    
    NAME = "consolas"
    SIZE = 18


def get_tile_color(tile_type: int) -> tuple:
    """
    Retrieve the color for a given tile type.
    
    Args:
        tile_type: The tile type identifier (TILE_WALL, TILE_FLOOR, etc.)
    
    Returns:
        A tuple of (R, G, B) values representing the tile color.
    
    Raises:
        ValueError: If the tile type is not recognized.
    """
    tile_color_map = {
        TILE_WALL: ColorPalette.WALL,
        TILE_FLOOR: ColorPalette.FLOOR,
        TILE_DOOR: ColorPalette.DOOR,
        TILE_CHEST: ColorPalette.CHEST,
        TILE_MONSTER: ColorPalette.MONSTER,
    }
    
    if tile_type not in tile_color_map:
        logger.warning(f"Unknown tile type: {tile_type}, using floor color as fallback")
        return ColorPalette.FLOOR
    
    return tile_color_map[tile_type]


def is_tile_passable(tile_type: int) -> bool:
    """
    Determine if a tile type allows entity movement.
    
    Args:
        tile_type: The tile type identifier to check.
    
    Returns:
        True if the tile is passable, False otherwise.
    """
    return tile_type in PASSABLE_TILES