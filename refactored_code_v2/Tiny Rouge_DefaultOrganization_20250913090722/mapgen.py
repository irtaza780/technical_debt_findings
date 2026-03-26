import logging
import random
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from entities import Monster
import constants as C

logger = logging.getLogger(__name__)

# Grid dimensions
GRID_WIDTH = C.GRID_WIDTH
GRID_HEIGHT = C.GRID_HEIGHT

# Border offset to keep playable area away from walls
BORDER_OFFSET = 1

# Path carving parameters
PATH_DETOUR_CHANCE = 0.25
PATH_PERPENDICULAR_CHANCE = 0.5
PATH_MAX_STEPS_MULTIPLIER = 4

# Open area carving parameters
OPEN_AREA_BASE_DENSITY = 0.5
OPEN_AREA_BASE_ITERATIONS = 4000
OPEN_AREA_NEIGHBOR_CHANCE = 0.2
CONNECTIVITY_CHECK_DENSITY = 0.6
CONNECTIVITY_CHECK_ITERATIONS = 3000
CONNECTIVITY_MAX_ATTEMPTS = 5

# Monster and chest placement parameters
MONSTER_COUNT_MIN = 40
MONSTER_COUNT_MAX = 200
MONSTER_FLOOR_RATIO = 20
CHEST_COUNT_MIN = 20
CHEST_COUNT_MAX = 120
CHEST_FLOOR_RATIO = 30


class MapData:
    """Container for generated map data including grid, entities, and key positions."""

    def __init__(
        self,
        grid: List[List[int]],
        start: Tuple[int, int],
        door: Tuple[int, int],
        monsters: Dict[Tuple[int, int], Monster],
        chests: Set[Tuple[int, int]],
    ):
        """
        Initialize MapData.

        Args:
            grid: 2D list representing the map tiles
            start: (x, y) tuple for player start position
            door: (x, y) tuple for exit door position
            monsters: Dictionary mapping positions to Monster instances
            chests: Set of (x, y) positions containing chests
        """
        self.grid = grid
        self.start = start
        self.door = door
        self.monsters = monsters
        self.chests = chests


def _neighbors(x: int, y: int, w: int, h: int) -> List[Tuple[int, int]]:
    """
    Get valid orthogonal neighbors for a position within bounds.

    Args:
        x: X coordinate
        y: Y coordinate
        w: Grid width
        h: Grid height

    Yields:
        (x, y) tuples of valid neighboring positions
    """
    if x > 0:
        yield (x - 1, y)
    if x < w - 1:
        yield (x + 1, y)
    if y > 0:
        yield (x, y - 1)
    if y < h - 1:
        yield (x, y + 1)


def _bfs_has_path(
    grid: List[List[int]], start: Tuple[int, int], door: Tuple[int, int]
) -> bool:
    """
    Check if a path exists from start to door using BFS.

    Only traverses FLOOR and DOOR tiles. Used to verify map connectivity.

    Args:
        grid: 2D list of tile types
        start: (x, y) starting position
        door: (x, y) goal position

    Returns:
        True if a path exists, False otherwise
    """
    w, h = len(grid[0]), len(grid)
    sx, sy = start
    gx, gy = door
    queue = deque([(sx, sy)])
    seen = {(sx, sy)}

    while queue:
        x, y = queue.popleft()
        if (x, y) == (gx, gy):
            return True

        for nx, ny in _neighbors(x, y, w, h):
            tile = grid[ny][nx]
            # Only traverse passable tiles
            if tile in (C.TILE_FLOOR, C.TILE_DOOR) and (nx, ny) not in seen:
                seen.add((nx, ny))
                queue.append((nx, ny))

    return False


def _clamp_to_bounds(value: int, min_val: int, max_val: int) -> int:
    """
    Clamp a value between min and max bounds.

    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Clamped value
    """
    return min(max(min_val, value), max_val)


def _get_path_moves(
    x: int, y: int, target_x: int, target_y: int
) -> List[Tuple[int, int]]:
    """
    Get cardinal moves toward a target position.

    Args:
        x: Current X coordinate
        y: Current Y coordinate
        target_x: Target X coordinate
        target_y: Target Y coordinate

    Returns:
        List of (x, y) moves that progress toward target
    """
    moves = []
    if x < target_x:
        moves.append((x + 1, y))
    elif x > target_x:
        moves.append((x - 1, y))
    if y < target_y:
        moves.append((x, y + 1))
    elif y > target_y:
        moves.append((x, y - 1))
    return moves


