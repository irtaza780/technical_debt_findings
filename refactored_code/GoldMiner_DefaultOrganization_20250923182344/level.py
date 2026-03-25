import logging
import random
from typing import Dict, List, Tuple

from models import MineObject, distance

# Configure logging
logger = logging.getLogger(__name__)

# Level difficulty constants
BASE_TIME_LIMIT = 60
MIN_TIME_LIMIT = 25
TIME_DECREMENT_PER_LEVEL = 5
BASE_GOAL_SCORE = 400
GOAL_SCORE_INCREMENT = 220

# Spawn area constants
SPAWN_AREA_HORIZONTAL_MARGIN = 40
SPAWN_AREA_VERTICAL_MARGIN = 10
SPAWN_AREA_VERTICAL_RATIO = 0.65

# Object placement constants
PLACEMENT_ATTEMPT_LIMIT = 100
MINIMUM_SPACING_BUFFER = 6

# Gold small constants
GOLD_SMALL_BASE_COUNT = 3
GOLD_SMALL_RADIUS_MIN = 14
GOLD_SMALL_RADIUS_MAX = 20
GOLD_SMALL_VALUE_MIN = 80
GOLD_SMALL_VALUE_MAX = 140
GOLD_SMALL_WEIGHT_MIN = 0.8
GOLD_SMALL_WEIGHT_MAX = 1.3
GOLD_SMALL_COLOR = "#f4d35e"

# Gold large constants
GOLD_LARGE_LEVEL_DIVISOR = 2
GOLD_LARGE_RADIUS_MIN = 24
GOLD_LARGE_RADIUS_MAX = 30
GOLD_LARGE_VALUE_MIN = 250
GOLD_LARGE_VALUE_MAX = 380
GOLD_LARGE_WEIGHT_MIN = 1.6
GOLD_LARGE_WEIGHT_MAX = 2.4
GOLD_LARGE_COLOR = "#e9c46a"

# Rock constants
ROCK_BASE_COUNT = 2
ROCK_RADIUS_MIN = 16
ROCK_RADIUS_MAX = 24
ROCK_VALUE_MIN = 10
ROCK_VALUE_MAX = 40
ROCK_WEIGHT_MIN = 2.0
ROCK_WEIGHT_MAX = 3.0
ROCK_COLOR = "#6c757d"

# Diamond constants
DIAMOND_LEVEL_DIVISOR = 2
DIAMOND_RADIUS_MIN = 10
DIAMOND_RADIUS_MAX = 14
DIAMOND_VALUE_MIN = 400
DIAMOND_VALUE_MAX = 650
DIAMOND_WEIGHT_MIN = 0.6
DIAMOND_WEIGHT_MAX = 1.0
DIAMOND_COLOR = "#00d4ff"

# Bomb constants
BOMB_LEVEL_DIVISOR = 2
BOMB_LEVEL_OFFSET = 1
BOMB_RADIUS_MIN = 12
BOMB_RADIUS_MAX = 16
BOMB_VALUE_MIN = 150
BOMB_VALUE_MAX = 250
BOMB_WEIGHT_MIN = 1.0
BOMB_WEIGHT_MAX = 1.6
BOMB_COLOR = "#e63946"


