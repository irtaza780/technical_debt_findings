import logging
import random
from typing import Dict, List, Tuple

from models import MineObject, distance

# Configure logging
logger = logging.getLogger(__name__)

# Difficulty curve constants
BASE_TIME_LIMIT = 60
MIN_TIME_LIMIT = 25
TIME_REDUCTION_PER_LEVEL = 5
BASE_GOAL_SCORE = 400
GOAL_SCORE_INCREMENT = 220

# Spawn area constants
SPAWN_AREA_HORIZONTAL_MARGIN = 40
SPAWN_AREA_VERTICAL_MARGIN = 10
SPAWN_AREA_VERTICAL_RATIO = 0.65
SPAWN_COLLISION_BUFFER = 6
MAX_PLACEMENT_ATTEMPTS = 100

# Object type constants
OBJECT_TYPE_GOLD_SMALL = "gold_small"
OBJECT_TYPE_GOLD_LARGE = "gold_large"
OBJECT_TYPE_ROCK = "rock"
OBJECT_TYPE_DIAMOND = "diamond"
OBJECT_TYPE_BOMB = "bomb"

# Gold small properties
GOLD_SMALL_RADIUS_MIN = 14
GOLD_SMALL_RADIUS_MAX = 20
GOLD_SMALL_VALUE_MIN = 80
GOLD_SMALL_VALUE_MAX = 140
GOLD_SMALL_WEIGHT_MIN = 0.8
GOLD_SMALL_WEIGHT_MAX = 1.3
GOLD_SMALL_COLOR = "#f4d35e"

# Gold large properties
GOLD_LARGE_RADIUS_MIN = 24
GOLD_LARGE_RADIUS_MAX = 30
GOLD_LARGE_VALUE_MIN = 250
GOLD_LARGE_VALUE_MAX = 380
GOLD_LARGE_WEIGHT_MIN = 1.6
GOLD_LARGE_WEIGHT_MAX = 2.4
GOLD_LARGE_COLOR = "#e9c46a"

# Rock properties
ROCK_RADIUS_MIN = 16
ROCK_RADIUS_MAX = 24
ROCK_VALUE_MIN = 10
ROCK_VALUE_MAX = 40
ROCK_WEIGHT_MIN = 2.0
ROCK_WEIGHT_MAX = 3.0
ROCK_COLOR = "#6c757d"

# Diamond properties
DIAMOND_RADIUS_MIN = 10
DIAMOND_RADIUS_MAX = 14
DIAMOND_VALUE_MIN = 400
DIAMOND_VALUE_MAX = 650
DIAMOND_WEIGHT_MIN = 0.6
DIAMOND_WEIGHT_MAX = 1.0
DIAMOND_COLOR = "#00d4ff"

# Bomb properties
BOMB_RADIUS_MIN = 12
BOMB_RADIUS_MAX = 16
BOMB_VALUE_MIN = 150
BOMB_VALUE_MAX = 250
BOMB_WEIGHT_MIN = 1.0
BOMB_WEIGHT_MAX = 1.6
BOMB_COLOR = "#e63946"