def _add_detour_move(
    x: int, y: int, rng: random.Random
) -> Optional[Tuple[int, int]]:
    """
    Generate an optional perpendicular detour move.

    Args:
        x: Current X coordinate
        y: Current Y coordinate
        rng: Random number generator instance

    Returns:
        A detour (x, y) move or None if no detour should be added
    """
    if rng.random() < PATH_PERPENDICULAR_CHANCE:
        if BORDER_OFFSET < y < GRID_HEIGHT - BORDER_OFFSET - 1:
            return (x + rng.choice([-1, 1]), y)
    else:
        if BORDER_OFFSET < y < GRID_HEIGHT - BORDER_OFFSET - 1:
            return (x, y + rng.choice([-1, 1]))
    return None


def _carve_path(
    grid: List[List[int]],
    start: Tuple[int, int],
    door: Tuple[int, int],
    rng: random.Random,
) -> None:
    """
    Carve a guaranteed path from start to door.

    Creates a meandering but monotonic path that generally progresses toward
    the goal while occasionally adding perpendicular detours for variety.

    Args:
        grid: 2D list to modify with carved floor tiles
        start: (x, y) starting position
        door: (x, y) goal position
        rng: Random number generator instance
    """
    x, y = start
    gx, gy = door
    grid[y][x] = C.TILE_FLOOR
    steps = 0
    max_steps = GRID_WIDTH * GRID_HEIGHT * PATH_MAX_STEPS_MULTIPLIER

    while (x, y) != (gx, gy) and steps < max_steps:
        steps += 1
        moves = _get_path_moves(x, y, gx, gy)

        # Occasionally add a perpendicular detour
        if rng.random() < PATH_DETOUR_CHANCE:
            detour = _add_detour_move(x, y, rng)
            if detour:
                moves.append(detour)

        if not moves:
            break

        nx, ny = rng.choice(moves)
        # Clamp to inner bounds to avoid touching borders
        nx = _clamp_to_bounds(nx, BORDER_OFFSET, GRID_WIDTH - BORDER_OFFSET - 1)
        ny = _clamp_to_bounds(ny, BORDER_OFFSET, GRID_HEIGHT - BORDER_OFFSET - 1)
        x, y = nx, ny
        grid[y][x] = C.TILE_FLOOR

    # Ensure door tile position is open
    grid[gy][gx] = C.TILE_FLOOR


def _add_random_open_areas(
    grid: List[List[int]],
    rng: random.Random,
    density: float = OPEN_AREA_BASE_DENSITY,
    iterations: int = OPEN_AREA_BASE_ITERATIONS,
) -> None:
    """
    Randomly carve additional floor tiles to create open areas.

    Args:
        grid: 2D list to modify with carved floor tiles
        rng: Random number generator instance
        density: Probability of carving each iteration (0.0-1.0)
        iterations: Number of carving attempts
    """
    for _ in range(iterations):
        if rng.random() < density:
            x = rng.randint(BORDER_OFFSET, GRID_WIDTH - BORDER_OFFSET - 1)
            y = rng.randint(BORDER_OFFSET, GRID_HEIGHT - BORDER_OFFSET - 1)
            grid[y][x] = C.TILE_FLOOR

            # Carve some neighboring tiles with lower probability
            for nx, ny in _neighbors(x, y, GRID_WIDTH, GRID_HEIGHT):
                if (
                    BORDER_OFFSET <= nx <= GRID_WIDTH - BORDER_OFFSET - 1
                    and BORDER_OFFSET <= ny <= GRID_HEIGHT - BORDER_OFFSET - 1
                ):
                    if rng.random() < OPEN_AREA_NEIGHBOR_CHANCE:
                        grid[ny][nx] = C.TILE_FLOOR