class LevelManager:
    """Manages game level progression with increasing difficulty."""

    def __init__(self) -> None:
        """Initialize level manager with base difficulty parameters."""
        self.base_time = BASE_TIME_LIMIT
        self.min_time = MIN_TIME_LIMIT
        self.base_goal = BASE_GOAL_SCORE
        self.goal_step = GOAL_SCORE_INCREMENT

    def get_config(
        self, level_idx: int, width: int, height: int, ground_y: int
    ) -> Dict:
        """
        Generate level configuration with difficulty scaling.

        Args:
            level_idx: Current level number (1-indexed)
            width: Game area width in pixels
            height: Game area height in pixels
            ground_y: Y-coordinate of ground level

        Returns:
            Dictionary containing time_limit, goal_score, and objects list
        """
        time_limit = self._calculate_time_limit(level_idx)
        goal_score = self._calculate_goal_score(level_idx)
        objects = self.spawn_objects(level_idx, width, height, ground_y)

        return {
            "time_limit": time_limit,
            "goal_score": goal_score,
            "objects": objects,
        }

    def _calculate_time_limit(self, level_idx: int) -> int:
        """
        Calculate time limit for given level with decreasing time as difficulty increases.

        Args:
            level_idx: Current level number (1-indexed)

        Returns:
            Time limit in seconds, clamped to minimum
        """
        time_limit = self.base_time - (level_idx - 1) * TIME_DECREMENT_PER_LEVEL
        return max(self.min_time, time_limit)

    def _calculate_goal_score(self, level_idx: int) -> int:
        """
        Calculate score goal for given level with increasing targets.

        Args:
            level_idx: Current level number (1-indexed)

        Returns:
            Target score to complete level
        """
        return self.base_goal + (level_idx - 1) * self.goal_step

    def spawn_objects(
        self, level_idx: int, width: int, height: int, ground_y: int
    ) -> List[MineObject]:
        """
        Spawn game objects with level-appropriate counts and properties.

        Args:
            level_idx: Current level number (1-indexed)
            width: Game area width in pixels
            height: Game area height in pixels
            ground_y: Y-coordinate of ground level

        Returns:
            List of MineObject instances placed in spawn area
        """
        spawn_bounds = self._calculate_spawn_bounds(width, height, ground_y)
        object_counts = self._calculate_object_counts(level_idx)
        candidates: List[MineObject] = []

        # Spawn each object type
        self._spawn_gold_small(candidates, spawn_bounds, object_counts["gold_small"])
        self._spawn_gold_large(candidates, spawn_bounds, object_counts["gold_large"])
        self._spawn_rocks(candidates, spawn_bounds, object_counts["rocks"])
        self._spawn_diamonds(candidates, spawn_bounds, object_counts["diamonds"])
        self._spawn_bombs(candidates, spawn_bounds, object_counts["bombs"])

        return candidates

    def _calculate_spawn_bounds(
        self, width: int, height: int, ground_y: int
    ) -> Dict[str, float]:
        """
        Calculate boundaries for object spawning area.

        Args:
            width: Game area width in pixels
            height: Game area height in pixels
            ground_y: Y-coordinate of ground level

        Returns:
            Dictionary with left, right, top, bottom spawn boundaries
        """
        return {
            "left": SPAWN_AREA_HORIZONTAL_MARGIN,
            "right": width - SPAWN_AREA_HORIZONTAL_MARGIN,
            "top": ground_y - (height * SPAWN_AREA_VERTICAL_RATIO),
            "bottom": ground_y - SPAWN_AREA_VERTICAL_MARGIN,
        }

    def _calculate_object_counts(self, level_idx: int) -> Dict[str, int]:
        """
        Calculate spawn counts for each object type based on level.

        Args:
            level_idx: Current level number (1-indexed)

        Returns:
            Dictionary with counts for each object type
        """
        return {
            "gold_small": GOLD_SMALL_BASE_COUNT + level_idx,
            "gold_large": 1 + (level_idx // GOLD_LARGE_LEVEL_DIVISOR),
            "rocks": ROCK_BASE_COUNT + level_idx,
            "diamonds": max(1, level_idx // DIAMOND_LEVEL_DIVISOR),
            "bombs": max(0, (level_idx - BOMB_LEVEL_OFFSET) // BOMB_LEVEL_DIVISOR),
        }

    def _place_object(
        self,
        radius: float,
        spawn_bounds: Dict[str, float],
        existing_objects: List[MineObject],
    ) -> Tuple[float, float]:
        """
        Place object at random position avoiding excessive overlap with existing objects.

        Args:
            radius: Radius of object to place
            spawn_bounds: Dictionary with spawn area boundaries
            existing_objects: List of already-placed objects to avoid

        Returns:
            Tuple of (x, y) coordinates for object placement
        """
        left = spawn_bounds["left"]
        right = spawn_bounds["right"]
        top = spawn_bounds["top"]
        bottom = spawn_bounds["bottom"]

        # Attempt to find non-overlapping position
        for _ in range(PLACEMENT_ATTEMPT_LIMIT):
            x = random.uniform(left + radius, right - radius)
            y = random.uniform(top + radius, bottom - radius)

            # Validate position is within bounds
            if y < top + radius or y > bottom - radius:
                continue

            # Check spacing from existing objects
            has_collision = any(
                distance(x, y, obj.x, obj.y) <= (radius + obj.r + MINIMUM_SPACING_BUFFER)
                for obj in existing_objects
            )

            if not has_collision:
                return x, y

        # Fallback: allow overlap if area too crowded
        logger.debug(
            f"Object placement crowded at level, allowing overlap for radius {radius}"
        )
        return (
            random.uniform(left + radius, right - radius),
            random.uniform(top + radius, bottom - radius),
        )

    def _spawn_gold_small(
        self,
        objects: List[MineObject],
        spawn_bounds: Dict[str, float],
        count: int,
    ) -> None:
        """
        Spawn small gold objects.

        Args:
            objects: List to append spawned objects to
            spawn_bounds: Dictionary with spawn area boundaries
            count: Number of small gold objects to spawn
        """
        for _ in range(count):
            radius = random.randint(GOLD_SMALL_RADIUS_MIN, GOLD_SMALL_RADIUS_MAX)
            x, y = self._place_object(radius, spawn_bounds, objects)
            value = random.randint(GOLD_SMALL_VALUE_MIN, GOLD_SMALL_VALUE_MAX)
            weight = random.uniform(GOLD_SMALL_WEIGHT_MIN, GOLD_SMALL_WEIGHT_MAX)
            objects.append(
                MineObject(x, y, radius, "gold", value, weight, GOLD_SMALL_COLOR)
            )

    def _spawn_gold_large(
        self,
        objects: List[MineObject],
        spawn_bounds: Dict[str, float],
        count: int,
    ) -> None:
        """
        Spawn large gold objects.

        Args:
            objects: List to append spawned objects to
            spawn_bounds: Dictionary with spawn area boundaries
            count: Number of large gold objects to spawn
        """
        for _ in range(count):
            radius = random.randint(GOLD_LARGE_RADIUS_MIN, GOLD_LARGE_RADIUS_MAX)
            x, y = self._place_object(radius, spawn_bounds, objects)
            value = random.randint(GOLD_LARGE_VALUE_MIN, GOLD_LARGE_VALUE_MAX)
            weight = random.uniform(GOLD_LARGE_WEIGHT_MIN, GOLD_LARGE_WEIGHT_MAX)
            objects.append(
                MineObject(x, y, radius, "gold", value, weight, GOLD_LARGE_COLOR)
            )

    def _spawn_rocks(
        self,
        objects: List[MineObject],
        spawn_bounds: Dict[str, float],
        count: int,
    ) -> None:
        """
        Spawn rock obstacles.

        Args:
            objects: List to append spawned objects to
            spawn_bounds: Dictionary with spawn area boundaries
            count: Number of rocks to spawn
        """
        for _ in range(count):
            radius = random.randint(ROCK_RADIUS_MIN, ROCK_RADIUS_MAX)
            x, y = self._place_object(radius, spawn_bounds, objects)
            value = random.randint(ROCK_VALUE_MIN, ROCK_VALUE_MAX)
            weight = random.uniform(ROCK_WEIGHT_MIN, ROCK_WEIGHT_MAX)
            objects.append(
                MineObject(x, y, radius, "rock", value, weight, ROCK_COLOR)
            )

    def _spawn_diamonds(
        self,
        objects: List[MineObject],
        spawn_bounds: Dict[str, float],
        count: int,
    ) -> None:
        """
        Spawn diamond objects with high value.

        Args:
            objects: List to append spawned objects to
            spawn_bounds: Dictionary with spawn area boundaries
            count: Number of diamonds to spawn
        """
        for _ in range(count):
            radius = random.randint(DIAMOND_RADIUS_MIN, DIAMOND_RADIUS_MAX)
            x, y = self._place_object(radius, spawn_bounds, objects)
            value = random.randint(DIAMOND_VALUE_MIN, DIAMOND_VALUE_MAX)
            weight = random.uniform(DIAMOND_WEIGHT_MIN, DIAMOND_WEIGHT_MAX)
            objects.append(
                MineObject(x, y, radius, "diamond", value, weight, DIAMOND_COLOR)
            )

    def _spawn_bombs(
        self,
        objects: List[MineObject],
        spawn_bounds: Dict[str, float],
        count: int,
    ) -> None:
        """
        Spawn bomb obstacles with negative value.

        Args:
            objects: List to append spawned objects to
            spawn_bounds: Dictionary with spawn area boundaries
            count: Number of bombs to spawn
        """
        for _ in range(count):
            radius = random.randint(BOMB_RADIUS_MIN, BOMB_RADIUS_MAX)
            x, y = self._place_object(radius, spawn_bounds, objects)
            value = -random.randint(BOMB_VALUE_MIN, BOMB_VALUE_MAX)
            weight = random.uniform(BOMB_WEIGHT_MIN, BOMB_WEIGHT_MAX)
            objects.append(
                MineObject(x, y, radius, "bomb", value, weight, BOMB_COLOR)
            )