class LevelManager:
    """Manages game difficulty progression and object spawning.
    
    Provides increasing difficulty with tighter time limits, higher score goals,
    and more obstacles as levels progress.
    """

    def __init__(self) -> None:
        """Initialize the level manager with default difficulty parameters."""
        logger.debug("Initializing LevelManager")

    def get_config(self, level_idx: int, width: int, height: int, ground_y: int) -> Dict:
        """Generate configuration for a specific level.
        
        Args:
            level_idx: The level number (1-indexed).
            width: Game area width in pixels.
            height: Game area height in pixels.
            ground_y: Y-coordinate of the ground level.
            
        Returns:
            Dictionary containing time_limit, goal_score, and objects list.
        """
        time_limit = self._calculate_time_limit(level_idx)
        goal_score = self._calculate_goal_score(level_idx)
        objects = self.spawn_objects(level_idx, width, height, ground_y)

        logger.info(
            f"Generated config for level {level_idx}: "
            f"time_limit={time_limit}s, goal_score={goal_score}, objects={len(objects)}"
        )

        return {
            "time_limit": time_limit,
            "goal_score": goal_score,
            "objects": objects,
        }

    def _calculate_time_limit(self, level_idx: int) -> int:
        """Calculate time limit for a given level.
        
        Time limit decreases by TIME_REDUCTION_PER_LEVEL for each level,
        with a minimum of MIN_TIME_LIMIT seconds.
        
        Args:
            level_idx: The level number (1-indexed).
            
        Returns:
            Time limit in seconds.
        """
        time_limit = BASE_TIME_LIMIT - (level_idx - 1) * TIME_REDUCTION_PER_LEVEL
        return max(MIN_TIME_LIMIT, time_limit)

    def _calculate_goal_score(self, level_idx: int) -> int:
        """Calculate goal score for a given level.
        
        Goal score increases by GOAL_SCORE_INCREMENT for each level.
        
        Args:
            level_idx: The level number (1-indexed).
            
        Returns:
            Target score to complete the level.
        """
        return BASE_GOAL_SCORE + (level_idx - 1) * GOAL_SCORE_INCREMENT

    def spawn_objects(
        self, level_idx: int, width: int, height: int, ground_y: int
    ) -> List[MineObject]:
        """Spawn game objects for a level with increasing difficulty.
        
        Objects are placed in the lower portion of the game area with collision
        avoidance. Object counts and types increase with level progression.
        
        Args:
            level_idx: The level number (1-indexed).
            width: Game area width in pixels.
            height: Game area height in pixels.
            ground_y: Y-coordinate of the ground level.
            
        Returns:
            List of MineObject instances placed in the level.
        """
        spawn_bounds = self._calculate_spawn_bounds(width, height, ground_y)
        object_counts = self._calculate_object_counts(level_idx)
        objects: List[MineObject] = []

        # Place each object type
        self._spawn_object_type(
            objects,
            object_counts["gold_small"],
            GOLD_SMALL_RADIUS_MIN,
            GOLD_SMALL_RADIUS_MAX,
            GOLD_SMALL_VALUE_MIN,
            GOLD_SMALL_VALUE_MAX,
            GOLD_SMALL_WEIGHT_MIN,
            GOLD_SMALL_WEIGHT_MAX,
            "gold",
            GOLD_SMALL_COLOR,
            spawn_bounds,
        )

        self._spawn_object_type(
            objects,
            object_counts["gold_large"],
            GOLD_LARGE_RADIUS_MIN,
            GOLD_LARGE_RADIUS_MAX,
            GOLD_LARGE_VALUE_MIN,
            GOLD_LARGE_VALUE_MAX,
            GOLD_LARGE_WEIGHT_MIN,
            GOLD_LARGE_WEIGHT_MAX,
            "gold",
            GOLD_LARGE_COLOR,
            spawn_bounds,
        )

        self._spawn_object_type(
            objects,
            object_counts["rocks"],
            ROCK_RADIUS_MIN,
            ROCK_RADIUS_MAX,
            ROCK_VALUE_MIN,
            ROCK_VALUE_MAX,
            ROCK_WEIGHT_MIN,
            ROCK_WEIGHT_MAX,
            "rock",
            ROCK_COLOR,
            spawn_bounds,
        )

        self._spawn_object_type(
            objects,
            object_counts["diamonds"],
            DIAMOND_RADIUS_MIN,
            DIAMOND_RADIUS_MAX,
            DIAMOND_VALUE_MIN,
            DIAMOND_VALUE_MAX,
            DIAMOND_WEIGHT_MIN,
            DIAMOND_WEIGHT_MAX,
            "diamond",
            DIAMOND_COLOR,
            spawn_bounds,
        )

        self._spawn_object_type(
            objects,
            object_counts["bombs"],
            BOMB_RADIUS_MIN,
            BOMB_RADIUS_MAX,
            BOMB_VALUE_MIN,
            BOMB_VALUE_MAX,
            BOMB_WEIGHT_MIN,
            BOMB_WEIGHT_MAX,
            "bomb",
            BOMB_COLOR,
            spawn_bounds,
            is_negative_value=True,
        )

        logger.debug(f"Spawned {len(objects)} objects for level {level_idx}")
        return objects

    def _calculate_spawn_bounds(
        self, width: int, height: int, ground_y: int
    ) -> Dict[str, float]:
        """Calculate the boundaries for object spawning.
        
        Objects are placed in the lower portion of the game area, leaving
        margins on the sides and top.
        
        Args:
            width: Game area width in pixels.
            height: Game area height in pixels.
            ground_y: Y-coordinate of the ground level.
            
        Returns:
            Dictionary with 'left', 'right', 'top', 'bottom' spawn boundaries.
        """
        return {
            "left": SPAWN_AREA_HORIZONTAL_MARGIN,
            "right": width - SPAWN_AREA_HORIZONTAL_MARGIN,
            "top": ground_y - (height * SPAWN_AREA_VERTICAL_RATIO),
            "bottom": ground_y - SPAWN_AREA_VERTICAL_MARGIN,
        }

    def _calculate_object_counts(self, level_idx: int) -> Dict[str, int]:
        """Calculate the number of each object type to spawn.
        
        Object counts increase with level progression to increase difficulty.
        
        Args:
            level_idx: The level number (1-indexed).
            
        Returns:
            Dictionary with counts for each object type.
        """
        return {
            "gold_small": 3 + level_idx,
            "gold_large": 1 + (level_idx // 2),
            "rocks": 2 + level_idx,
            "diamonds": max(1, level_idx // 2),
            "bombs": max(0, (level_idx - 1) // 2),
        }

    def _spawn_object_type(
        self,
        objects: List[MineObject],
        count: int,
        radius_min: int,
        radius_max: int,
        value_min: int,
        value_max: int,
        weight_min: float,
        weight_max: float,
        object_type: str,
        color: str,
        spawn_bounds: Dict[str, float],
        is_negative_value: bool = False,
    ) -> None:
        """Spawn multiple objects of a specific type with collision avoidance.
        
        Args:
            objects: List to append spawned objects to.
            count: Number of objects to spawn.
            radius_min: Minimum object radius.
            radius_max: Maximum object radius.
            value_min: Minimum object value.
            value_max: Maximum object value.
            weight_min: Minimum object weight.
            weight_max: Maximum object weight.
            object_type: Type identifier for the object.
            color: Hex color code for rendering.
            spawn_bounds: Dictionary with spawn area boundaries.
            is_negative_value: If True, negate the value (for bombs).
        """
        for _ in range(count):
            radius = random.randint(radius_min, radius_max)
            x, y = self._find_spawn_position(radius, objects, spawn_bounds)
            value = random.randint(value_min, value_max)
            if is_negative_value:
                value = -value
            weight = random.uniform(weight_min, weight_max)

            objects.append(
                MineObject(x, y, radius, object_type, value, weight, color)
            )

    def _find_spawn_position(
        self,
        radius: int,
        existing_objects: List[MineObject],
        spawn_bounds: Dict[str, float],
    ) -> Tuple[float, float]:
        """Find a valid spawn position with collision avoidance.
        
        Attempts to place an object without excessive overlap with existing objects.
        If placement fails after MAX_PLACEMENT_ATTEMPTS, returns a fallback position.
        
        Args:
            radius: Radius of the object to place.
            existing_objects: List of already-placed objects.
            spawn_bounds: Dictionary with spawn area boundaries.
            
        Returns:
            Tuple of (x, y) coordinates for the object.
        """
        left = spawn_bounds["left"]
        right = spawn_bounds["right"]
        top = spawn_bounds["top"]
        bottom = spawn_bounds["bottom"]

        for attempt in range(MAX_PLACEMENT_ATTEMPTS):
            x = random.uniform(left + radius, right - radius)
            y = random.uniform(top + radius, bottom - radius)

            # Verify position is within vertical bounds
            if y < top + radius or y > bottom - radius:
                continue

            # Check for collisions with existing objects
            has_collision = False
            for existing_obj in existing_objects:
                min_distance = radius + existing_obj.r + SPAWN_COLLISION_BUFFER
                if distance(x, y, existing_obj.x, existing_obj.y) <= min_distance:
                    has_collision = True
                    break

            if not has_collision:
                return x, y

        # Fallback: allow slight overlap if area is too crowded
        logger.debug(
            f"Could not find collision-free position after {MAX_PLACEMENT_ATTEMPTS} "
            f"attempts, using fallback position"
        )
        x = random.uniform(left + radius, right - radius)
        y = random.uniform(top + radius, bottom - radius)
        return x, y