def _initialize_grid() -> List[List[int]]:
    """
    Create a grid filled with wall tiles.

    Returns:
        2D list of TILE_WALL values
    """
    return [[C.TILE_WALL for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]


def _set_border_walls(grid: List[List[int]]) -> None:
    """
    Set all border tiles to walls to contain the playable area.

    Args:
        grid: 2D list to modify
    """
    for x in range(GRID_WIDTH):
        grid[0][x] = C.TILE_WALL
        grid[GRID_HEIGHT - 1][x] = C.TILE_WALL
    for y in range(GRID_HEIGHT):
        grid[y][0] = C.TILE_WALL
        grid[y][GRID_WIDTH - 1] = C.TILE_WALL


def _ensure_connectivity(
    grid: List[List[int]], start: Tuple[int, int], door: Tuple[int, int], rng: random.Random
) -> None:
    """
    Verify and ensure map connectivity by carving additional areas if needed.

    Args:
        grid: 2D list to potentially modify
        start: (x, y) starting position
        door: (x, y) goal position
        rng: Random number generator instance
    """
    attempts = 0
    while not _bfs_has_path(grid, start, door) and attempts < CONNECTIVITY_MAX_ATTEMPTS:
        attempts += 1
        logger.debug(f"Connectivity check failed, attempt {attempts} to fix")
        _add_random_open_areas(
            grid,
            rng,
            density=CONNECTIVITY_CHECK_DENSITY,
            iterations=CONNECTIVITY_CHECK_ITERATIONS,
        )


def _get_floor_positions(
    grid: List[List[int]], start: Tuple[int, int], door: Tuple[int, int]
) -> List[Tuple[int, int]]:
    """
    Get all floor tile positions excluding start and door.

    Args:
        grid: 2D list of tile types
        start: (x, y) starting position to exclude
        door: (x, y) goal position to exclude

    Returns:
        List of (x, y) floor positions
    """
    return [
        (x, y)
        for y in range(GRID_HEIGHT)
        for x in range(GRID_WIDTH)
        if grid[y][x] == C.TILE_FLOOR and (x, y) not in (start, door)
    ]


def _calculate_entity_counts(floor_count: int) -> Tuple[int, int]:
    """
    Calculate monster and chest counts based on available floor tiles.

    Args:
        floor_count: Number of available floor positions

    Returns:
        Tuple of (monster_count, chest_count)
    """
    num_monsters = max(
        MONSTER_COUNT_MIN, min(MONSTER_COUNT_MAX, floor_count // MONSTER_FLOOR_RATIO)
    )
    num_chests = max(
        CHEST_COUNT_MIN, min(CHEST_COUNT_MAX, floor_count // CHEST_FLOOR_RATIO)
    )
    return num_monsters, num_chests


def _place_monsters(
    floor_positions: List[Tuple[int, int]],
    num_monsters: int,
    rng: random.Random,
) -> Dict[Tuple[int, int], Monster]:
    """
    Place monsters on available floor positions.

    Args:
        floor_positions: List of available (x, y) positions
        num_monsters: Number of monsters to place
        rng: Random number generator instance

    Returns:
        Dictionary mapping positions to Monster instances
    """
    monsters: Dict[Tuple[int, int], Monster] = {}
    placed = 0
    idx = 0

    while placed < num_monsters and idx < len(floor_positions):
        x, y = floor_positions[idx]
        idx += 1
        if (x, y) not in monsters:
            monsters[(x, y)] = Monster(
                x=x, y=y, hp=rng.randint(C.MONSTER_HP_MIN, C.MONSTER_HP_MAX)
            )
            placed += 1

    return monsters


def _place_chests(
    floor_positions: List[Tuple[int, int]],
    num_chests: int,
    monsters: Dict[Tuple[int, int], Monster],
    start_idx: int,
) -> Set[Tuple[int, int]]:
    """
    Place chests on available floor positions, avoiding monsters.

    Args:
        floor_positions: List of available (x, y) positions
        num_chests: Number of chests to place
        monsters: Dictionary of monster positions
        start_idx: Index to start searching from in floor_positions

    Returns:
        Set of (x, y) chest positions
    """
    chests: Set[Tuple[int, int]] = set()
    placed = 0
    idx = start_idx

    while placed < num_chests and idx < len(floor_positions):
        x, y = floor_positions[idx]
        idx += 1
        if (x, y) not in monsters and (x, y) not in chests:
            chests.add((x, y))
            placed += 1

    return chests


def generate_map(seed: Optional[int] = None) -> MapData:
    """
    Generate a complete dungeon map with guaranteed connectivity.

    Creates an 80x80 grid with walls, a guaranteed path from start to door,
    random open areas, and populates it with monsters and chests. Monsters
    and chests are overlays that do not modify base grid tiles.

    Uses a local RNG instance to avoid mutating global random state.

    Args:
        seed: Optional random seed for reproducible generation

    Returns:
        MapData instance containing grid, entities, and key positions
    """
    # Use a local RNG to avoid mutating global random state
    rng = random.Random(seed) if seed is not None else random.Random()

    # Initialize grid and set borders
    grid = _initialize_grid()
    _set_border_walls(grid)

    # Define key positions
    start = (BORDER_OFFSET, BORDER_OFFSET)
    door = (GRID_WIDTH - BORDER_OFFSET - 1, GRID_HEIGHT - BORDER_OFFSET - 1)

    # Carve a guaranteed path from start to door
    _carve_path(grid, start, door, rng)

    # Carve additional open areas
    _add_random_open_areas(grid, rng, density=OPEN_AREA_BASE_DENSITY, iterations=OPEN_AREA_